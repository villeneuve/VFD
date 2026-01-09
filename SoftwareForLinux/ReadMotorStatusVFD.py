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

client.connect()
  
try:
    result = client.read_holding_registers(address=0x3000, count=1, slave=1)
    if not result.isError():
        TextToPrint = ''
        if result.registers[0] == 1:
            TextToPrint = 'Motor is running\n'
        if result.registers[0] == 3:
            TextToPrint = 'Motor is stopped\n'
        TextToPrint = TextToPrint + 'Status = ' + str(result.registers[0])
        print(TextToPrint)
        print(f"DONE! Command successful: {result}")
    else:
        print(f"Error reading registers: {result}")
except:
    print("HORROR.. ERROR!!!!!")
    
client.close()
print("End exit..")
