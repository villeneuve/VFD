#! /usr/bin/env python3

# Guy Decembre 2025 -- Gujan
# This program communicate with the CNWeiken WK600 VFD via ModBus

from dialog import Dialog
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import locale

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

END = False
while END == False:

    code, tag = d.menu("OK, choose in this list:",
                       choices=[("(1)", "Read 20 data registers"),
                                ("(2)", "Read motor status"),
                                ("(3)", "Start motor"),
                                ("(4)", "Stop motor"),
                                ("(5)", "Write Frequency set point"),
                                ("(6)", "Read fault registers"),
                                ("(7)", "Read any (input address)"),
                                ("(8)", "Write 1 word / VFD Reset"),
                                ("(9)", "Exit")])
    if code == d.OK:
        if tag == '(1)':
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
        if tag == '(2)':
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
        if tag == '(3)':
            if d.yesno("Are you sure you want to start the motor?") == d.OK:
                try:
                    client.write_register(address=0x2000, value=1, slave=1)
                except:
                    print("HORROR.. ERROR!!!!!")
                    END = True
        if tag == '(4)':
            if d.yesno("Are you sure you want to stop the motor?") == d.OK:
                try:
                    client.write_register(address=0x2000, value=6, slave=1)
                except:
                    print("HORROR.. ERROR!!!!!")
                    END = True
        if tag == '(5)':
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
        if tag == '(6)':
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
        if tag == '(7)':
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
        if tag == '(8)':
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
        if tag == '(9)':
            END = True
        # Anyway we pass here
    else:
        if code == d.ESC:
            END = True
        if code == d.CANCEL:
            END = True
# Close connection
client.close()
print('\n\n            Ok Exit. Bye bye!')
print('            =====================')
