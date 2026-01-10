# VFD (Variable Frequency Drive) on swimming pool water pump.  
This project is to use a VFD to drive the swimming pool water pump motor.  
The VFD is from CNWeiken the model is WK600D-0022-M1T : 1 phase 2.2kW.  
The swimming pool pump motor is rated 230Vac 50Hz 5.5A 1.2kW.  
## This is an ongoing project. This repository will grow with project progress  
## Last update January 2026  

This VFD was bought on [AliExpress](https://fr.aliexpress.com/item/1005007804372091.html?pdp_npi=4%40dis%21EUR%21%E2%82%AC%2083%2C68%21%E2%82%AC%2054%2C39%21%21%2196.00%2162.40%21%402103835e17588183866768574e4166%2112000042258239052%21sh%21FR%210%21X&spm=a2g0o.store_pc_allItems_or_groupList.new_all_items_2007523647771.1005007804372091&gatewayAdapt=glo2fra).  
The documentation can be found on [CNWeiken website](http://www.cnweiken.cn/upload/files/20230819/6382804255758362504914814.pdf?spm=a2g0o.detail.1000023.3.911b2tC62tC61r&file=6382804255758362504914814.pdf).  A copy is on this repository + the Modbus documentation.

For the moment I have tested the VFD driving the motor.  
It works as expected but I have returned it to the lab to test the communication with a computer.  
The VFD supports ModBus. I have tested it with a RS485 connection to a Linux computer. It works  as expected. The next step is to connect it to a microcontroller (most probably a raspberry pi pico) using microPython.  
So far I've written some Python scripts that are useful to dialog with the VFD. They are all here, in the SoftwareForLinux folder.  
You may have to install the pymodbus Python library 
```
sudo apt install python3-pymodbus #Debian or derivative distributions
```
Some scripts are just plain text utilities. Example:  

 <img src="https://github.com/villeneuve/VFD/blob/main/ScreenShots/Screenshot%202026-01-09%2010.32.31.png">

The DialogVFD.py is more friendly, it's interactive with the user.  
You may have to install the Python Dialog library 
```
sudo apt install python3-dialog #Debian or derivative distributions
```
This is how it looks.  

 <img src="https://github.com/villeneuve/VFD/blob/main/ScreenShots/Screenshot%202026-01-09%2010.28.57.png/">
 
It can monitor the VFD with a 2 seconds refresh rate 

<img src="https://github.com/villeneuve/VFD/blob/main/ScreenShots/Screenshot%202026-01-09%2010.30.17.png">

These scripts are pure Python and should be portable from Linux to Windows but I haven't tried.  

Ok I go to work on MicroPython now on...  + Hardware

## Changes, tricks, setting I did:   

Parameters changes:  
I set **P1-00=4** to get single-phase motor mode 2 = high-speed. It was set to 3   
According manufacturer:   
&emsp;&emsp;&emsp;&emsp; p1-00=3 single-phase motor mode 1 Output around 155V, low-speed mode    
&emsp;&emsp;&emsp;&emsp; p1-00=4 single-phase motor mode 2 Output around 215V, high-speed mode    
&emsp;&emsp;&emsp;&emsp; This complies with manufacturer [youtube video](https://www.youtube.com/watch?v=KAJoE-C64vI)   

To be able to communicate via ModBus with the Python ModBus library, I changed:    
**PD-05 from 30 to 31** (change from non standard to standard ModBus.)  

And finally these settings:   
**P0-02 = 2** (command source = communication)   
**P0-03 = 9** (Frequency set by communication)   
**P7-01 = 1** M/F key Switchover between operation panel control and remote command control.   
**P0-27 = 4** Binding operation panel command source to panel potentiometer   
So I have start/stop + Frequency setting via modbus in normal operation: remote (loc/rem LED blinking)  
If I press M/F key then it goes to local (loc/rem LED off) then I have start/stop + F (knob) from operation panel  
Press M/F again to return to remote mode  

**RS485 link:**  
I used a USB to RS485 adaptor on the host computer to connect to the VFD.  
I had many adaptor disconnections because I had connected A to A, B to B, and GND to GND  
When I disconnect the GND no more disconnection (it make sense because it's a differential bus. Searching the web also confirmed that. Many advices suggest not to connect GND).  
I also put a 120 ohms resistors at each end as recommended + a shielded cable.  
The connection is very robust now, no error, even at 115200 bauds.  

...






