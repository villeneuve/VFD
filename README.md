# VFD (Variable Frequency Drive) on swimming pool water pump.  


# Contents  

1. [Introduction](./README.md#1-introduction)   
 1.1 [Why a VFD](./README.md#11-why-a-vfd)   
 1.2 [Project overview](./README.md#12-project-overview)   


qdqdqd
qdqdq
qsdqdqs
qsdqdqd
qdqdqsd
qsdqdq
qsdqdq
qdqdqd
qsdqdsqd
qsddqd
TEST TESTS 
UNDER WORKS
iiiiiiiiiiii


# 1. Introduction   

et oui ici intro

## 1.1 Why a VFD?   

parceque je le veux

## 1.2 Project overview   

ceci est le p overview







This project uses a VFD to drive the swimming pool water pump motor.  
The VFD is from CNWeiken the model is **WK600D-0022-M1T : 1 phase 2.2kW**.  
The swimming pool pump motor is rated **230Vac 50Hz 5.5A 1.2kW**.  
## This is an ongoing project. This repository will grow with project progress  
## Last update 2 July 2026  (almost finished now)

This VFD was bought on [AliExpress](https://fr.aliexpress.com/item/1005007804372091.html?pdp_npi=4%40dis%21EUR%21%E2%82%AC%2083%2C68%21%E2%82%AC%2054%2C39%21%21%2196.00%2162.40%21%402103835e17588183866768574e4166%2112000042258239052%21sh%21FR%210%21X&spm=a2g0o.store_pc_allItems_or_groupList.new_all_items_2007523647771.1005007804372091&gatewayAdapt=glo2fra).  
The documentation can be found on [CNWeiken website](http://www.cnweiken.cn/upload/files/20230819/6382804255758362504914814.pdf?spm=a2g0o.detail.1000023.3.911b2tC62tC61r&file=6382804255758362504914814.pdf).     
A copy of this doc + the Modbus documentation is on this repository in the Documentation folder.     

The VFD is now installed in its cabinet and is running. It drives the swimming pool water pump. It's working as expected.  

The control system (the Raspberry pi Pico) is not yet installed on site. It is still under development. 
The software is almost ready. Check the MicroPython folder to see it.

The VFD supports ModBus. I have tested it with a RS485 connection to a Linux computer. It works  as expected.    
I have now connected it to a raspberry pi pico using microPython. It works  as expected.    

For Linux check folder SoftLinux.   
For MicroPython check folder MicroPython.   

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

To connect to the Raspberry Pi Pico I used a serial to RS485 adaptor connected pico UART1. 



**Here are photos of the VFD in its cabinet.**


<img src="https://github.com/villeneuve/VFD/blob/main//Hardware/Pictures/CoffretInt.png">    
<img src="./Hardware/Pictures/CoffretInt.png">


<img src="https://github.com/villeneuve/VFD/blob/main//Hardware/Pictures/CoffretExt.png">


When I started the VFD for the first time I had several ElectroMagnetic Interferences (EMI).  
The PLC network adaptors that I use nearby stop working,   
A 1wire humidity sensor inside the house started to give wrong values.
And a current measure system, also located 20m away, started to give wrong values as well.  
So I ordered and installed an EMI filter, it is the stainless steel box located just above the VFD.  
It worked perfectly, no more problem.   

I decided to add a fan in the cabinet.  
It isn't absolutely necessary but the cabinet is located on the west and the sun hit it in the afternoon.  
In summer when it's more than 30°C outside, the internal VFD temperature can reach 50°C.  
This is still ok for the VFD (maximum is 75°C in mfr doc).  
With the fan I keep VFD temperature below 38°C.   
The fan is PWM driven by the raspberry pi pico W and fan speed varies with VFD temperature.  

PICO BOARD    



FAN    

