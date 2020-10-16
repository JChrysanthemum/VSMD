import can
import time
from .VSMD1X6 import *
from multiprocessing import Process


class VsmdCanFrame(object):
    """ Per Frame in CAN-Network

    Use message in socket-can-bus to initialize,
    """

    def __init__(self, message, debug=False):
        """Decode raw message and send them to sub-frame

        :param message: message in socket can bus
        :param debug: print some log in decoding message

        .. note:
            This class write for CAN2.0 , which has 29-bitwise-ExtendId
            and 8-bytes-dataFrame

        .. note:
            DO NOT try to use para in protect level (like: _extID) if you
            have no idea what you are really doing with CAN Frame

        """

        # can device : can0 , vcan0
        self.channel = message.channel

        # Data Length Code , Every two 0x para get 1 DLC
        self.dlc = message.dlc

        # print(type(message.arbitration_id))
        if type(message.arbitration_id) == str:
            message.arbitration_id = int(message.arbitration_id, 16)

        # :type message.arbitration_id : int
        # Convert this int to bin and use string to storage
        ext_msg = str(bin(message.arbitration_id))[2:].rjust(29, "0")

        # :type [str,]
        data_msg = []

        self.ERROR_FLG = False

        # :type message.data : bytearray
        # Each element convert to an int in bytearray iteration
        i = 0
        for t_int in message.data:
            # Every two dlc data get 32-bit , which can be used for a register
            if i % 4 == 0:
                data_msg.append(str(hex(t_int))[2:].rjust(2, "0"))
            else:
                f_i = int(i / 4)
                data_msg[f_i] += str(hex(t_int))[2:].rjust(2, "0")
                # What the data mean dues to what reg it is
                # so we reserve the 0x number
                # print(hex2float(data_msg[f_i]))
                # data_msg[f_i] = str(int(data_msg[f_i], 16))
            i += 1

        raw_dm = ""
        for dm in data_msg:
            raw_dm += dm.ljust(8, "0")
        raw_dm = raw_dm.ljust(16, "0")

        self.debug_msg = self.log_end()
        self.debug_msg += self.log_formatter("Main: ", [
            ("Raw", str(hex(message.arbitration_id))[2:].rjust(8, "0") + "#" + raw_dm),
            ("Sender", self.channel), ("Extent ID Frame", ext_msg), ("DLC", self.dlc), ("Data Frame", data_msg)
            ])
        if self.dlc % 2 != 0:
            self.debug_msg += self.log_formatter("*** Warning ***",
                                                 [("DLC Count warning", "DLC count should not be ODD")])
        if debug:
            print(self.debug_msg)

        self.ext_frame = self.VsmdCanExtFrame(ext_msg, debug=debug)

        if self.ext_frame.DEVICE_ERR_FLG:
            return

        self.data_frame = self.VsmdCanDataFrame(data_msg=data_msg, dlc=self.dlc, cw=self.ext_frame.cw,
                                                cmd0adr=self.ext_frame.cmd0regAdr, debug=debug)

        if self.ERROR_FLG or self.ext_frame.ERROR_FLG or self.data_frame.ERROR_FLG:
            debug_msg = self.debug_msg + self.ext_frame.debug_msg + self.data_frame.debug_msg
            with open("/home/pi/log.txt", "a+") as file:
                debug_msg = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n" + debug_msg + "\n"
                file.write(debug_msg)

    class VsmdCanExtFrame(object):
        """CAN Extend Identifier Frame

        You can find the detail of the frame-design for VSMD in ExtIdTable

        """

        def __init__(self, ext_msg, debug=False):
            """Decode the ext can message

                    :type ext_msg: str

                    .. note:
                        Message.data could bring 8 bytes data maxium, which equals 2*8=16 hex Data
                        Message.dlc means the count of data, which may be used for error checking (I AM NOT SHURE)

            """
            self.ERROR_FLG = False

            self.DEVICE_ERR_FLG = False

            #: msg.arbitration_id is int , we need a string type of bin-array
            self._extID = ext_msg

            self._target_id = self._extID[ExtIdTable.target_id_0:ExtIdTable.target_id_1]

            self._source_id = self._extID[ExtIdTable.source_id_0:ExtIdTable.source_id_1]

            try:
                self.target_device = DeviceTable(self._target_id)
                self.source_device = DeviceTable(self._source_id)
            except ValueError as e:
                self.DEVICE_ERR_FLG = True
                print(self._target_id, self._source_id, e)
                # return

            if self.target_device == DeviceTable.BroadCast and self._extID[ExtIdTable.target_id_1] == 0:
                raise Exception("Invalid target ID")

            self.cw = self._extID[ExtIdTable.C0:ExtIdTable.C1 + 1]

            self.cmd0regAdr = self._extID[ExtIdTable.CMD0REG_0:]

            self.debug_msg = VsmdCanFrame.log_formatter("Extend ID Frame", [
                ("Source Device", self.source_device.name), ("Target Device", self.target_device.name),
                ("Command Word", self.cw), ("CMD or Register ADR", self.cmd0regAdr if CWTable(self.cw) !=
                                                                                      CWTable.CMD else CMDTable(
                    self.cmd0regAdr).name)
            ])

            if debug:
                print(self.debug_msg)

    class VsmdCanDataFrame(object):

        def __init__(self, dlc, data_msg, cw, cmd0adr, debug=False):

            self.cw = CWTable(cw)

            # If Read Regs will get dlc = 2
            self.cnt_data = int(dlc / 4) if dlc != 2 else 1

            self.regs_values = {}
            self.status = None
            self.sensors = None

            self.ERROR_FLG = False
            self.debug_msg = ""

            def _fill_reg_inf(_cnt: int, _data, _my_t):
                _result = []

                try:
                    _reg = _my_t.query(cmd0adr)
                except ValueError as e:
                    if _my_t is StatusRegTable and int(cmd0adr, 2) <= 16:
                        self.debug_msg += VsmdCanFrame.log_formatter("*** Warning ***",
                                                                     [(
                                                                      "Key Not Found", "No Key in table , reserved ?")])
                        return _result
                    else:
                        return ""

                for _i in range(_cnt):
                    try:
                        if _i != 0:
                            _reg = _reg.next()
                        raw_data = _data[_i]

                        # Use float as Data format in these register
                        if _reg in [DataRegTable.SPD, DataRegTable.ACC, DataRegTable.DEC, DataRegTable.CRA,
                                    DataRegTable.CRN, DataRegTable.CRH, StatusRegTable.SPD]:
                            _result.append([_reg.name, hex2float(raw_data)])
                        # Use int as Data format in these register
                        elif _reg in [DataRegTable.CID, DataRegTable.MCS, DataRegTable.PAE, DataRegTable.CAF,
                                      DataRegTable.ZAR, DataRegTable.EMOD, StatusRegTable.POS]:
                            _result.append([_reg.name, hex2int32(raw_data)])
                        # Use Enum for Baud rate
                        elif _reg == DataRegTable.BDR:
                            try:
                                _result.append([_reg.name, BaudRateDict[raw_data]])
                            except KeyError as e:
                                print("BaudRate Set Error", e)
                                print(BaudRateDict)
                                raise e
                        elif _reg in [DataRegTable.MSR_MSV_PSR_PSV, StatusRegTable.STATUS]:
                            _result.append([_reg.name, raw_data])
                        else:
                            print("Not specified data format, transform to int32")
                            _result.append([_reg.name, hex2int32(raw_data)])
                    except ValueError as e:
                        war_log = VsmdCanFrame.log_formatter("Warning", [("Message", e)])
                        print(war_log)
                        break
                return _result

            def _fill_stat_value_inf(_data):

                # 32bit and fill zero in right before revision

                _data = str(bin(int(_data, 16)))[2:].rjust(32, "0")
                # Reverse this string because it count from right
                _data = _data[::-1]

                _result = []
                _sensor = []
                for record in StatusValueTable:
                    _v = _data[record.value[0]]
                    if record in SafeInf and _v == "1":
                        self.ERROR_FLG = True
                        _result.append(
                            [record.value[1], _v + " / " + record.value[2]]
                        )
                    if record in SensorInf:
                        _sensor.append(
                            [record.value[1], _v]
                        )
                return _result, _sensor

            if self.cw == CWTable.R_Stat_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=StatusRegTable)
                # Whatever you got , STATUS is the last one you got
                keys = [x[0] for x in self.regs_values]
                if "STATUS" in keys and "SPD" not in keys:
                    if "POS" in keys:
                        (self.status, self.sensors) = _fill_stat_value_inf(data_msg[1])
                    else:
                        (self.status, self.sensors) = _fill_stat_value_inf(data_msg[0])
            elif self.cw == CWTable.R_Data_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=DataRegTable)
            elif self.cw == CWTable.W_Data_Reg:  # Write one register Once
                self.regs_values = _fill_reg_inf(1, _data=data_msg, _my_t=DataRegTable)
            elif self.cw == CWTable.CMD:
                self.command = CMDTable(cmd0adr)

            self.debug_msg += VsmdCanFrame.log_formatter("Action", [("CW Means", self.cw.name)])
            if self.cw in [CWTable.W_Data_Reg, CWTable.R_Data_Reg]:
                self.debug_msg += VsmdCanFrame.log_formatter("Data Frame - Data Reg", self.regs_values)
            elif self.cw == CWTable.CMD:
                data_frame = []
                if self.command in [CMDTable.ENA, CMDTable.OFF]:
                    pass
                elif self.command in [CMDTable.STP]:
                    data_frame.append((self.command.name, int(data_msg[0], 16)))
                elif self.command in [CMDTable.MOV, CMDTable.POS, CMDTable.RMV]:
                    data_frame.append((self.command.name, hex2int32(data_msg[0])))
                elif self.command == CMDTable.READ_DATA_REGS:
                    d1 = data_msg[0][:2]
                    d2 = data_msg[0][2:4]
                    data_frame.append(("Data Reg Start:", DataRegTable.query(str(bin(int(d1, 16)))[2:].rjust(7, "0"))))
                    data_frame.append(("Data Reg count:", int(d2, 16)))
                elif self.command == CMDTable.READ_STATUS_REGS:
                    d1 = data_msg[0][:2]
                    d2 = data_msg[0][2:4]
                    data_frame.append(
                        ("Data Reg Start:", StatusRegTable.query(str(bin(int(d1, 16)))[2:].rjust(7, "0"))))
                    data_frame.append(("Data Reg count:", int(d2, 16)))
                else:
                    data_frame.append((self.command.name, int(data_msg, 16)))
                self.debug_msg += VsmdCanFrame.log_formatter("Data Frame", [("Command", data_frame)])
            else:  # CWTable.R_Stat_Reg
                keys = [x[0] for x in self.regs_values]
                if "POS" in keys or "SPD" in keys:
                    self.debug_msg += VsmdCanFrame.log_formatter("Data Frame - Stat Reg", self.regs_values)
                if self.status is not None:
                    if self.ERROR_FLG:
                        self.debug_msg += VsmdCanFrame.log_formatter("STATUS", self.status)
                    else:
                        self.debug_msg += VsmdCanFrame.log_formatter("STATUS", [("0 ERROR", "0 WARNING")])
            self.debug_msg += VsmdCanFrame.log_end()
            if debug:
                print(self.debug_msg)

    @staticmethod
    def log_formatter(title, tcs):
        result = "| %s | \n" % title
        for tc in tcs:
            result += "+ %-23s :  %s \n" % (tc[0], tc[1])
        return result

    @staticmethod
    def log_end():
        return "%s\n" % ("*" * 59)


class CanMsgListener(Process):

    def __init__(self, channel="can0", bitrate=100000):
        super(CanMsgListener, self).__init__()
        self.channel = channel
        self.bitrate = bitrate
        self.debug_msg = ""
        self.exitFlag = False
        self.cnt = 0
        self.bus = can.interface.Bus(bustype='socketcan', channel=self.channel, bitrate=self.bitrate)

    def run(self):
        for _msg in self.bus:
            if self.exitFlag:
                return
            self.handle(_msg)
            self.cnt += 1

    @staticmethod
    def handle(msg):
        frame = VsmdCanFrame(msg, debug=True)
        if frame.ERROR_FLG:
            debug_msg = frame.debug_msg
            print(debug_msg)


if __name__ == "__main__":
    listener = CanMsgListener()
    listener.start()
