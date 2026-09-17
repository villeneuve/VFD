# Software for Linux to talk to the VFD

Here are useful scripts to dialog with the VFD.   
You may have to install the pymodbus Python library  

```
sudo apt install python3-pymodbus #Debian or derivative distributions
```

Some scripts are just plain text utilities. Example:  

 <img src="./ScreenShots/Screenshot%202026-01-09%2010.32.31.png">

The DialogVFD.py is more friendly, it's interactive with the user.  
You may have to install the Python Dialog library   
```
sudo apt install python3-dialog #Debian or derivative distributions
```  
This is how it looks.  

 <img src="./ScreenShots/Screenshot%202026-01-09%2010.28.57.png/">
 
It can monitor the VFD with a 2 seconds refresh rate 

<img src="./ScreenShots/Screenshot%202026-01-09%2010.30.17.png">

These scripts are pure Python and should be portable from Linux to Windows but I haven't tried.  
