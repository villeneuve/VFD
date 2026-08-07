from machine import Pin
import time
import sys
import asyncio
import uselect
from CetTime import cettime

button = Pin(6, Pin.IN, Pin.PULL_UP)

SERVER_TIME_OUT = 1000 * 60 * 5  #  ms 5 minutes
PERIODIC_SENSOR_READING = 30000 #  30 seconds
PERIODIC_DATA_READING = 40000 #  must be > PERIODIC_SENSOR_READING
PERIODIC_FAN_CONTROL = 50000 #  50 seconds
T_LCD_MAX = 10 * 1000  #  10 sec 

# We wait 5s to give time to all electronics to energize and init.
# if button is pressed during this time we exit to REPL,
# this is "maintenance mode"

count = 5
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

# ==Programme journalier ==
# Variables globales et imports necessaires
# defaut: start 35Hz a 6:00, 25Hz a 7:00 stop a 21:00
# format [(heure, minute, action), (heure, minute, action), etc..]
# progr = [(6, 0, 35), (7, 0, 25), (21, 0, 0)]  # liste de tuples
# progr is imported from common (the flag time_has_changed also)
import common
from Str2Tuple import str2tuple

async def action(a):
    try:
        if isinstance(a, int):
            try:
                if a == 0:   # sequence de stop demandee
                    try:
                        v.StopMotor()
                        print('[progr] Stop sequence 1/2 motor stopped. '\
                        'Pause 10 minutes.')
                        await asyncio.sleep(600)  # 10 minutes
                        v.OpenContactor()
                        print('[progr] Stop sequence 2/2 contactor open. End.')
                    except Exception as e:
                        print('[progr] Erreur en sequence de stop.')
                        print('[progr]', repr(e))                    
                elif a in range(20, 51): # 20 ~ 50 Hz only
                    if v.isonline and v.contactor_status:
                        try:
                            v.frequency_setpoint = a * 200
                            print('[progr] Frequency set to', a)
                        except Exception as e:
                            print('[progr] Erreur en reglant la frequence')
                            print('[progr]', repr(e))
                    else:
                        try:  # ici sequence de start 5mn a 45Hz etc.. 
                            v.CloseContactor()
                            print('[progr] Start sequence 1/4 contactor '\
                            'closed. Pause 1 minute.')
                            await asyncio.sleep(60)  # 1 minute
                            v.frequency_setpoint = 45 * 200
                            print('[progr] Start sequence 2/4 frequency '\
                            'set to 45Hz. Pause 1 minute.')
                            await asyncio.sleep(60)  # 1 minute 
                            v.StartMotor()
                            print('[progr] Start sequence 3/4 motor '\
                            'started. Pause 5 minutes.')
                            await asyncio.sleep(300)  # 5 minutes
                            v.frequency_setpoint = a * 200
                            print('[progr] Start sequence 4/4 frequency '\
                            'set to', a, 'End')
                        except Exception as e:
                            print("[progr] Erreur en sequence de start")
                            print('[progr]', repr(e))
                else:
                    print("[progr] Not in range 20~50Hz, or 0")
            except Exception as e:
                print("[progr] Erreur ici, en evaluant a.")
                print('[progr]', repr(e))
        else:
            print('[progr] Erreur : le parametre action/frequence doit '\
            'etre un entier')
    except Exception as e:
        print('[progr] Error in function action(a)')
        print('[progr]', repr(e)) 

async def main_1():

    # -------- DEBUG --------
    tempsDebut = time.ticks_ms()
    tmax = 50000  # ms
    jj = 0
    
    t_start_lcd = time.ticks_ms()
    t_start_sensors_reading = time.ticks_ms()
    t_start_data_reading = time.ticks_ms()
    t_start_fan_control = time.ticks_ms()

    print("--- Main 1 started ---")
    
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
            print("Reading sensors..")
            t_start_sensors_reading = time.ticks_ms()
            asyncio.create_task(read_sensors.get_sensors_value())
        # We read sensors values if available
        if read_sensors.sensors.flag_ready_to_read:
            read_sensors.sensors.flag_ready_to_read = False
            for i, id in enumerate(read_sensors.sensors.sensor_id):
                print(read_sensors.sensors.sensor_name[i], "=", \
                read_sensors.sensors.sensor_value[i], \
                "crc err:", read_sensors.sensors.sensor_crc_err[i], \
                "other err:", read_sensors.sensors.sensor_other_err[i], \
                end=' | ')
            print(" Total access to each sensor:", read_sensors.sensors.count)
            print("Last update time:", \
            time.localtime(read_sensors.sensors.last_update))
            
        if time.ticks_diff(time.ticks_ms(), t_start_data_reading) > \
                    PERIODIC_DATA_READING:
            t_start_data_reading = time.ticks_ms()
            v.GetAllData()
            print("Data:", v.all_data)
            
        if time.ticks_diff(time.ticks_ms(), t_start_fan_control) > \
                    PERIODIC_FAN_CONTROL:
            t_start_fan_control = time.ticks_ms()
            v.FanControl()

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

async def main_2():
    
    acceptable = [
    'ContactorOn', 'ContactorOff', 'MotorOn', 'MotorOff', 'SetFrequency',
    'SetDateTime', 'ReadAnyRegister', 'SetProgram', 'ShowProgram'
    ]
    
    print("--- Main 2 started ---")
    print("Listening on USB")
    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)
    buffer = ""
    
    while True:
        if poller.poll(0):
            char = sys.stdin.read(1)
            if char == '\n' or char == '\r':
                command = buffer.strip()
                cmd_lst = command.split()
                print("Command received:", command)
                # 1st test check cmd_lst is not empty (when received only \n)
                if cmd_lst and cmd_lst[0] in acceptable:
                    if len(cmd_lst) == 1:
                        if cmd_lst[0] == "ContactorOn":
                            print("Contactor ON order received")
                            v.CloseContactor()
                        elif cmd_lst[0] == "ContactorOff":
                            print("Contactor OFF order received")
                            v.OpenContactor()
                        elif cmd_lst[0] == "MotorOn":
                            print("Motor ON order received")
                            v.StartMotor()
                        elif cmd_lst[0] == "MotorOff":
                            print("Motor OFF order received")
                            v.StopMotor()
                        elif cmd_lst[0] == "ShowProgram":
                            print("Daily program :", common.progr)
                        else:
                            print("Invalid command. Parameter(s) missing?")
                    elif len(cmd_lst) == 2:
                        if cmd_lst[0] == "SetFrequency":
                            print("Set Frequency command received."
                                f" To set to : {cmd_lst[1]}")
                            try:
                                v.frequency_setpoint = int(cmd_lst[1]) * 200
                            except Exception as e:
                                print("Frequency must be an integer in 0~50Hz")
                                print(repr(e))
                        if cmd_lst[0] == "SetDateTime":
                            print("Set date and time command received."
                                f" To set to : {cmd_lst[1]}")
                            try:
                                cettime(int(cmd_lst[1]))
                                common.time_has_changed = True
                            except Exception as e:
                                print('Error when trying to set time')
                                print(repr(e))
                        if cmd_lst[0] == "SetProgram":
                            print("Set Program command received."
                                f" To set to : {cmd_lst[1]}")
                            try:
                                tmp_progr = str2tuple(cmd_lst[1])
                                if tmp_progr is not None:
                                    common.progr = tmp_progr
                                    print('OK. Program will change.')
                                else:
                                    print('Error when trying to convert' \
                                    ' string to tuple!')
                            except Exception as e:
                                print('Error when trying to set the program')
                                print(repr(e))
                    elif len(cmd_lst) == 3:
                        if cmd_lst[0] == "ReadAnyRegister":
                            print("Read any register command received."
                                f" To read from addr: {cmd_lst[1]}"
                                f" Register quantity: {cmd_lst[2]}")
                            if "x" in cmd_lst[1]:
                                try:
                                    print(v.ReadAnyRegister(addr=int\
                                    (cmd_lst[1], 16), count=int(cmd_lst[2])))
                                except Exception as e:
                                    print(
                                        "Failed to convert to int. "
                                        "Addr must be in Hex (i.e 0x7000)"
                                        " Qt'y in Decimal.")
                                    print(repr(e))
                            else:
                                print("Addr must be in Hex format: i.e 0x7000")
                else:
                    print('Commande invalide')
                buffer = "" # reinit for next time
            else:
                buffer += char
        await asyncio.sleep_ms(50)

async def main_3():
    
    # this main_3 process the daily program (vfd start/stop at fixed times)
    # we loop here every x seconds
    # we convert current hour and minute in a current minute variable (cm)
    # cm = (H*60)+M so from 00:00 ~ 23:29  --> 0 ~ 1439
    # Init
    x = 5  # we'll loop every x seconds
    pm = 1500  # previous minute = 1500 Because 1500 isn't possible we are 
               # sure to have a first run in the loop
    task = None
    print("--- Main 3 started ---")
    try:
        while True:
            if not common.time_has_changed:
                H, M = time.localtime()[3:5]
                cm = H * 60 + M
                if cm - pm > 1:  # we have missed one run (at least)
                    print("[progr] Ho! Error we missed one run. "\
                    "cm:", cm, "pm:", pm)
                    # to change to manage to do somethong. Exit?
                    # Or do nothing more than inform.. So OK like thet.
                else:
                    if cm == pm: 
                        # we already came here. It's not first time. so exit.
                        pass
                    else:
                        # print("[progr] Hour", H, "Minute", M, "cm", cm, "pm", pm)
                        pm = cm # we will not come back here. during this
                        # minute, we pass only once.
                        # print("[progr] Hour", H, "Minute", M, "cm", cm, "pm", pm)
                        ml = []
                        for item in common.progr:  # let's build a minutes list
                            ml.append(item[0] * 60 + item[1]) 
                        # print("[progr] ml", ml)
                        for index, item in enumerate(ml):
                            if item == cm:
                                # matching the program let's 'lauch the action
                                act = common.progr[index][2]
                                print('[progr] Matching. Action:', act, \
                                "Hour", H, "Minute", M )
                                # call coroutine only if not already running
                                task = task if task is not None and not \
                                task.done() else \
                                asyncio.create_task(action(act))
                                break
            else:
                common.time_has_changed = False
                pm = 1500  # we re-init at next loop
                print('[progr] Time has changed. Re-init program processing.')
            await asyncio.sleep(x)
    except Exception as e:
        print('[progr]', repr(e))

async def main():
    # main_1 is doing everything related to vfd, motor, etc..
    # main_2 listen the REPL (USB) for incoming commands
    # main_3 manage the pump daily program
    await asyncio.gather(main_1(), main_2(), main_3())

asyncio.run(main())
