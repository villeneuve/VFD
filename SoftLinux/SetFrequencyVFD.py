#! /usr/bin/env python3

# Guy Decembre 2025 -- Gujan
# This program communicate with the CNWeiken WK600 VFD via ModBus

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import sys

# Configure the Modbus RTU client
# Replace '/dev/ttyUSB0' with your actual serial port
client = ModbusSerialClient(
    # port='/dev/ttyUSB0',
    port='/dev/ttyPicoBridge',
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=2,
    timeout=1
)

try:
    # Connect to the Modbus device
    if client.connect():
        print("Connected to Modbus device.")
        # freq = input("Input a value between 0 - 100. It is the frequency set point in % of 50Hz : ")
        freq = "".join(sys.argv[1:])
        try:
            freqToWrite = int(freq) * 100 # Value to write to VFD in 0~10000 for 0~100.00%
            if 0 <= freqToWrite <= 10000:
                try:
                    result = client.write_register(address=0x1000, value=freqToWrite, slave=1)
                    if not result.isError():
                        print(f"DONE! Command successful: {result}")
                    else:
                        print(f"Error writing register: {result}")
                except:
                    print("HORROR.. ERROR!!!!!")
            else:
                print('Value out of range! Exit!')
        except ValueError:
            print('Entered value is not an integer! Exit!')
    else:
        print("Failed to connect to Modbus device.")
except ModbusException as e:
    print(f"Modbus communication error: {e}")

finally:
    # Close the connection
    if client.connect():
        client.close()
        print("Disconnected from Modbus device.")
