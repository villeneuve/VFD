# This programm set the raspberry pi pico rtc to Central European Time (CET)
# the fonction cettime receives EPOCH as a parameter and set pico rtc to CET
# Winter (CET) is UTC+1H Summer (CEST) is UTC+2H
# Changes happen last Sundays of March (CEST) and October (CET) at 01:00 UTC
# Ref. formulas : http://www.webexhibits.org/daylightsaving/i.html
#                 Since 1996, valid through 2099
import time
from machine import RTC
rtc = RTC()

def cettime(pc_epoch):
    year = time.localtime(pc_epoch)[0]       #get current year
    HHMarch   = time.mktime((year,3 ,(31-(int(5*year/4+4))%7),1,0,0,0,0,0)) #Time of March change to CEST
    HHOctober = time.mktime((year,10,(31-(int(5*year/4+1))%7),1,0,0,0,0,0)) #Time of October change to CET
    if pc_epoch < HHMarch :                 # we are before last sunday of march
        cet = time.localtime(pc_epoch+3600) # CET:  UTC+1H
    elif pc_epoch < HHOctober :             # we are before last sunday of october
        cet = time.localtime(pc_epoch+7200) # CEST: UTC+2H
    else:                                   # we are after last sunday of october
        cet = time.localtime(pc_epoch+3600) # CET:  UTC+1H
    rtc.datetime((cet[0], cet[1], cet[2], 0, cet[3], cet[4], cet[5], 0))
