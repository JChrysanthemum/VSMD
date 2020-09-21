from VSMD1X6 import *
# CommonCMD, DataRegTable, StatusRegTable, DeviceTable, CWTable, CMDTable, str2can_msg
import time, random
import os
from canMsgHandler import VsmdCanFrame, CanMsgListener


class Example4StringCommand(object):
    """How to generate command like : 00180280#0000000100012132

    This string-format CAN message can be used on "can-utils", GNU. You can
    install it by apt. And this class show the common commands of these type

    """

    @staticmethod
    def read_data_register():
        print(CommonCMD.read_data_regs("All", DataRegTable.CID, 1))

    @staticmethod
    def write_data_register():
        print(CommonCMD.write_data_regs("X0", DataRegTable.CID, 2))
        print(CommonCMD.save("X0"))  # You will lose your change if you don't save

    @staticmethod
    def read_status_register():
        print(CommonCMD.read_status_regs("All", StatusRegTable.SPD, 1))

    @staticmethod
    def motors():
        print(CommonCMD.enable_motor("ALL"))
        print(CommonCMD.move_motor("ALL", -16))
        print(CommonCMD.disable_motor("ALL"))

    @staticmethod
    def customized():
        """
        An hidden function in CommonCMD, you can write your own command if you want.
        """
        CommonCMD.__easy_cmd(tar=DeviceTable.BroadCast, src=DeviceTable.SliderX0, cw=CWTable.CMD,
                             cmd0reg=CMDTable.READ_STATUS_REGS, data=[0, 1])
        CommonCMD.__easy_cmd(tar=DeviceTable.BroadCast, src=DeviceTable.SliderX0, cw=CWTable.W_Data_Reg,
                             cmd0reg=DataRegTable.CRN, data=2.0)


class Example4PythonCan(object):
    """How to use generated string command to python package "python-can"


    """
    # If you use python-can, you can convert str command by this:
    cmd = CommonCMD.read_data_regs("All", DataRegTable.CID, 1)
    msg = str2can_msg(cmd)  # can.interface.Bus


def initialize_motor(_cid, _spd=19200.0, _bitrate=500000, _mcs=32, _channel="can0"):
    bus = can.interface.Bus(bustype='socketcan', channel=_channel,)
    for cmd in [CommonCMD.write_data_regs("All", DataRegTable.CID, _cid),
                CommonCMD.save("All"),
                CommonCMD.write_data_regs("All", DataRegTable.BDR, _bitrate),
                CommonCMD.save("All"),
                CommonCMD.write_data_regs("All", DataRegTable.MCS, _mcs),
                CommonCMD.save("All"),
                ]:
        # print(cmd)
        bus.send(str2can_msg(cmd))


def random_move_test():
    bus = can.interface.Bus(bustype='socketcan', channel="can0", bitrate=500000)
    bus.send(str2can_msg(CommonCMD.enable_motor("All")))
    for i in range(50000):
        distance = int(random.choice((1, -1))*800*random.uniform(5, 10))
        # sleep_time = 2 * distance/19200.0
        sleep_time = distance / 19200.0 + 3
        cmd = CommonCMD.move_dis("All", distance)
        print(i, cmd)
        # os.system("cansend can0 %s"% cmd)
        bus.send(str2can_msg(cmd))
        time.sleep(sleep_time)
    bus.send(str2can_msg(CommonCMD.stop_motor("All")))


def random_move_test2():
    f = open("log.txt", "a")
    for i in range(100):
        print(i)
        os.system("cansend can0 0004178b#000000c8")
        output = os.popen("ip -details -statistics link show can0 ").read()
        output = "\n****%d****\n" % i + output
        print(output)
        f.write(output)
        time.sleep(2)

