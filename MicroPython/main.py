from machine import Pin
import time
import sys
import asyncio
import uselect

button = Pin(6, Pin.IN, Pin.PULL_UP)

SERVER_TIME_OUT = 1000 * 60 * 5  # ms
# PERIODIC_SENSOR_READING = 5 * 60 * 1000  # ms every 5 minutes
PERIODIC_SENSOR_READING = 20000 #  Tests
PERIODIC_DATA_READING = 30000 # must be > PERIODIC_SENSOR_READING
PERIODIC_FAN_CONTROL = 50000 # Tests
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

async def main_1():

    # -------- DEBUG --------
    tempsDebut = time.ticks_ms()
    tmax = 6000  # ms
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
            print("SENSORS READING.................")
            t_start_sensors_reading = time.ticks_ms()
            asyncio.create_task(read_sensors.get_sensors_value())
        # We read sensors values if available
        if read_sensors.sensors.flag_ready_to_read:
            read_sensors.sensors.flag_ready_to_read = False
            for i, id in enumerate(read_sensors.sensors.sensor_id):
                print(read_sensors.sensors.sensor_name[i], "=", \
                read_sensors.sensors.sensor_value[i], \
                "crc err:", read_sensors.sensors.sensor_crc_err[i], \
                "other err:", read_sensors.sensors.sensor_other_err[i] )
            print("Last update time:", \
            time.localtime(read_sensors.sensors.last_update))
            print("Total access to each sensor:", read_sensors.sensors.count)
            
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
    'SetDateTime', 'ReadAnyRegister'
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
                print('cmd_lst[0] : ', cmd_lst[0])
                if cmd_lst[0] in acceptable:
                    print('Acceptable')
                    if len(cmd_lst) == 1:
                        print(f"\n[LEN 1 Command received : {command}]")
                        print(f"len de cmd_lst : {len(cmd_lst)}")
                        print(cmd_lst, cmd_lst[0])
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
                        else:
                            print("Invalid command. Parameter(s) missing?")
                    elif len(cmd_lst) == 2:
                        print(f"\n[LEN 2 Command received : {command}]")
                        print(f"len de cmd_lst : {len(cmd_lst)}")
                        print(cmd_lst, cmd_lst[0])
                        if cmd_lst[0] == "SetFrequency":
                            print("Set Frequency command received."
                                f" To set to : {cmd_lst[1]}")
                            try:
                                v.frequency_setpoint = int(cmd_lst[1]) * 200
                            except:
                                print("Frequency must be an integer in 0~50Hz")
                        if cmd_lst[0] == "SetDateTime":
                            print("Set date and time command received."
                                f" To set to : {cmd_lst[1]}")
                    elif len(cmd_lst) == 3:
                        print(f"\n[LEN 3 Command received : {command}]")
                        print(f"len de cmd_lst : {len(cmd_lst)}")
                        if cmd_lst[0] == "ReadAnyRegister":
                            print("Read any register command received."
                                f" To read from addr: {cmd_lst[1]}"
                                f" Register quantity: {cmd_lst[2]}")
                            if "x" in cmd_lst[1]:
                                try:
                                    print(v.ReadAnyRegister(addr=int\
                                    (cmd_lst[1], 16), count=int(cmd_lst[2])))
                                except:
                                    print(
                                        "Failed to convert to int. "
                                        "Addr must be in Hex (i.e 0x7000)"
                                        " Qt'y in Decimal.")
                            else:
                                print("Addr must be in Hex format: i.e 0x7000")
                else:
                    print('Commande invalide')
                buffer = "" # reinit for next time
            else:
                buffer += char
        await asyncio.sleep_ms(50)

async def main():
    # main_1 is the doing everything related to vfd, motor, etc..
    # main_2 listen the REPL (USB) for incoming commands
    await asyncio.gather(main_1(), main_2())

asyncio.run(main())
