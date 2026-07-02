import machine
import time
from lcd_Adafruit_16x2_RGB_i2c import MCP23017, Adafruit_RGB_LCD
import asyncio

# --- CONFIGURATION I2C ---
i2c = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3), freq=400000)
try:
    mcp = MCP23017(i2c)
    lcd = Adafruit_RGB_LCD(mcp)
except Exception as e:
    print("[uselcd] Erreur Init:", e)
    while True: pass

# --- MASQUES BOUTONS (basés sur pinout MCP) ---
BTN_SELECT = 1 << 0 # Bit 0
BTN_RIGHT  = 1 << 1 # Bit 1
BTN_DOWN   = 1 << 2 # Bit 2
BTN_UP     = 1 << 3 # Bit 3
BTN_LEFT   = 1 << 4 # Bit 4

rtc = machine.RTC()

# the state machine to keep lcd / menu states
class STATE:
    def __init__(self, state):
        self.state = state
        self.STATE_IDLE      = 0
        self.STATE_MENU      = 1
        self.STATE_EDIT_DATE = 2
        self.STATE_EDIT_TIME = 3
        self.STATE_EDIT_FREQ = 4
        self.STATE_MOTEUR    = 5
        self.STATE_CONTACTEUR = 6

s = STATE(0)

def get_buttons():
    return lcd.all_buttons

async def wait_release():
    while lcd.all_buttons != 0:
        await asyncio.sleep(0.01)
    await asyncio.sleep(0.05) #  debounce delay

def zpad(val):
    """Zero padding for display (ex: 5 -> '05')"""
    return "{:02d}".format(val)
  
async def menu_driver(vfd):
    
    # Reading frequency set point. Set to 50 if vfd offline
    if vfd.isonline:
        freq_hz = int(int(vfd.frequency_setpoint) / 200)
    else:
        freq_hz = 50

    # long scroll message
    msg_usage = "Up/Down=change param Select=modifier ce param"

    # Menus
    menus = ["Reglage date", "Reglage heure", "Reglage frequence", "Moteur", "Contacteur"]
    menu_index = 0
        
    # ------- DEBUG ---
    tempsDebutMenuDriver = time.ticks_ms()
    tmaxMenuDriver = 5000 #  ms
    print('[uselcd] Init menu_driver')
    ii = 0
    
    timeLastActivity = time.ticks_ms()
    tmaxActivity = 15000 #  ms
    
    lcd.clear()
    lcd.set_color([100, 100, 100]) #  White
    lcd.display_top(menus[menu_index])
    lcd.display_bottom(msg_usage)

    # Enter here from main : STATE_IDLE we change to STATE_MENU 
    s.state = s.STATE_MENU 
    
    # we must enter the loop with no button pressed
    # we wait release because button was pressed (in main)
    await wait_release()
    btns = 0
    
    # --- Variables pour la gestion de l'appui long ---
    last_btns = 0
    next_repeat = 0
    
    while s.state : # we'll leave the loop when back to s.STATE_IDLE ( =0)
         
        # Gestion intelligente de la répétition des touches
        if btns:
            timeLastActivity = time.ticks_ms()
            
            # Si c'est une touche de navigation, on active le défilement continu
            if btns & (BTN_UP | BTN_DOWN | BTN_LEFT | BTN_RIGHT):
                ticks_now = time.ticks_ms() # <-- CORRECTION ICI : 'now' devient 'ticks_now'
                if btns != last_btns:
                    last_btns = btns
                    next_repeat = time.ticks_add(ticks_now, 400) # Délai initial avant répétition (400ms)
                else:
                    if time.ticks_diff(ticks_now, next_repeat) >= 0:
                        next_repeat = time.ticks_add(ticks_now, 120) # Vitesse de défilement (120ms)
                    else:
                        btns = 0 # On ignore l'appui pour ce cycle de boucle
            else:
                # Pour le bouton SELECT, on conserve la sécurité d'attente du relâchement
                await wait_release()
                last_btns = 0
        else:
            last_btns = 0
        
        lcd.tick() #  scroll
        
        ii +=1 #  DEBUG
        
        # --- ETAT MENU ---
        if s.state == s.STATE_MENU :
            
            if btns & BTN_UP:
                menu_index = (menu_index + 1) % len(menus)
                lcd.display_top(menus[menu_index])
                
            elif btns & BTN_DOWN:
                menu_index = (menu_index - 1) % len(menus)
                lcd.display_top(menus[menu_index])
                
            elif btns & BTN_SELECT:
                if menu_index == 0:
                    s.state = s.STATE_EDIT_DATE
                    lcd.clear()
                    lcd.display_bottom("Up/Dn=val R/L=mv")
                    lcd.blink_cursor(True)
                    now = rtc.datetime()
                    vals = [now[2], now[1], now[0] % 100] # Day, Month, Year(2digits)
                    year_prefix = (now[0] // 100) * 100
                    cursor_pos = 0 # 0-1: Jour, 2-3: Mois, 4-5: Année
                    date_str = "{}:{}:{}".format(zpad(vals[0]), zpad(vals[1]), year_prefix + vals[2])
                    lcd.display_top("Date=" + date_str)
                    
                elif menu_index == 1:
                    s.state = s.STATE_EDIT_TIME
                    now = rtc.datetime()
                    vals = [now[4], now[5], now[6]]
                    cursor_pos = 0 
                    lcd.clear()
                    lcd.display_bottom("Up/Dn=val R/L=mv")
                    lcd.blink_cursor(True)
                    time_str = "{}:{}:{}".format(zpad(vals[0]), zpad(vals[1]), zpad(vals[2]))
                    lcd.display_top("Heure = " + time_str)
                    
                elif menu_index == 2:
                    s.state = s.STATE_EDIT_FREQ
                    lcd.display_bottom("Up/Down=+-1Hz")
                    lcd.display_top("Frequence={}Hz".format(freq_hz))
                    
                elif menu_index == 3:
                    s.state = s.STATE_MOTEUR
                    status = vfd.MotorStatus()
                    if status == 1:
                        lcd.display_top("Moteur tourne")
                        lcd.display_bottom("Select=OFF autre touche=quitter")
                    elif status == 3:
                        lcd.display_top("Moteur arret")
                        lcd.display_bottom("Select=ON autre touche=quitter")
                    else :
                        lcd.display_top("Etat inconnu")
                        lcd.display_bottom("VFD offline?")
                    
                elif menu_index == 4:
                    s.state = s.STATE_CONTACTEUR
                    if vfd.contactor_status:
                        lcd.display_top("Contacteur ON")
                    else:
                        lcd.display_top("Contacteur OFF")
                    lcd.display_bottom("Select=ON/OFF autre touche=quitter")

        elif s.state == s.STATE_EDIT_DATE :

            if cursor_pos < 2: phys = 5 + cursor_pos
            elif cursor_pos < 4: phys = 8 + (cursor_pos - 2)
            else: phys = 13 + (cursor_pos - 4)
            lcd.set_cursor(phys, 0)
            
            if btns:
                if btns & BTN_SELECT:
                    new_year = year_prefix + vals[2]
                    new_dt = (new_year, vals[1], vals[0], now[3], now[4], now[5], now[6], 0)
                    rtc.datetime(new_dt)
                    s.state = s.STATE_MENU
                    lcd.blink_cursor(False)
                    menu_index = 1
                    lcd.display_top(menus[menu_index])
                    lcd.display_bottom(msg_usage)
                    print("[uselcd] From uselcd: Action set time")

                elif btns & BTN_RIGHT: cursor_pos = (cursor_pos + 1) % 6
                elif btns & BTN_LEFT: cursor_pos = (cursor_pos - 1) % 6
                
                elif btns & BTN_UP or btns & BTN_DOWN:
                    direction = 1 if (btns & BTN_UP) else -1
                    
                    if cursor_pos < 2: idx = 0; max_val = 31 
                    elif cursor_pos < 4: idx = 1; max_val = 12 
                    else: idx = 2; max_val = 99 
                    
                    tens = vals[idx] // 10
                    units = vals[idx] % 10
                    is_tens = (cursor_pos % 2 == 0)
                    
                    if is_tens:
                        limit = max_val // 10
                        tens = (tens + direction) 
                        if tens < 0: tens = limit
                        if tens > limit: tens = 0
                        if (tens * 10 + units) > max_val: units = max_val % 10
                    else:
                        limit = 9
                        if idx == 1 and tens == 1: limit = 2
                        if idx == 0 and tens == 3: limit = 1
                        
                        units += direction
                        if units < 0: units = limit
                        if units > limit: units = 0
                    
                    new_val = tens * 10 + units
                    if new_val == 0 and idx < 2: new_val = 1 
                    vals[idx] = new_val
                    date_str = "{}:{}:{}".format(zpad(vals[0]), zpad(vals[1]), year_prefix + vals[2])
                    lcd.display_top("Date=" + date_str)
            
        elif s.state == s.STATE_EDIT_TIME :

            phys_pos = 8 + cursor_pos + (cursor_pos // 2)
            lcd.set_cursor(phys_pos, 0)
            
            if btns:
                if btns & BTN_SELECT:
                    new_dt = (now[0], now[1], now[2], now[3], vals[0], vals[1], vals[2], 0)
                    rtc.datetime(new_dt)
                    s.state = s.STATE_MENU
                    lcd.blink_cursor(False)
                    menu_index = 0
                    lcd.display_top(menus[menu_index])
                    lcd.display_bottom(msg_usage)
                    print("[uselcd] From uselcd: Action set time")

                elif btns & BTN_RIGHT:
                    cursor_pos = (cursor_pos + 1) % 6
                
                elif btns & BTN_LEFT:
                    cursor_pos = (cursor_pos - 1) % 6
                    
                elif btns & BTN_UP or btns & BTN_DOWN:
                    direction = 1 if (btns & BTN_UP) else -1
                    
                    if cursor_pos < 2: 
                        idx = 0
                        limit_high_diz = 2
                        limit_high_uni = 9 if vals[0] < 20 else 3
                    elif cursor_pos < 4: 
                        idx = 1
                        limit_high_diz = 5
                        limit_high_uni = 9
                    else: 
                        idx = 2
                        limit_high_diz = 5
                        limit_high_uni = 9
                    
                    tens = vals[idx] // 10
                    units = vals[idx] % 10
                    is_tens_digit = (cursor_pos % 2 == 0)
                    
                    if is_tens_digit:
                        tens = (tens + direction)
                        if tens < 0: tens = limit_high_diz
                        if tens > limit_high_diz: tens = 0
                        if idx == 0 and tens == 2 and units > 3: units = 3 
                    else:
                        units = (units + direction)
                        if units < 0: units = limit_high_uni
                        if units > limit_high_uni: units = 0
                    
                    vals[idx] = tens * 10 + units
                    time_str = "{}:{}:{}".format(zpad(vals[0]), zpad(vals[1]), zpad(vals[2]))
                    lcd.display_top("Heure = " + time_str)
            
        elif s.state == s.STATE_EDIT_FREQ :
            
            if btns & BTN_SELECT:
                s.state = s.STATE_MENU
                menu_index = 0
                lcd.display_top(menus[menu_index])
                lcd.display_bottom(msg_usage)
                vfd.frequency_setpoint = freq_hz * 200 
                print("[uselcd] Action set frequency ", freq_hz)
                
            elif btns & BTN_UP:
                if freq_hz < 50: freq_hz += 1
                lcd.display_top("Frequence={}Hz".format(freq_hz))
                
            elif btns & BTN_DOWN:
                if freq_hz > 20: freq_hz -= 1
                lcd.display_top("Frequence={}Hz".format(freq_hz))
        
        elif s.state == s.STATE_MOTEUR :
            if btns & BTN_SELECT:
                if status == 1:
                    vfd.StopMotor()
                    print("[uselcd] Action STOP")
                elif status == 3:
                    vfd.StartMotor()
                    print("[uselcd] Action START")
                else:
                    print("[uselcd] No ACTION")
                    pass 
            if btns :
                s.state = s.STATE_MENU
                menu_index = 0
                lcd.display_top(menus[menu_index])
                lcd.display_bottom(msg_usage)
        
        elif s.state == s.STATE_CONTACTEUR :
            if btns & BTN_SELECT:
                if vfd.contactor_status:
                    vfd.OpenContactor()
                    print("[uselcd] Action open contactor")
                else:
                    vfd.CloseContactor()
                    print("[uselcd] Action close contactor")
            if btns :
                s.state = s.STATE_MENU
                menu_index = 0
                lcd.display_top(menus[menu_index])
                lcd.display_bottom(msg_usage)
                         
        # --- DEBUG ----            
        if time.ticks_diff(time.ticks_ms(), tempsDebutMenuDriver ) > tmaxMenuDriver :
            print('[uselcd] running, times in loop =', ii)
            tempsDebutMenuDriver = time.ticks_ms()
        
        # Timeout
        if time.ticks_diff(time.ticks_ms(), timeLastActivity ) > tmaxActivity :
            s.state = s.STATE_IDLE  
            lcd.set_color([0,0,0])
            cc = rtc.datetime()
            tt = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}".format(cc[2],cc[1],cc[0],cc[4],cc[5])
            lcd.clear()
            lcd.display_top(tt)
        
        # read the buttons for next round in the loop
        btns = get_buttons()
        
        await asyncio.sleep(0.01)

    print('[uselcd] EXIT menu_driver. s.state =', s.state)
    
