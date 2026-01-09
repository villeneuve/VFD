#! /usr/bin/env python3

# Guy Decembre 2025 -- Gujan
# This program communicate with the CNWeiken WK600 VFD via ModBus

from dialog import Dialog
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import locale
import time

VFDdataList=[
'Setup value ( Decimal)',
'Running frequency     ',
'Bus voltage           ',
'Output voltage        ',
'Output voltage        ',
'Output power          ',
'Output torque         ',
'Running speed         ',
'DI input flag         ',
'DO output flag        ',
'AI1 voltage           ',
'AI2 voltage           ',
'AI3 voltage           ',
'Counting value input  ',
'Length value input    ',
'Load speed            ',
'PID setup             ',
'PID feedback          ',
'PLC process           ',
'Register 1013H        '
]

# Main monitoring parameter list for Group U0
# Format: [Code, Name, Min. Unit, Address, Value]
monitoring_parameters = [
    ["U0-00", "Running frequency (Hz)", "0.01 Hz", "0x7000", ""],
    ["U0-01", "Set frequency (Hz)", "0.01 Hz", "0x7001", ""],
    ["U0-02", "Bus voltage", "0.1 V", "0x7002", ""],
    ["U0-03", "Output voltage", "1 V", "0x7003", ""],
    ["U0-04", "Output current", "0.01 A", "0x7004", ""],
    ["U0-05", "Output power", "0.1 kW", "0x7005", ""],
    ["U0-06", "Output torque", "0.1%", "0x7006", ""],
    ["U0-07", "X state", "1", "0x7007", ""],
    ["U0-08", "DO state", "1", "0x7008", ""],
    ["U0-09", "AI1 voltage (V)", "0.01 V", "0x7009", ""],
    ["U0-10", "AI2 voltage (V)/current (mA)", "0.01 V/0.01 mA", "0x700A", ""],
    ["U0-11", "AI3 voltage (V)", "0.01 V", "0x700B", ""],
    ["U0-12", "Count value", "1", "0x700C", ""],
    ["U0-13", "Length value", "1", "0x700D", ""],
    ["U0-14", "Load speed", "1", "0x700E", ""],
    ["U0-15", "PID setting", "1", "0x700F", ""],
    ["U0-16", "PID feedback", "1", "0x7010", ""],
    ["U0-17", "PLC stage", "1", "0x7011", ""],
    ["U0-18", "Input pulse frequency (Hz)", "0.01 kHz", "0x7012", ""],
    ["U0-19", "Feedback speed", "0.01 Hz", "0x7013", ""],
    ["U0-20", "Remaining running time", "0.1 Min", "0x7014", ""],
    ["U0-21", "AI1 voltage before correction", "0.001 V", "0x7015", ""],
    ["U0-22", "AI2 voltage (V)/current (mA) before correction", "0.01 V/0.01 mA", "0x7016", ""],
    ["U0-23", "AI3 voltage before correction", "0.001 V", "0x7017", ""],
    ["U0-24", "Linear speed", "1 m/Min", "0x7018", ""],
    ["U0-25", "Accumulative power-on time", "1 Min", "0x7019", ""],
    ["U0-26", "Accumulative running time", "0.1 Min", "0x701A", ""],
    ["U0-27", "Pulse input frequency", "1 Hz", "0x701B", ""],
    ["U0-28", "Communication setting value", "0.01%", "0x701C", ""],
    ["U0-29", "Encoder feedback speed", "0.01 Hz", "0x701D", ""],
    ["U0-30", "Main frequency X", "0.01 Hz", "0x701E", ""],
    ["U0-31", "Auxiliary frequency Y", "0.01 Hz", "0x701F", ""],
    ["U0-32", "Viewing any register address value", "1", "0x7020", ""],
    ["U0-33", "Synchronous motor rotor position", "0.1°", "0x7021", ""],
    ["U0-34", "Motor temperature", "1°C", "0x7022", ""],
    ["U0-35", "Target torque", "0.1%", "0x7023", ""],
    ["U0-36", "Resolver position", "1", "0x7024", ""],
    ["U0-37", "Power factor angle", "0.1°", "0x7025", ""],
    ["U0-38", "ABZ position", "1", "0x7026", ""],
    ["U0-39", "Target voltage upon V/F separation", "1 V", "0x7027", ""],
    ["U0-40", "Output voltage upon V/F separation", "1 V", "0x7028", ""],
    ["U0-41", "X state visual display", "1", "0x7029", ""],
    ["U0-42", "DO state visual display", "1", "0x702A", ""],
    ["U0-43", "X function state visual display 1", "1", "0x702B", ""],
    ["U0-44", "X function state visual display 2", "1", "0x702C", ""],
    ["U0-45", "Fault information", "1", "0x702D", ""]
]
# Adding the missing range (0x702E to 0x7039) with "-"
for addr in range(0x702E, 0x703A):
    monitoring_parameters.append(["-", "-", "-", f"0x{addr:04X}", ""])
# Adding the remaining final parameters
monitoring_parameters.extend([
    ["U0-58", "Phase Z counting", "1", "0x703A", ""],
    ["U0-59", "Current set frequency", "0.01%", "0x703B", ""],
    ["U0-60", "Current running frequency", "0.01%", "0x703C", ""],
    ["U0-61", "AC drive running state", "1", "0x703D", ""],
    ["U0-62", "Current fault code", "1", "0x703E", ""],
    ["U0-63", "Sent value of point-point communication", "0.01%", "0x703F", ""],
    ["U0-64", "Received value of point-point communication", "0.01%", "0x7040", ""],
    ["U0-65", "Torque upper limit", "0.1%", "0x7041", ""]
])

# Configure the Modbus RTU client
# Replace '/dev/ttyUSB0' with your actual serial port
client = ModbusSerialClient(
    port='/dev/ttyUSB0',
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=2,
    timeout=1
)
client.connect()

# This is almost always a good thing to do at the beginning of your programs.
# locale.setlocale(locale.LC_ALL, '') Guy fonctionne mieux via ssh et mes clients locales GB certains FR d'autres
#                                     ========================================================================
locale.setlocale(locale.LC_ALL, '')
# You may want to use 'autowidgetsize=True' here (requires pythondialog >= 3.1)
d = Dialog(dialog="dialog")
d.autowidgetsize=True
# Dialog.set_background_title() requires pythondialog 2.13 or later
d.set_background_title("Communication with VFD via ModBus")

# fields used when input data to read (choice '7 read any')
fields = [
    ("Starting address (Hex):", 1, 1, "0xF000", 1, 25, 10, 10, 0),
    ("Words count (Dec) :", 2, 1, "29",     2, 25, 10, 5,  0)
]
fields_2 = [
    ("Address (Hex):", 1, 1, "0x2000", 1, 25, 10, 10, 0),
    ("Value to write (Dec):", 2, 1, "7",     2, 25, 10, 5,  0)
]

def parameters2text(params):
    # Column width definitions
    w_code = 5
    w_name = 27
    w_unit = 10
    w_addr = 8
    w_val = 6

    text = ""  
    # Print only most interesting parameters   \Z4\Zr to change color \Zn to restore normal
    # Modified version to use Dialog.gauge : no screen flickering but only 12 parameters (why?..)
    # Parameters U0-00 ~ 06
    for item in params[:7]:
        text = text + (f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + r"\Z4\Zr" + f"{item[4]:<{w_val}}" + r"\Zn |") + "\n"
    # Parameters U0-14
    for item in params[14:15]:
        text = text + (f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + r"\Z4\Zr" + f"{item[4]:<{w_val}}" + r"\Zn |") + "\n"
    # Parameters U0-25 ~ 26
    for item in params[25:27]:
        text = text + (f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + r"\Z4\Zr" + f"{item[4]:<{w_val}}" + r"\Zn |") + "\n"
    # Parameters U0-37
    for item in params[37:38]:
        text = text + (f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + r"\Z4\Zr" + f"{item[4]:<{w_val}}" + r"\Zn |") + "\n"
    # Parameters U0-59 ~ 62
    # for item in params[59:63]:
        # text = text + (f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              # f"{item[3]:<{w_addr}} | " + r"\Z4\Zr" + f"{item[4]:<{w_val}}" + r"\Zn |") + "\n"
    # Parameters U0-61
    for item in params[61:62]:
        text = text + (f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + r"\Z4\Zr" + f"{item[4]:<{w_val}}" + r"\Zn |") + "\n"

    return(text)

END = False
while END == False:

    code, tag = d.menu("OK, choose in this list:",
                       choices=[("1", "Read 20 data registers"),
                                ("2", "Read motor status"),
                                ("3", "Start motor"),
                                ("4", "Stop motor"),
                                ("5", "Write Frequency set point"),
                                ("6", "Read fault registers"),
                                ("7", "Read any (input address)"),
                                ("8", "Write 1 word / VFD Reset"),
                                ("9", "Monitoring main parameters"),
                                ("0", "Exit")])
    if code == d.OK:
        if tag == '1':
            try:
                result = client.read_holding_registers(address=0x1000, count=20, slave=1)
                if not result.isError():
                    ListToPrint = []
                    for i in range(0, 20):
                        ListToPrint.append(VFDdataList[i] + ' = ' + str(result.registers[i]))
                    TextToPrint = '\n'.join(ListToPrint)
                    d.msgbox(TextToPrint, no_collapse=True)
                else:
                    print(f"Error reading registers: {result}")
                    END = True
            except:
                print("HORROR.. ERROR!!!!!")
                END = True
        if tag == '2':
            try:
                result = client.read_holding_registers(address=0x3000, count=1, slave=1)
                if not result.isError():
                    TextToPrint = ''
                    if result.registers[0] == 1:
                        TextToPrint = 'Motor is running\n'
                    if result.registers[0] == 3:
                        TextToPrint = 'Motor is stopped\n'
                    TextToPrint = TextToPrint + 'Status = ' + str(result.registers[0])
                    d.msgbox(TextToPrint, no_collapse=True)
                else:
                    print(f"Error reading registers: {result}")
                    END = True
            except:
                print("HORROR.. ERROR!!!!!")
                END = True
        if tag == '3':
            if d.yesno("Are you sure you want to start the motor?") == d.OK:
                try:
                    client.write_register(address=0x2000, value=1, slave=1)
                except:
                    print("HORROR.. ERROR!!!!!")
                    END = True
        if tag == '4':
            if d.yesno("Are you sure you want to stop the motor?") == d.OK:
                try:
                    client.write_register(address=0x2000, value=6, slave=1)
                except:
                    print("HORROR.. ERROR!!!!!")
                    END = True
        if tag == '5':
            code, freq = d.inputbox('Input Frequency set point 0~100%')
            if code == 'ok':
                if freq.isdigit() == True:
                    if int(freq) in range(0, 101):
                        freqToWrite = int(freq) * 100 # Value to write to VFD in 0~10000 for 0~100.00%
                        try:
                            client.write_register(address=0x1000, value=freqToWrite, slave=1)
                        except:
                            print("HORROR.. ERROR!!!!!")
                            END = True
                    else:
                        print('Value our of range! Exit!')
                        END = True
                else:
                    print('Entered value is not an integer! Exit!')
                    END = True
        if tag == '6':
            try:
                result = client.read_holding_registers(address=0x8000, count=2, slave=1)
                if not result.isError():
                    TextToPrint = 'VFD fault = ' + str(f"0x{result.registers[0]:04X}")
                    TextToPrint = TextToPrint + '\nCommunication fault = ' 
                    TextToPrint = TextToPrint + str(f"0x{result.registers[1]:04X}")
                    d.msgbox(TextToPrint, no_collapse=True)
                else:
                    print(f"Error reading registers: {result}")
                    END = True
            except:
                print("HORROR.. ERROR!!!!!")
                END = True
        if tag == '7':
            code, tags = d.mixedform(
                "Input the following :",
                fields,
                title="Read any data",
                # height=15,
                # width=50,
                # form_height=4
            )
            if code == 'ok':
                try:
                    addr_val = int(tags[0], 16)
                    count_val = int(tags[1])
                    try:
                        result = client.read_holding_registers(address=addr_val, count=count_val, slave=1)
                        if not result.isError():
                            ListToPrint = []
                            for i in range(0, count_val):
                                ListToPrint.append(str(addr_val+i) + ' ' + str(f"0x{addr_val+i:04X}") + ' = ' + str(result.registers[i]))
                            TextToPrint = '\n'.join(ListToPrint)
                            d.msgbox(TextToPrint, no_collapse=True)                        
                        else:
                            print(f"Error reading registers: {result}")
                            END = True
                    except:
                        print("HORROR.. ERROR!!!!!")
                        END = True
                except ValueError:
                    print('Entered value is not a number! Exit!')
                    END = True
        if tag == '8':
            code, tags = d.mixedform(
                "Writing 7 @0x2000 is a fault reset:",
                fields_2,
                title="Write any 1 word",
            )
            if code == 'ok':
                try:
                    addr_val = int(tags[0], 16)
                    value_val = int(tags[1])
                    try:
                        result = client.write_register(address=addr_val, value=value_val, slave=1)
                        if not result.isError():
                            d.msgbox("DONE", no_collapse=True)
                        else:
                            print(f"Error writing register: {result}")
                            END = True
                    except:
                        print("HORROR.. ERROR!!!!!")
                        END = True
                except ValueError:
                    print('Entered value is not a number! Exit!')
                    END = True
        if tag == '9':
            try:
                result = client.read_holding_registers(address=0x7000, count=66, slave=1)
                if not result.isError():
                    for i in range(66):
                        monitoring_parameters[i][4] = str(result.registers[i])
                    TextToPrint = parameters2text(monitoring_parameters)
                    d.gauge_start(text=TextToPrint, colors=True, no_collapse=True, title="Monitoring - Values are refreshed every 2s - Ctrl-C to stop")
                    try:
                        while True:
                            result = client.read_holding_registers(address=0x7000, count=66, slave=1)
                            if not result.isError():
                                for i in range(66):
                                    monitoring_parameters[i][4] = str(result.registers[i])
                                updated_text = parameters2text(monitoring_parameters)
                                d.gauge_update(percent=0, text=updated_text, update_text=True)
                                time.sleep(2)
                            else:
                                d.gauge_stop()
                                print(f"Error reading registers: {result}")
                                END = True
                                break
                    except KeyboardInterrupt:
                        d.gauge_stop()
                else:
                    print(f"Error reading registers: {result}")
                    END = True
            except:
                print("HORROR.. ERROR!!!!!")
                END = True                    
        if tag == '0':
            END = True
        # Anyway we pass here
    else:
        if code == d.ESC:
            END = True
        if code == d.CANCEL:
            END = True
# Close connection
client.close()
print('\n\nOk Exit. Bye bye!')
print('=================')
