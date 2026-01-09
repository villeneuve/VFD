#! /usr/bin/env python3

# Guy January 2026 -- Gujan
# This program communicates with the CNWeiken WK600 VFD via ModBus
# It reads Group U0 Monitoring parameters and displays them in a formatted table.

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

def display_parameters(params):
    # Column width definitions
    w_code = 5
    w_name = 46
    w_unit = 15
    w_addr = 8
    w_val = 6

    # Table Header with borders
    header = (f"| {'Code':<{w_code}} | {'Parameter Name':<{w_name}} | "
              f"{'Min. Unit':<{w_unit}} | {'Address':<{w_addr}} | {'Value':<{w_val}} |")
    
    separator = "-" * len(header)
    
    print(separator)
    print(header)
    print(separator)

    # Display each row without extra horizontal separators
    for item in params:
        print(f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | {item[4]:<{w_val}} |")
    
    # Final footer line
    print(separator)

if __name__ == "__main__":
    try:
        start_address = 0x7000
        register_count = 66 # Total registers from 0x7000 to 0x7041
        
        # Modbus reading
        result = client.read_holding_registers(address=start_address, count=register_count, slave=1)
        
        if not result.isError():
            # Update values in the list
            for i in range(register_count):
                monitoring_parameters[i][4] = str(result.registers[i])
            print(f"DONE! Command successful: {result}")
        else:
            print(f"Modbus Error: {result}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    
    # Final display
    display_parameters(monitoring_parameters)
    
    client.close()
    print("Program finished.")
