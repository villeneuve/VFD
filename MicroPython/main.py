from machine import Pin
import time
import sys
import asyncio


button = Pin(6, Pin.IN, Pin.PULL_UP)

SERVER_TIME_OUT = 60000 #ms

# We wait 5s to give time to all electronics to energize and init 
# if button is pressed during this time we exit to REPL this is "maintenance mode"

# DEBUG
# count = 5
count = 1
maintenance = False
print('Starting. Step 1..')
print('To exit to REPL press the button within 5s.. ',end='')
while True:
    if button.value() == 0: # Pressed
        print('Button Pressed. Exit to REPL, maintenance mode')
        maintenance = True
        break
    time.sleep(1) 
    count -= 1
    print(count,'. ',end='')
    if count <= 0: # 5x1s
        break
if maintenance:
    sys.exit()

# 5s elapsed and no maintenace mode requested the program continues
print('\nStarting. Step 2..')

from vfd_Obj import VFD, host
print('Starting step 3..')
time.sleep(1)

v = VFD(host)
if v.SetFreq(10000):  # Return True if VFD is online (and set F to 50Hz)
    vfd_status = "On line"
else:
    vfd_status = "Off line"  
print('VFD',vfd_status)

import uselcd
print('Starting step 4..')
uselcd.lcd.clear()
uselcd.lcd.message("VFD "+vfd_status)

import web_server
print('Web server imported')

async def main_principal():
    
    # -------- DEBUG --------
    tempsDebut = time.ticks_ms()
    tmax = 3000 #ms
    jj = 0
    
    print("--- Programme Principal Lancé ---")
    while True:
        
        # --- Gestion Bouton Serveur ---
        if button.value() == 0:
            print('Button pressed: Starting web server')
            time.sleep(0.2) # Debounce delay
            time_start_server = time.ticks_ms()
            IP = web_server.demarrer_serveur()
            uselcd.lcd.clear()
            uselcd.lcd.display_top("Se connecter a :")
            uselcd.lcd.display_bottom(IP)
            
        # We test first if IDLE because Python will not test button
        # if idle (evaluate left to right). So we avoid more traffic on i2c    
        if uselcd.s.state == uselcd.s.STATE_IDLE and uselcd.get_buttons() :
            print('lcd button pressed: call menu on lcd')
            print('Main: uselcd.s.state=', uselcd.s.state)
            asyncio.create_task(uselcd.menu_driver(v))          
            
        # Ici il faudra lire les capteurs (et etat vfd?)
        
        # --- Arret serveur sur timeout ---
        if web_server.serveur_actif:
            if time.ticks_diff(time.ticks_ms(), time_start_server) > SERVER_TIME_OUT :
                print('Demande arret serveur car temps >',SERVER_TIME_OUT,'ms')
                web_server.stop_serveur()
                
        # ------ DEBUG -----------
        if time.ticks_diff(time.ticks_ms(), tempsDebut ) > tmax :
            tempsDebut = time.ticks_ms()
            print('Passe dans main loop. Nb fois :', jj)
                
        await asyncio.sleep_ms(10)
        jj +=1 # DEBUG

asyncio.run(main_principal())
