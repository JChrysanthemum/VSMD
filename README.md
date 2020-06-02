# VSMD

Controller for VSMD can motor

## Debug model

Explained by doc file [VSMD1X6_SERIES_V1.0.pdf](doc/VSMD1X6_SERIES_V1.0.pdf), it's
easy to convert can.message to meaningful frame.

```
bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000)

while True:
    for msg in bus:
    print("\n%2d\n" % cnt)

    # set debug = true make it to show inf of can-frame
    can_frame = VsmdCanFrame(msg, debug=True)
```

For an example,say frame 0004079F#0020000000000000 , it can be interpreted as below:
```
************************************************************                                                                                                             
| Main:  |                                                                                                                                                               
+ Raw                    :  0004079f#0020000000000000
+ Sender                 :  vcan0
+ Extent ID Frame        :  00000000001000000011110011111
+ DLC                    :  8
+ Data Frame             :  ['00200000', '00000000']

| Extend ID Frame |
+ Source Device          :  Pi
+ Target Device          :  BroadCast
+ Command Word           :  11
+ CMD or Register ADR    :  READ_DATA_REGS

| Action |
+ CW Means               :  CMD
| Data Frame |
+ Command                :  [('Data Reg Start:', <DataRegTable.CID: ['0000000', 'Channel ID', 'Determined by motor']>), ('Data Reg count:', 32)]                        
************************************************************
```

## Quick VSMD-CAN setup and drive

More function will be added soon.

```
from VSMD import CANFunctionList

bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000)
CANFunctionList.move("X",10,bus)

```

## Generate your own CMD

I have sealed most type of command of VSMD in script,you can import them like this:

```
from VSMD import CommonCMD
```

Which contains these sub-function:

* enable_motor(device: str)
    
    ENA  0x01
    
    CAN motor is allowed to move after ENA is ON
    
* disable_motor(device: str)

    OFF  0x02

    Make CAN motor ignore move cmd. Often used for broadcast

* move_motor(device: str, speed: int)

    MOV  0x05

    Move motor with specific speed. This is somehow dangerous

* stop_motor(device: str)

    STP  0x04

    Stop the motor now.

* move_to(device: str, pos: int)

    POS  0x06

    Mode to absolute pos.
    
* move_dis(device: str, dis: int)

    RMV  0x0B
    
    Mode to relative pos.

* read_status_regs(device: str, reg: StatusRegTable, cnt: int)

    READ STATUS REGS  0x1E

    Follow the PDF

* read_data_regs(device: str, reg: DataRegTable, cnt: int)
        
    READ DATA REGS  0x1F
        
    Follow the PDF
        
Note : set_data_regs is coming soon

