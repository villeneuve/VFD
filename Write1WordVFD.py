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

print("Careful! I don't check..")
print("Writing 7 @0x2000 is a fault reset:")
addr  = input("Address where to write (Hex) : ")
val = input("Value to write (Dec) : ")

try:
    addr_val = int(addr, 16)
    value_val = int(val)
    print(addr_val,value_val)
    try:
        result = client.write_register(address=addr_val, value=value_val, slave=1)
        if not result.isError():
            print("OK!")
            print(f"DONE! Command successful: {result}")
        else:
            print(f"Error writing register: {result}")
    except:
        print("HORROR.. ERROR!!!!!")
except ValueError:
    print('Entered value is not valid! Exit!')

client.close()
print("End exit..")
