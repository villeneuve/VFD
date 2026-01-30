So far I've written some Python scripts that are useful to dialog with the VFD. They are all here, in the SoftwareForLinux folder.  
You may have to install the pymodbus Python library 
```
sudo apt install python3-pymodbus #Debian or derivative distributions
```
Some scripts are just plain text utilities. Example:  

 <img src="https://github.com/villeneuve/VFD/blob/main/SoftLinux/ScreenShots/Screenshot%202026-01-09%2010.32.31.png">

The DialogVFD.py is more friendly, it's interactive with the user.  
You may have to install the Python Dialog library 
```
sudo apt install python3-dialog #Debian or derivative distributions
```
This is how it looks.  

 <img src="https://github.com/villeneuve/VFD/blob/main/SoftLinux/ScreenShots/Screenshot%202026-01-09%2010.28.57.png/">
 
It can monitor the VFD with a 2 seconds refresh rate 

<img src="https://github.com/villeneuve/VFD/blob/main/SoftLinux/ScreenShots/Screenshot%202026-01-09%2010.30.17.png">

These scripts are pure Python and should be portable from Linux to Windows but I haven't tried.  
