from enum import IntEnum, Enum
import can
from ctypes import *
# pointer, cast, c_int, c_float, POINTER
from types import MappingProxyType, DynamicClassAttribute
from typing import overload

# plus base for motor
step_base = 200

# plus msc for motor
step_mcs = 32

# plus per around
# The motor has ppc plus to rotate a complete around
ppa = step_base * step_mcs

# Speed of motor for plus
# Unit : plus pre second
spd_p = 19200

# millimeter per around
mpa = 8

# plus per mm
ppmm = ppa/mpa

# speed for motor
# Unit : mm/s
# spd = (p_pmm * send_spacing / 1000ms/s)^-1
spd = spd_p/ppa*mpa

# Note: This the full speed of motor, and it need a time to accelerate.
# for spd 19200.00, it needs almost 2 second to speed up


class OhEnum(Enum):
    """Specific class for 4-col Data of VSMD

            Name    :   Value   :   Description     :   Detail
    Regs    RegName    Address      Meaning of Reg      DataFormat
    Status  StaName    StatCode     Meaning of Sta      ValueMean
    """

    def next(self):
        """ Get next <enum:X.value>

        Example:
            # >>> class Test(OhEnum):
            # >>>     E_1 = "V1"
            # >>>     E_2 = "V2"
            # >>> Test.E_1.next()
            # Test.E_2

        :type : enum
        :return: Next enum-element in order
        """
        if not hasattr(self, "_OhEnum__record"):
            self.__init_record()
        i = 0
        for v in self.__record:
            if self.name == v.name and i < self.__record.__len__() - 1:
                return self.__record[i + 1]
            i += 1
        raise ValueError("{!r} is the last key".format(self.name))

    @classmethod
    def __init_record(cls):
        """Init a list for query

            Hashed Map can not afford this , so we need more space to do this
        :return:
        """
        od = MappingProxyType(cls._member_map_)
        cls.__record = list(od.values())

    @classmethod
    def query(cls, value, pos=0):
        """Query this enum by value (Address or StatCode)

        :type value: str
        :param value: value in enum.value[0]

        :type pos: int
        :param pos: what should return

        :return:
            pos=0 : return enum (including name and value)
            pos=1 : return name only
            pos=2 : return Description only
            pos=3 : return Detail only
        """
        if not hasattr(cls, "_OhEnum__record"):
            cls.__init_record()
        for v in cls.__record:
            if v.value[0] == value:
                if pos == 0:
                    return v
                elif pos == 1:
                    return v.name
                elif pos == 2:
                    return v.value[1]
                elif pos == 3:
                    return v.value[2]
                else:
                    raise ValueError("Wrong Pos")
        raise ValueError("Not recorded")


class ExtIdTable(IntEnum):
    """Name of bits and their description

    xxx_id_0 and xxx_id_1 are used for slice of array
    like ">>> array[start:end] "

    """
    # Fixed value 0
    BIT27 = 0

    # Start of device ID for target
    # All zero (total 9) for broadcast
    target_id_0 = 1

    # End of device ID for target
    target_id_1 = 10

    # Fixed value 0
    BIT18 = 10

    # Start of device ID for source
    source_id_0 = 11

    # End of device ID for source
    source_id_1 = 20

    # Command word
    C0 = 20

    # Command word
    C1 = 21

    # Command or Address for register
    CMD0REG_0 = 22


class DeviceTable(Enum):
    """Device table for our project

            ..note:
                1. device = DeviceTable(id)  # get a enum
                2. id=DeviceTable.xxx.value  # get a string
            """
    # Target device only
    BroadCast = "000000000"
    SliderX0 = "000000001"
    SliderX1 = "000000010"
    SliderY = "000000011"
    SliderZ = "000000100"
    Pi = "000001111"
    UnKnow = "111111111"


class SensorValueTable(IntEnum):
    no_action = 0
    origin_reset = 1
    stop_with_decelerate = 2
    stopWD_oriReset = 3
    stop_immediately = 4
    stopIm_oriReset = 5
    move_continuous_positive = 6
    move_continuous_negative = 7
    enable_offline = 8
    disable_offline = 9


class CMDTable(Enum):
    ENA = "0000001"
    OFF = "0000010"
    ORG = "0000011"
    STP = "0000100"
    MOV = "0000101"
    POS = "0000110"
    SAV = "0000111"
    OUTPUT = "0001000"
    ZERO_START = "0001001"
    ZERO_STOP = "0001010"
    RMV = "0001011"
    ACTION_START = "0010000"
    ACTION_STOP = "0010001"
    ACTION_CLEAR = "0010010"
    ACTION_ZERO = "0010011"
    ACTION_SPEED = "0010100"
    ACTION_POSITION = "0010101"
    ACTION_DELAY = "0010110"
    ENC = "0011101"
    READ_STATUS_REGS = "0011110"
    READ_DATA_REGS = "0011111"


class CWTable(Enum):
    R_Stat_Reg = "00"  # "Read Status Register"
    R_Data_Reg = "01"  # "Read Data Register"
    W_Data_Reg = "10"  # "Write Data Register"
    CMD = "11"  # "Command"


# 20K	0x1C2132
# 25K	0x168132
# 30K	0x12C132
# 40K	0xE1132
# 50K	0xB4132
# 60K	0x5A163
# 75K	0x78132
# 80K	0x4B153
# 90K	0x4B143
# 100K	0x5A132
# 125K	0x48132
# 150K	0x3C132
# 200K	0x2D132
# 250K	0x24132
# 300K	0x1E132
# 400K	0xF153
# 500K	0x12132
# 600K	0x9163
# 750K	0x8153
# 900K	0x6163
# 1000K	0x9132

BaudRateDict = {
    "0005a132": 100000,
    "00012132": 500000,

}


class StatusValueTable(OhEnum):
    """
    For Detail, the former is 0 and another is 1

    """

    # StatName  Value Description     Detail
    S1 = [0, "Status of Sensor 1", "0-low level/1-high level"]
    S2 = [1, "Status of Sensor 2", "0-low level/1-high level"]
    S3 = [2, "Status of Sensor 3", "0-low level/1-high level"]
    S4 = [3, "Status of Sensor 4", "0-low level/1-high level"]
    POS = [4, "Cur Pos Equals Tar Po s", "0-Not Equal/1-Equal"]
    SPD = [5, "Cur SPD Equals Tar SP D", "0-Not Equal/1-Equal"]
    FLT = [6, "Hard ware Error (Need  Reset)", "0-Normal/1-Error"]
    ORG = [7, "Flag of origin", "0-Not  at origin/1-At origin"]
    STP = [8, "Flag of stop", "0-Not s top (running)/1-Stopped"]
    CMD_WRG = [9, "Command Error (or  Para out or range)", "0-CMD ok/1-CMD Error"]
    FLASH_ERR = [10, "Flash Error(RW  in Flash)", "0-Normal/1-Error"]  # reading or writing Flash
    ACTION = [11, "Flag of offline action", "0-No offline action/1-Offline action"]
    PWR = [13, "Flag or motor enable energy", "0-ENA/1-OFF"]
    ZERO = [14, "Flag of end of the zeroing", "0-No zeroing,during zeroing/1-zeroing end"]
    S5 = [15, "Status of Sensor 5", "0-low level/1-high level"]
    S6 = [16, "Status of Sensor 6", "0-low level/1-high level"]
    OTS = [20, "Over heat", "0-normal/1-Over heating protection"]
    OCP = [21, "Over current", "0-normal/1-Over current protection"]
    UV = [22, "Under Voltage", "0-normal/1-Under voltage protection"]
    ENC_ERR = [24, "Encoding error(stall or encoder-error )", "0-normal/1-error"]


SafeInf = [
    StatusValueTable.OTS, StatusValueTable.OCP, StatusValueTable.UV,
    StatusValueTable.ENC_ERR, StatusValueTable.FLASH_ERR, StatusValueTable.FLT,
    StatusValueTable.CMD_WRG
]
SensorInf = [
    StatusValueTable.S1, StatusValueTable.S2, StatusValueTable.S3, StatusValueTable.S4, StatusValueTable.S5,
    StatusValueTable.S6,
]


class DataRegTable(OhEnum):
    # RegNae   ADR       Description              Detail
    CID = ["0000000", "Channel ID", "Determined by motor"]  # 0x00
    BDR = ["0000001", "Baud Rate", "Default 132000"]  # 0x01
    MCS = ["0000010", "Motor Control Subdivision",
           "0 : one step \n1 : 1/2\n2 : 1/4\n3 : 1/8\n4: 1/16\n5 : 1/32\n"
           "6 : 1/64 (Ser-045,13X,14X Only)\n7:1/128 (Ser-045,13X,14X Only)\n"
           "8 : 1/256 (Ser-045,13X,14X Only)"]  # 0x02
    SPD = ["0000011", "Target Speed", "(-192000,192000)pps"]  # 0x03
    ACC = ["0000100", "Accelerate", "(0,192000000)pps/s"]  # 0x04
    DEC = ["0000101", "Decelerate", "(0,192000000)pps/s"]  # 0x05
    CRA = ["0000110", "Current Accelerate", "0-2.5A(Series-025)\n0-4.5A(Series-045)"]  # 0x06
    CRN = ["0000111", "Current Normal", "0-2.5A(Series-025)\n0-4.5A(Series-045)"]  # 0x07
    CRH = ["0001000", "Current Hold", "0-2.5A(Series-025)\n0-4.5A(Series-045)"]  # 0x08
    S1F_S1R_S2F_S2R = ["0001001", "Function Settings for S1,S2", "See SensorValueTable"]  # 0x09
    S3F_S3R_S4F_S4R = ["0001010", "Function Settings for S3,S4", "See SensorValueTable"]  # 0x0A
    S5F_S5R_S6F_S6R = ["0001011", "Function Settings for S5,S6", "See SensorValueTable"]  # 0x0B
    _R1 = ["0001100", "Reserved", "Blank"]  # 0x0C
    S_CONFIG = ["0001101", "Settings for S1-S6",
                "0 : Input\n1:Output\nBit Definition\nBIT0 : Fixed Input for S1\nBIT1 : Fixed Input for S2\n"
                "BIT2 : S3\nBIT3 : S4\nBIT4 : S5\nBIT5 : S6"]  # 0x0D
    ZMD = ["0001110", "Zeroing mode definition",
           "0 : Zeroing off\n1 : Zeroing once\n2 : zeroing once + safe position\n3 : Double zeroing\n"
           "4 : Double zeroing + safe position\n5 : Non-sense zeroing (Series-136/146)"]  # 0x0E
    OSV = ["0001111", "Open zeroing Sensor level", "0 : low level\n1 : high level"]  # 0x0F
    SNR = ["0010000", "Sensor Number of zeroing", "0 : S1\n1 : S2\n2 : S3\n3 : S4\n4 : S5\n5 : S6"]  # 0x10
    ZSD = ["0010001", "Zeroing's Speed", "Not Defined"]  # 0x11
    ZSP = ["0010010", "Zeroing's Safe-Position", "Not Defined"]  # 0x12
    DMD = ["0010011", "Offline Mod", "0 : Normal mode\n1 : zeroing before offline"]  # 0x13
    DAR = ["0010100", "Duration when online and no communication",
           "0 : No auto running\n1-60 : time(sec)"]  # 0x14
    _R2 = ["0010101", "Reserved", "Blank"]  # 0x15
    _R3 = ["0010110", "Reserved", "Blank"]  # 0x16
    MSR_MSV_PSR_PSV = ["0010111", "MSR_MSV_PSR_PSV",
                       "MSR (Negative sensor)\n0 : No negative limit\n1 : S1\n2 : S2\n3 :S3\n4 : S4"
                       "5 : S5\n6 : S6\nMSV (Negative trigger level)\n0 : low level\n1 : high level\n"
                       "PSR (Positive Sensor)\n0 : 1 No positive\n1 : S1\n2 : S2\n3 : S3\n4 : S4\n5 : S5\n"
                       "6 : S6\nPSV (Positive trigger level)\n0 : 1 low level\n1 : high level"]  # 0x17
    PAE = ["0011000", "Power-on Attach Enable-energy", "0 : No auto ENA\n1 : Auto ENA"]  # 0x18
    CAF = ["0011001", "Command Attach FAQ.", "0 : Not support\n1 : Support"]  # 0x19
    ZAR = ["0011010", "Zeroing After Power-on", "0 : No zeroing\n1: zeroing"]  # 0x1A
    SDS = ["0011011", "subdivision of Non-sense zeroing", "Not defined"]  # 0x1B
    ZCR = ["0011100", "Current when Non-sense zeroing", "Not defined"]  # 0x1C
    EMOD = ["0100000", "Encoding Mod", "Encoding Mod Off\nEncoding Mod On"]  # 0x20
    ELNS = ["0100001", "Number of encoder lines", "10-10000"]  # 0x21
    ESTP = ["0100010", "Full steps per lap", "10-10000"]  # 0x22
    ERTY = ["0100011", "number of retries", "0-no-limit\n1-100retry times"]  # 0x23
    EDIR = ["0100100", "Encoder direction", "0-backward\n1-forward"]  # 0x24
    EZ = ["0100101", "Encoder sensitivity", "Not defined"]  # 0x25
    EWR = ["0100110", "What to do when the retry limit is reached", "0-do nothing\n1-stop\n2-offline"]  # 0x26


class StatusRegTable(OhEnum):
    # RegName ADR       Description     Detail
    SPD = ["0000000", "Current Speed ", "(float32)"]
    POS = ["0000001", "Current Position ", "(int32)"]
    STATUS = ["0000010", "Status Code ", "(u-int32)"]
    VSMD_Version = ["0001010", "VSMD116-025T-1.0.000.171010", "None"]


def hex2float(_hex):
    i = int(_hex, 16)  # convert from hex to a Python int
    cp = pointer(c_int(i))  # make this into a c integer
    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
    return fp.contents.value


def float2hex(_f: float):
    cp = pointer(c_float(_f))
    fp = cast(cp, POINTER(c_int))
    if _f >= 0:
        return hex(fp.contents.value)
    else:
        return hex(int(fp.contents.value) & 0xFFFFFFFF)


def int2hex(_i):
    if type(_i) == str:
        _i = int(_i)

    if _i >= 0:
        return hex(_i)
    else:
        return hex(_i & 0xFFFFFFFF)


def hex2int32(_hex):
    i = int(_hex, 16)
    cp = pointer(c_int(i))
    fp = cast(cp, POINTER(c_int32))
    return fp.contents.value


def str2can_msg(raw_cmd: str):
    extid = int(raw_cmd.split("#")[0], 16)
    data_frame = []
    datas = raw_cmd.split("#")[1]
    for i in range(int(datas.__len__()/2)):
        data_frame.append(int(datas[i*2:i*2 + 2], 16))
    msg_snd = can.Message(arbitration_id=extid, channel="can0",
                          data=data_frame,
                          is_extended_id=True)
    return msg_snd


class CommonCMD(object):

    @staticmethod
    def __easy_cmd(tar: DeviceTable, src: DeviceTable, cw: CWTable, cmd0reg, data):
        """

        :param tar:
        :param src:
        :param cw:
        :param cmd0reg:
            1. R/W Register: RegName (str) like "Channel ID"
            2. Command to VSMD: Command (CMTable) like CMDTable.READ_DAtA_REGS
        :param data:
            1. Read Register: RegCount (int) like 3 which will be convert to D1 D2
            2. Write Register: Data (int or float) which will be convert to D1-D4 (Write one register per can-frame)
            3. Command: "STP,MOV,POS,RMV,READ_STATUS_REGS,READ_DATA_REGS" has data
        :return:
        """

        data_frame = "0" * 16
        if cw == CWTable.R_Stat_Reg or cw == CWTable.R_Data_Reg:
            # It wrote in motor
            print("it determined by motor !")
            return "00000000#0000000000000000"
        if cw == CWTable.W_Data_Reg:
            reg_name = cmd0reg
            cmd0reg = cmd0reg.value[0]
            if reg_name in [DataRegTable.SPD, DataRegTable.ACC, DataRegTable.DEC, DataRegTable.CRA, DataRegTable.CRN,
                            DataRegTable.CRH, ]:
                data_frame = str(float2hex(data))[2:].rjust(8, "0")
            elif reg_name in [DataRegTable.CID, DataRegTable.MCS, DataRegTable.PAE, DataRegTable.CAF,
                              DataRegTable.EMOD]:
                data_frame = str(int2hex(data))[2:].rjust(8, "0")
            elif reg_name == DataRegTable.BDR:
                for k, v in BaudRateDict.items():
                    if v == data:
                        data_frame = k
                        break
                if data_frame == "0" * 16:
                    raise Exception("Not a valid BDR")
            elif reg_name == DataRegTable.MSR_MSV_PSR_PSV:
                data_frame = str(data).rjust(8, "0")
            else:
                print("Not Defined ! ")
                data_frame = str(int2hex(data))[2:].rjust(8, "0")
        else:  # CWTable.CMD
            if cmd0reg in [CMDTable.ENA, CMDTable.OFF, CMDTable.SAV]:
                data_frame = "0" * 0  # dlc = 0
            elif cmd0reg in [CMDTable.STP]:
                data_frame = str(int2hex(data))[2:].rjust(4, "0")  # dlc = 2
            elif cmd0reg == CMDTable.MOV:
                data_frame = str(float2hex(data))[2:].rjust(8, "0")  # dlc = 4
            elif cmd0reg in [CMDTable.POS, CMDTable.RMV]:
                data_frame = str(int2hex(data))[2:].rjust(8, "0")  # dlc = 4
            elif cmd0reg in [CMDTable.READ_DATA_REGS, CMDTable.READ_STATUS_REGS]:
                data_frame = str(int2hex(int(data[0], 2)))[2:].rjust(2, "0") + str(int2hex(data[1]))[2:].rjust(2,
                                                                                                               "0")  # dlc = 4

            else:
                data_frame = "0" * 16  # dlc = 8

            cmd0reg = cmd0reg.value
        ext_frame = "000" + tar.value + ("0" if tar != DeviceTable.BroadCast else "1") + src.value + cw.value + cmd0reg
        # print("Bin Ext:", ext_frame)
        ext_frame = str(int2hex(int(ext_frame, 2)))[2:].rjust(8, "0")
        # print("%s#%s" % (ext_frame, data_frame))

        return "%s#%s" % (ext_frame, data_frame)
        # return [ext_frame, data_frame]

    @staticmethod
    def _get_tar_device(name: str, unsafe=False):
        name = name.upper()
        tar = None
        if name == "ALL":
            # Turn off the YZ and control two Z
            tar = DeviceTable.BroadCast
        elif name == "Y":
            tar = DeviceTable.SliderY
        elif name == "Z":
            tar = DeviceTable.SliderZ
        if unsafe:
            if name == "X0":
                tar = DeviceTable.SliderX0
            if name == "X1":
                tar = DeviceTable.SliderX1

        if tar is None:
            raise Exception("Target device not found")
        return tar

    @staticmethod
    def enable_motor(device: str):
        tar = CommonCMD._get_tar_device(device)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.ENA, data=0)
        return cmd

    @staticmethod
    def disable_motor(device: str):
        tar = CommonCMD._get_tar_device(device)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.OFF, data=0)
        return cmd

    @staticmethod
    def move_motor(device: str, speed: float):
        device = device.upper()
        tar = CommonCMD._get_tar_device(device)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.MOV, data=speed)
        return cmd

    @staticmethod
    def stop_motor(device: str):
        tar = CommonCMD._get_tar_device(device)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.STP, data=1)
        return cmd

    @staticmethod
    def move_to(device: str, pos: int):
        tar = CommonCMD._get_tar_device(device)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.POS, data=pos * ppmm)
        return cmd

    @staticmethod
    def move_dis(device: str, dis: int):
        tar = CommonCMD._get_tar_device(device)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.RMV, data=dis)
        return cmd

    @staticmethod
    def zero(device: str):
        tar = CommonCMD._get_tar_device(device)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.ZERO_START, data=0)
        return cmd

    @staticmethod
    def read_status_regs(device: str, reg: StatusRegTable, cnt: int):
        tar = CommonCMD._get_tar_device(device, unsafe=True)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.READ_STATUS_REGS,
                                   data=[reg.value[0], cnt])
        return cmd

    @staticmethod
    def read_data_regs(device: str, reg: DataRegTable, cnt: int):
        tar = CommonCMD._get_tar_device(device, unsafe=True)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.READ_DATA_REGS,
                                   data=[reg.value[0], cnt])
        return cmd

    @staticmethod
    def write_data_regs(device: str, reg: DataRegTable, data):
        tar = CommonCMD._get_tar_device(device, unsafe=True)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.W_Data_Reg, cmd0reg=reg,
                                   data=data)
        return cmd

    @staticmethod
    def save(device: str):
        tar = CommonCMD._get_tar_device(device, unsafe=True)
        src = DeviceTable.Pi
        cmd = CommonCMD.__easy_cmd(tar=tar, src=src, cw=CWTable.CMD, cmd0reg=CMDTable.SAV, data=0)
        return cmd

