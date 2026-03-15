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

## main.py
This is the first issue of main.py that will run when the pico boots.  
It uses asyncio to run several tasks simultaneously :  
 - Driving the vfd with vfd.py (vfd.py must be updated to be simpler and vfd must be an object).  
 - Driving the lcd with uselcd.py (and a slighty modified version of lcd_Adafruit_16x2_RGB_i2c.py compared to the 
 one [here](https://github.com/villeneuve/micropython-lcd-adafruit-16x2-rgb-i2c)).
  uselcd.py has a menu system to set the frequency, the date, the time,
   ( and to come : start/stop the motor and close/open the contactor)  
 - Runs vfd_bridge.py to allow ModBus command from a PC connected to the pico UART0.   
 - Runs a web server. When a push button is pressed starts the WiFi in access point, displays IP to connect at on the lcd, 
 and runs the server showing vfd - motor - contactor status, actions possible: set the frequency, start/stop
  motor and contactor.
  
  All these functions are still in development this is alpha release.  
  
  
 
