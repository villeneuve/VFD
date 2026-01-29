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
addr  = input("Starting address (Hex) : ")
count = input("Words count (Dec) : ")

try:
    addr_val = int(addr, 16)
    count_val = int(count)
    try:
        result = client.read_holding_registers(address=addr_val, count=count_val, slave=1)
        if not result.isError():
            ListToPrint = []
            for i in range(0, count_val):
                ListToPrint.append(str(addr_val+i) + ' ' + str(f"0x{addr_val+i:04X}") + ' = ' + str(result.registers[i]))
            TextToPrint = '\n'.join(ListToPrint)
            print(TextToPrint)          
            print(f"DONE! Command successful: {result}")              
        else:
            print(f"Error reading registers: {result}")
    except:
        print("HORROR.. ERROR!!!!!")
except ValueError:
    print('Entered value is not valid! Exit!')

client.close()
print("End exit..")
