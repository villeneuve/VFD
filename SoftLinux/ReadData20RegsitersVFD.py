#! /usr/bin/env python3

# Guy Decembre 2025 -- Gujan
# This program communicate with the CNWeiken WK600 VFD via ModBus

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

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

client.connect()

try:
    result = client.read_holding_registers(address=0x1000, count=20, slave=1)
    if not result.isError():
        ListToPrint = []
        for i in range(0, 20):
            ListToPrint.append(VFDdataList[i] + ' = ' + str(result.registers[i]))
        TextToPrint = '\n'.join(ListToPrint)
        print(TextToPrint)
        print(f"DONE! Command successful: {result}")
    else:
        print(f"Error reading registers: {result}")
except:
    print("HORROR.. ERROR!!!!!")

client.close()
print("End exit..")
