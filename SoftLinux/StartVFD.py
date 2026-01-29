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
    result = client.write_register(address=0x2000, value=1, slave=1)
    if not result.isError():
        print(f"DONE! Command successful: {result}")
    else:
        print(f"Error writing register: {result}")
except:
    print("HORROR.. ERROR!!!!!")

client.close()
print("End exit..")
