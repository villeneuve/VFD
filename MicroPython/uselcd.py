import machine
import time
from lcd_Adafruit_16x2_RGB_i2c import MCP23017, Adafruit_RGB_LCD
import asyncio
#from vfd_bridge import SetFreq

# --- CONFIGURATION I2C ---
i2c = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3), freq=400000)
try:
    mcp = MCP23017(i2c)
    lcd = Adafruit_RGB_LCD(mcp)
except Exception as e:
    print("Erreur Init:", e)
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
    await asyncio.sleep(0.05) # debounce delay

def zpad(val):
    """Zero padding for display (ex: 5 -> '05')"""
    return "{:02d}".format(val)
  
async def menu_driver(vfd):
    
    # Fréquence (variable stockée)
    freq_hz = 50 

    # long scroll message
    msg_usage = "Up/Down=change param Select=modifier ce param"

    # Menus
    menus = ["Reglage date", "Reglage heure", "Reglage frequence", "Moteur", "Contacteur"]
    menu_index = 0
    
    # ------- DEBUG ---
    tempsDebutMenuDriver = time.ticks_ms()
    tmaxMenuDriver = 2500 #ms
    print('Init menu_driver')
    ii = 0
    
    timeLastActivity = time.ticks_ms()
    tmaxActivity = 5000 #ms
    
    lcd.clear()
    lcd.set_color([100, 100, 100]) # White
    lcd.display_top(menus[menu_index])
    lcd.display_bottom(msg_usage)

    # Enter here from main : STATE_IDLE we change to STATE_MENU 
    s.state = s.STATE_MENU 
    
    # we must enter the loop with no button press
    # we wait release because button was pressed (in main)
    await wait_release()
    btns = 0
    
    while s.state : # we'll leave the loop when back to s.STATE_IDLE ( =0)
         
        # btns first read was done in main. 
        # btns is read again at this loop end.
        if btns:
            timeLastActivity = time.ticks_ms()
            await wait_release()
        
        lcd.tick()   # scroll
        
        ii +=1  # DEBUG
        
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
                    # [JJ, MM, AAAA] -> indices 2, 1, 0 du RTC
                    # Simplification : Année modifiable sur les 2 derniers digits
                    vals = [now[2], now[1], now[0] % 100] # Day, Month, Year(2digits)
                    year_prefix = (now[0] // 100) * 100
                    cursor_pos = 0 # 0-1: Jour, 2-3: Mois, 4-5: Année
                    # Date format = JJ:MM:AAAA
                    date_str = "{}:{}:{}".format(zpad(vals[0]), zpad(vals[1]), year_prefix + vals[2])
                    lcd.display_top("Date=" + date_str)
                    
                elif menu_index == 1:
                    s.state = s.STATE_EDIT_TIME
                    # Récupérer l'heure actuelle (YYYY, M, D, w, HH, MM, SS, ms)
                    now = rtc.datetime()
                    # On travaille sur [HH, MM, SS] -> indices 4, 5, 6
                    vals = [now[4], now[5], now[6]]
                    cursor_pos = 0 # 0=H_dizaine, 1=H_unité, 2=M_diz, 3=M_uni, 4=S_diz, 5=S_uni
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
                        lcd.display_top("Moteur :")
                        lcd.display_bottom("Tourne")
                    elif status == 3:
                        lcd.display_top("Moteur :")
                        lcd.display_bottom("A l'arret")
                    else :
                        lcd.display_bottom("Status inconnu")
                        lcd.display_top("VFD offline?")
                    
                elif menu_index == 4:
                    s.state = s.STATE_CONTACTEUR
                    lcd.display_bottom("Pas en service")
                    lcd.display_top("Travaux en cours")
                    
        elif s.state == s.STATE_EDIT_DATE :

            # Mapping curseur physique (Date= occupe 5 chars)
            # Format JJ:MM:AAAA -> curseur sur J1(5), J2(6), M1(8), M2(9), A3(13), A4(14)
            if cursor_pos < 2: phys = 5 + cursor_pos
            elif cursor_pos < 4: phys = 8 + (cursor_pos - 2)
            else: phys = 13 + (cursor_pos - 4)
            lcd.set_cursor(phys, 0)
            
            if btns:
                
                if btns & BTN_SELECT:
                    # Sauvegarde brute (sans verification validité jour/mois avancée pour cet exemple)
                    new_year = year_prefix + vals[2]
                    # rtc.datetime((YYYY, M, D, w, HH, MM, SS, ms))
                    new_dt = (new_year, vals[1], vals[0], now[3], now[4], now[5], now[6], 0)
                    rtc.datetime(new_dt)
                    s.state = s.STATE_MENU
                    lcd.blink_cursor(False)
                    menu_index = 1
                    lcd.display_top(menus[menu_index])
                    lcd.display_bottom(msg_usage)

                elif btns & BTN_RIGHT: cursor_pos = (cursor_pos + 1) % 6
                elif btns & BTN_LEFT: cursor_pos = (cursor_pos - 1) % 6
                
                elif btns & BTN_UP or btns & BTN_DOWN:
                    direction = 1 if (btns & BTN_UP) else -1
                    
                    # Identification de ce qu'on modifie
                    if cursor_pos < 2: idx = 0; max_val = 31 # Jour
                    elif cursor_pos < 4: idx = 1; max_val = 12 # Mois
                    else: idx = 2; max_val = 99 # Année
                    
                    tens = vals[idx] // 10
                    units = vals[idx] % 10
                    is_tens = (cursor_pos % 2 == 0)
                    
                    if is_tens:
                        limit = max_val // 10
                        tens = (tens + direction) 
                        if tens < 0: tens = limit
                        if tens > limit: tens = 0
                        # Clip units if overflow (ex 39 jours)
                        if (tens * 10 + units) > max_val: units = max_val % 10
                    else:
                        limit = 9
                        # Cas particuliers pour limites précises (ex mois pas > 2 si dizaine=1)
                        if idx == 1 and tens == 1: limit = 2
                        if idx == 0 and tens == 3: limit = 1
                        
                        units += direction
                        if units < 0: units = limit
                        if units > limit: units = 0
                    
                    new_val = tens * 10 + units
                    if new_val == 0 and idx < 2: new_val = 1 # Pas de jour 0 ou mois 0
                    vals[idx] = new_val
                    date_str = "{}:{}:{}".format(zpad(vals[0]), zpad(vals[1]), year_prefix + vals[2])
                    lcd.display_top("Date=" + date_str)
            
        elif s.state == s.STATE_EDIT_TIME :

            # Positionnement curseur LCD (format HH:MM:SS)
            # Mapping curseur logique (0-5) -> curseur physique (8,9, 11,12, 14,15)
            phys_pos = 8 + cursor_pos + (cursor_pos // 2)
            lcd.set_cursor(phys_pos, 0)
            
            if btns:
                if btns & BTN_SELECT:
                    # Sauvegarde
                    # rtc.datetime((YYYY, M, D, w, HH, MM, SS, ms))
                    new_dt = (now[0], now[1], now[2], now[3], vals[0], vals[1], vals[2], 0)
                    rtc.datetime(new_dt)
                    s.state = s.STATE_MENU
                    lcd.blink_cursor(False)
                    menu_index = 0
                    lcd.display_top(menus[menu_index])
                    lcd.display_bottom(msg_usage)

                elif btns & BTN_RIGHT:
                    cursor_pos = (cursor_pos + 1) % 6
                
                elif btns & BTN_LEFT:
                    cursor_pos = (cursor_pos - 1) % 6
                    
                elif btns & BTN_UP or btns & BTN_DOWN:
                    direction = 1 if (btns & BTN_UP) else -1
                    
                    # Logique modification chiffre par chiffre
                    # On décompose la valeur courante (ex: 14 -> 1 et 4)
                    if cursor_pos < 2: # HEURES
                        idx = 0
                        limit_high_diz = 2
                        limit_high_uni = 9 if vals[0] < 20 else 3
                    elif cursor_pos < 4: # MINUTES
                        idx = 1
                        limit_high_diz = 5
                        limit_high_uni = 9
                    else: # SECONDES
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
                        # Correction auto si on passe 19h -> 29h (interdit) -> 23h
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
                # HERE we must set the frequency
                #vfd.SetFreq(freq_hz * 200)  # use method
                vfd.frequency_setpoint = freq_hz * 200 # use property
                
            elif btns & BTN_UP:
                if freq_hz < 50: freq_hz += 1
                lcd.display_top("Frequence={}Hz".format(freq_hz))
                
            elif btns & BTN_DOWN:
                if freq_hz > 20: freq_hz -= 1
                lcd.display_top("Frequence={}Hz".format(freq_hz))
        
        elif s.state == s.STATE_MOTEUR :
            if btns :
                s.state = s.STATE_MENU
                menu_index = 0
                lcd.display_top(menus[menu_index])
                lcd.display_bottom(msg_usage)
        
        elif s.state == s.STATE_CONTACTEUR :
            if btns :
                s.state = s.STATE_MENU
                menu_index = 0
                lcd.display_top(menus[menu_index])
                lcd.display_bottom(msg_usage)
                         
        # --- DEBUG ----            
        if time.ticks_diff(time.ticks_ms(), tempsDebutMenuDriver ) > tmaxMenuDriver :
            print('Hi from uselcd, ii =', ii)
            tempsDebutMenuDriver = time.ticks_ms()
        
        # Timeout
        if time.ticks_diff(time.ticks_ms(), timeLastActivity ) > tmaxActivity :
            s.state = s.STATE_IDLE  # sortie de la boucle
            lcd.set_color([0,0,0])
            # Display date and time before leaving
            cc = rtc.datetime()
            tt = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}".format(cc[2],cc[1],cc[0],cc[4],cc[5])
            lcd.clear()
            lcd.display_top(tt)
        
        # read the buttons for next round in the loop
        btns = get_buttons()
        
        await asyncio.sleep(0.01)

    print('EXIT menu_driver. s.state =', s.state)
        
