from machine import Pin
import time
import sys
import asyncio


button = Pin(6, Pin.IN, Pin.PULL_UP)

SERVER_TIME_OUT = 1000 * 60 * 5  # ms
# PERIODIC_SENSOR_READING = 5 * 60 * 1000  # ms every 5 minutes
PERIODIC_SENSOR_READING = 20000 #  Tests
# T_LCD_MAX = 5 * 60 * 1000  # 5 minutes
T_LCD_MAX = 10 * 1000  # 10 sec during tests

# We wait 5s to give time to all electronics to energize and init.
# if button is pressed during this time we exit to REPL,
# this is "maintenance mode"

# DEBUG
# count = 5
count = 1
maintenance = False
print('Starting. Step 1..')
print('To exit to REPL press the button within 5s.. ', end='')
while True:
    if button.value() == 0:  # Pressed
        print('Button Pressed. Exit to REPL, maintenance mode')
        maintenance = True
        break
    time.sleep(1)
    count -= 1
    print(count, '. ', end='')
    if count <= 0:  # 5x1s
        break
if maintenance:
    sys.exit()
# 5s elapsed and no maintenace mode requested the program continues

print('\nStarting. Step 2..')
from vfd_Obj import VFD, host

print('Starting step 3..')
time.sleep(1)
v = VFD(host)

if v.isonline:
    vfd_status = "On line"
    if v.SetFreq(10000):
        # At energization VFD frequency setpoint is 0 (On VFD itself)
        # If we give a start command with frequency setpoint = 0
        # the system freezes. So we MUST give a nonzero setpoint.
        print("Frequency set to 50Hz! Change it if you want.")
    else:
        print("Not possible VFD online and cannot set frequency :-(")
else:
    vfd_status = "Off line"
print('VFD', vfd_status)


import uselcd
print('Starting step 4..')
uselcd.lcd.clear()
uselcd.lcd.message("VFD " + vfd_status)

import web_server
print('Web server imported')

import read_sensors
print('read_sensors imported')


async def main_principal():

    # -------- DEBUG --------
    tempsDebut = time.ticks_ms()
    tmax = 6000  # ms
    jj = 0
    
    t_start_lcd = time.ticks_ms()
    t_start_sensors_reading = time.ticks_ms()

    print("--- Programme Principal Lancé ---")
    while True:

        # --- Gestion Bouton Serveur ---
        if button.value() == 0:
            print('Button pressed: Starting web server')
            time.sleep(0.2)  # Debounce delay
            time_start_server = time.ticks_ms()
            IP = web_server.demarrer_serveur(v)
            uselcd.lcd.clear()
            uselcd.lcd.display_top("Se connecter a :")
            uselcd.lcd.display_bottom(IP)

        # We test first if IDLE because Python will not test button
        # if idle (evaluate left to right). So we avoid more traffic on i2c
        if uselcd.s.state == uselcd.s.STATE_IDLE and uselcd.get_buttons():
            print('lcd button pressed: call menu on lcd')
            print('Main: uselcd.s.state=', uselcd.s.state)
            asyncio.create_task(uselcd.menu_driver(v))

        # Sensors reading (async, 750ms needed for DS18B20 temperature sensors)
        if time.ticks_diff(time.ticks_ms(), t_start_sensors_reading) > \
                    PERIODIC_SENSOR_READING:
            print("SENSORS READING.................")
            t_start_sensors_reading = time.ticks_ms()
            asyncio.create_task(read_sensors.get_sensors_value())
        # We read sensors values if available
        if read_sensors.sensors.flag_ready_to_read:
            read_sensors.sensors.flag_ready_to_read = False
            print(read_sensors.sensors.sensor_name)
            print(read_sensors.sensors.sensor_value)
            print(time.localtime(read_sensors.sensors.last_update))
            # Here we must send these values to who want them

        #  We clear lcd when nothing happen after T_LCD_MAX
        if uselcd.s.state == uselcd.s.STATE_IDLE \
        and not web_server.serveur_actif:
            if time.ticks_diff(time.ticks_ms(), t_start_lcd) > T_LCD_MAX:
                t_start_lcd = time.ticks_ms()
                uselcd.lcd.clear()
                uselcd.lcd.set_color([0,0,0])  # not needed but just in case..
        else:
            # No lcd clear when uselcd or web server running
            # Reset t_start_lcd to clear only after t_max_lcd after exit 
            # uselcd or exit web server
            t_start_lcd = time.ticks_ms()

        # --- Arret serveur sur timeout ---
        if web_server.serveur_actif:
            if time.ticks_diff(time.ticks_ms(), time_start_server) > \
                    SERVER_TIME_OUT:
                print('Demande arret serveur car temps >',
                      SERVER_TIME_OUT, 'ms')
                web_server.stop_serveur()

        # ------ DEBUG -----------
        if time.ticks_diff(time.ticks_ms(), tempsDebut) > tmax:
            tempsDebut = time.ticks_ms()
            print('Passe dans main loop. Nb fois :', jj)

        await asyncio.sleep_ms(10)
        jj += 1  # DEBUG

asyncio.run(main_principal())
