# MicroPython Raspberry Pi Pico softwares 



## the vfd.py script   
This script can read and write via ModBus to the VFD. It can do all the most useful tasks.   
There is a interactive mode and a non-interactive mode where you just call the needed function.   
Here are 2 screenshots:  

 <img src="https://github.com/villeneuve/VFD/blob/main/MicroPython/ScreenShots/20260130_14h13m04s_grim.png">

<img src="https://github.com/villeneuve/VFD/blob/main/MicroPython/ScreenShots/20260130_14h23m52s_grim.png">

## the vfd_bridge.py script 
This is the same as the vfd.py script + a bridge between UART0 and UART1. The VFD is on UART1 on RS485. 
A device can be connected on UART0 and can use ModBus to transparently dialog with the VFD. 
At the same time the REPL (usually on USB but can be webrepl) can also dialog with the VFD. 
There is a lock to avoid collision between the 2 channels (REPL + UART0) sharing the UART1.
A Linux computer can use the softwares in the SoftLinux folder of this repository to dialog with the VFD 
simultaneously with the MicroPython software on the REPL.
