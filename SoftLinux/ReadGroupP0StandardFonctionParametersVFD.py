#! /usr/bin/env python3

# Guy December 2025 -- Gujan
# This program communicates with the CNWeiken WK600 VFD via ModBus
# It reads Group P0 parameters and displays them in a formatted table.

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

# Configure the Modbus RTU client
client = ModbusSerialClient(
    port='/dev/ttyUSB0',
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=2,
    timeout=1
)

client.connect()

# Main parameter list with 2 reserved empty fields at the end ("Address" and "Value")
# Format: [Code, Name, Range, Default, Prop, Address, Value]
motor_parameters = [
    ["P0-00", "G/P type display", "1: G type 2: P type", "Model dependent", "●", "", ""],
    ["P0-01", "Motor 1 control mode", "0: SVC 1: FVC 2: V/F", "0", "★", "", ""],
    ["P0-02", "Command source selection", "0: Panel 1: Terminal 2: Comm", "0", "☆", "", ""],
    ["P0-03", "Main frequency source X", "0: Digital (non-ret) 1: Digital (ret) 2: AI1...", "0", "★", "", ""],
    ["P0-04", "Auxiliary frequency source Y", "The same as P0-03", "0", "★", "", ""],
    ["P0-05", "Range of Y for X and Y", "0: Relative to max freq 1: Relative to main X", "0", "☆", "", ""],
    ["P0-06", "Range of Y for X and Y", "0%–150%", "100%", "☆", "", ""],
    ["P0-07", "Frequency source selection", "Unit: source; Ten: relationship", "0", "☆", "", ""],
    ["P0-08", "Preset frequency", "0.00 to maximum frequency", "50.00 Hz", "☆", "", ""],
    ["P0-09", "Rotation direction", "0: Same direction 1: Reverse direction", "0", "☆", "", ""],
    ["P0-10", "Maximum frequency", "50.00–500.00 Hz", "50.00 Hz", "★", "", ""],
    ["P0-11", "Source of freq upper limit", "0: P0-12 1: AI1 2: AI2 3: AI3 4: Pulse 5: Comm", "0", "★", "", ""],
    ["P0-12", "Frequency upper limit", "Frequency lower limit to maximum frequency", "50.00 Hz", "☆", "", ""],
    ["P0-13", "Freq upper limit offset", "0.00 Hz to maximum frequency", "0.00 Hz", "☆", "", ""],
    ["P0-14", "Frequency lower limit", "0.00 Hz to frequency upper limit", "0.00 Hz", "☆", "", ""],
    ["P0-15", "Carrier frequency", "0.5–16.0 kHz", "Model dependent", "☆", "", ""],
    ["P0-16", "Carrier freq adj temp", "0: No 1: Yes", "1", "☆", "", ""],
    ["P0-17", "Acceleration time 1", "0.00–650.00s / 0.0–6500.0s / 0–65000s", "Model dependent", "☆", "", ""],
    ["P0-18", "Deceleration time 1", "0.00–650.00s / 0.0–6500.0s / 0–65000s", "Model dependent", "☆", "", ""],
    ["P0-19", "Accel/Decel time unit", "0: 1s 1: 0.1s 2: 0.01s", "1", "★", "", ""],
    ["P0-20", "-", "-", "-", "-", "", ""],
    ["P0-21", "Freq offset aux source", "0.00 Hz to maximum frequency", "0.00 Hz", "☆", "", ""],
    ["P0-22", "Freq reference resolution", "1: 0.1 Hz 2: 0.01 Hz", "2", "★", "", ""],
    ["P0-23", "Retentive of digital freq", "0: Not retentive 1: Retentive", "2", "☆", "", ""],
    ["P0-24", "Motor parameter group", "0: Group 1 1: Group 2 2: Group 3 3: Group 4", "0", "★", "", ""],
    ["P0-25", "Accel/Decel ref frequency", "0: Max frequency 1: Set frequency 2: 100 Hz", "0", "★", "", ""],
    ["P0-26", "UP/DOWN reference", "0: Running frequency 1: Set frequency", "0", "★", "", ""],
    ["P0-27", "Binding command source", "Unit: Panel; Ten: Term; Hundred: Comm; Thou: Auto", "0000", "☆", "", ""],
    ["P0-28", "Serial comm protocol", "0: Modbus 1: Profibus-DP 2: CANopen", "0", "☆", "", ""]
]

def display_parameters(params):
    # Updated column width definitions
    w_code = 5
    w_name = 28
    w_range = 50
    w_def = 15
    w_prop = 1
    w_addr = 7
    w_val = 5

    # Table Header with borders and renamed Property column to 'P'
    header = (f"| {'Code':<{w_code}} | {'Parameter Name':<{w_name}} | "
              f"{'Setting Range':<{w_range}} | {'Default':<{w_def}} | "
              f"{'P':<{w_prop}} | {'Address':<{w_addr}} | {'Value':<{w_val}} |")
    
    separator = "-" * len(header)
    
    print(separator)
    print(header)
    print(separator)

    # Display each row
    for item in params:
        # Truncation helper function
        trunc = lambda s, w: (str(s)[:w-3] + '...') if len(str(s)) > w else str(s)
        
        d_name = trunc(item[1], w_name)
        d_range = trunc(item[2], w_range)
        
        print(f"| {item[0]:<{w_code}} | {d_name:<{w_name}} | {d_range:<{w_range}} | "
              f"{item[3]:<{w_def}} | {item[4]:<{w_prop}} | {item[5]:<{w_addr}} | {item[6]:<{w_val}} |")
    
    # Final footer line
    print(separator)

if __name__ == "__main__":
    try:
        start_address = int("F000", 16)
        register_count = len(motor_parameters)
        
        # Reading registers from VFD
        result = client.read_holding_registers(address=start_address, count=register_count, slave=1)
        
        if not result.isError():
            # Fill the list with Modbus data
            for i in range(0, register_count):
                motor_parameters[i][5] = f"0x{start_address + i:04X}"
                motor_parameters[i][6] = str(result.registers[i])
            
            print(f"DONE! Command successful: {result}")
        else:
            print(f"Modbus Error: {result}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    
    # Final display
    display_parameters(motor_parameters)
    
    client.close()
    print("Program finished.")
