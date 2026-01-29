from umodbus.serial import Serial as ModbusRTUMaster
from machine import Pin
from time import sleep

rtu_pins = (Pin(4), Pin(5))     # (TX, RX)
uart_id = 1

host = ModbusRTUMaster(
    pins=rtu_pins,          # given as tuple (TX, RX)
    # baudrate=9600,        # optional, default 9600
    # data_bits=8,          # optional, default 8
    stop_bits=2,          # optional, default 1
    # parity=None,          # optional, default None
    # ctrl_pin=12,          # optional, control DE/RE
    uart_id=uart_id         # optional, default 1, see port specific documentation
)

slave_addr = 1

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
    ["U0-33", "Synchronous motor rotor position", "0.1 degree", "0x7021", ""],
    ["U0-34", "Motor temperature", "1 degree C.", "0x7022", ""],
    ["U0-35", "Target torque", "0.1%", "0x7023", ""],
    ["U0-36", "Resolver position", "1", "0x7024", ""],
    ["U0-37", "Power factor angle", "0.1 degree", "0x7025", ""],
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

def display15parameters(params):
    # Column width definitions
    w_code = 5
    w_name = 27
    w_unit = 10
    w_addr = 8
    w_val = 6

    # Table Header with borders
    header = (f"| {'Code':<{w_code}} | {'Parameter Name':<{w_name}} | " 
              f"{'Min. Unit':<{w_unit}} | {'Address':<{w_addr}} | {'Value':<{w_val}} |")
    
    separator = "-" * len(header)

    print(separator + '\n' + header + '\n' + separator)
    
    # Print only most interesting parameters   
    # Parameters U0-00 ~ 06
    for item in params[:7]:
        print( f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + f"{item[4]:<{w_val}} |")
    # Parameters U0-14
    for item in params[14:15]:
        print( f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + f"{item[4]:<{w_val}} |")
    # Parameters U0-25 ~ 26
    for item in params[25:27]:
        print( f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + f"{item[4]:<{w_val}} |")
    # Parameters U0-37
    for item in params[37:38]:
        print( f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + f"{item[4]:<{w_val}} |")
    # Parameters U0-59 ~ 62
    for item in params[59:63]:
        print( f"| {item[0]:<{w_code}} | {item[1]:<{w_name}} | {item[2]:<{w_unit}} | "
              f"{item[3]:<{w_addr}} | " + f"{item[4]:<{w_val}} |")
    
    # Final footer line
    print(separator + "\n")

def wrap_text(text, width):
    """Wraps text into a list of strings based on the given width."""
    if not text or text == "-": return [text]
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        if sum(len(w) + 1 for w in current_line) + len(word) <= width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def display66parameters(params):
    # Column width definitions
    w_code = 5
    w_name = 35
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

    for item in params:
        wrapped_name = wrap_text(item[1], w_name)
        wrapped_unit = wrap_text(item[2], w_unit)
        
        max_lines = max(len(wrapped_name), len(wrapped_unit))
        
        for i in range(max_lines):
            name_line = wrapped_name[i] if i < len(wrapped_name) else ""
            unit_line = wrapped_unit[i] if i < len(wrapped_unit) else ""
            
            if i == 0:
                print(f"| {item[0]:<{w_code}} | {name_line:<{w_name}} | {unit_line:<{w_unit}} | "
                      f"{item[3]:<{w_addr}} | {item[4]:<{w_val}} |")
            else:
                print(f"| {'':<{w_code}} | {name_line:<{w_name}} | {unit_line:<{w_unit}} | "
                      f"{'':<{w_addr}} | {'':<{w_val}} |")
    print(separator)

def Read20Registers():
    hreg_address = 0x1000   # register to start reading
    register_qty = 20    # amount of registers to read 
    try:
        register_value = host.read_holding_registers(
            slave_addr=slave_addr,
            starting_addr=hreg_address,
            register_qty=register_qty,
            signed=False)
        ListToPrint = []
        for i in range(0, 20):
            ListToPrint.append(VFDdataList[i] + ' = ' + str(register_value[i]))
        TextToPrint = '\n'.join(ListToPrint)
        print(TextToPrint)
    except Exception as e: print(repr(e))

def MotorStatus():
    hreg_address = 0x3000   # register to start reading
    register_qty = 1    # amount of registers to read    
    try:
        register_value = host.read_holding_registers(
            slave_addr=slave_addr,
            starting_addr=hreg_address,
            register_qty=register_qty,
            signed=False)
        TextToPrint = 'Status = ' + str(register_value[0])
        if register_value[0] == 1:
            TextToPrint = TextToPrint + ' Motor is running'
        if register_value[0] == 3:
            TextToPrint = TextToPrint + ' Motor is stopped'
        print(TextToPrint)
    except Exception as e: print(repr(e))

def StartMotor():
    hreg_address = 0x2000  
    new_hreg_val = 1    
    try:
        operation_status = host.write_single_register(
            slave_addr=slave_addr,
            register_address=hreg_address,
            register_value=new_hreg_val,
            signed=False)
        print('Result :', operation_status)
    except Exception as e: print(repr(e))

def StopMotor():
    hreg_address = 0x2000  
    new_hreg_val = 6    
    try:
        operation_status = host.write_single_register(
            slave_addr=slave_addr,
            register_address=hreg_address,
            register_value=new_hreg_val,
            signed=False)
        print('Result :', operation_status)
    except Exception as e: print(repr(e))

def SetFreqMax():
    SetFreq(10000)
    
def SetFreq(f):
    r = False
    if isinstance(f, int):
        if 0 <= f <= 10000:
            hreg_address = 0x1000  
            new_hreg_val = f    
            try:
                operation_status = host.write_single_register(
                    slave_addr=slave_addr,
                    register_address=hreg_address,
                    register_value=new_hreg_val,
                    signed=False)
                print('Result :', operation_status)
                r = operation_status
            except Exception as e: print(repr(e))
            #print("End exit..")
        else:
            print('Value out of range! Must be in 0..10000 = 0%..100.00%')
    else:
        print('Entered value is not an integer! Exit!')
    return(r)

def ReadFaultRegisters():
    hreg_address = 0x8000   # register to start reading
    register_qty = 2    # amount of registers to read    
    try:
        register_value = host.read_holding_registers(
            slave_addr=slave_addr,
            starting_addr=hreg_address,
            register_qty=register_qty,
            signed=False)
        TextToPrint = 'VFD fault = ' + str(f"0x{register_value[0]:04X}")
        TextToPrint = TextToPrint + '\nCommunication fault = ' 
        TextToPrint = TextToPrint + str(f"0x{register_value[1]:04X}")
        print(TextToPrint)
    except Exception as e: print(repr(e))

def ReadAnyRegister(addr=0x7000, count=20):
    hreg_address = addr     # register to start reading
    register_qty = count    # amount of registers to read    
    try:
        register_value = host.read_holding_registers(
            slave_addr=slave_addr,
            starting_addr=hreg_address,
            register_qty=register_qty,
            signed=False)
        ListToPrint = []
        for i in range(0, count):
            ListToPrint.append(str(addr+i) + ' ' + str(f"0x{addr+i:04X}") + ' = ' + str(register_value[i]))
        TextToPrint = '\n'.join(ListToPrint)
        print(TextToPrint)
    except Exception as e: print(repr(e))

def Write1Word(addr=0x2000, value=7):
    hreg_address = addr  
    new_hreg_val = value    
    try:
        operation_status = host.write_single_register(
            slave_addr=slave_addr,
            register_address=hreg_address,
            register_value=new_hreg_val,
            signed=False)
        print('Result :', operation_status)
    except Exception as e: print(repr(e))

def Monitoring(refreshrate=2, count=2, extended=False):
    hreg_address = 0x7000     # register to start reading
    register_qty = 66    # amount of registers to read    
    try:
        while True:
            register_value = host.read_holding_registers(
                slave_addr=slave_addr,
                starting_addr=hreg_address,
                register_qty=register_qty,
                signed=False)
            for i in range(66):
                monitoring_parameters[i][4] = str(register_value[i])
            if extended:
                display66parameters(monitoring_parameters)
            else:
                display15parameters(monitoring_parameters)
            if count == 1: break
            if count > 0:           # if count = 0 loop forever until Ctrl-C
                count = count -1
            sleep(refreshrate)
    except Exception as e: print(repr(e))

def Menu():
    End = False
    while End == False:
        print('')
        print('Type 1 : To read the first 20 registers')
        print('Type 2 : For motor status')
        print('Type 3 : To start motor')
        print('Type 4 : To stop  motor')
        print('Type 5 : To define frequency setpoint')
        print('Type 6 : To read the fault registers')
        print('Type 7 : To read any registers')
        print('Type 8 : To write 1 register')
        print('Type 9 : To monitor the main parameters')
        print('Type 0 : To exit')
        xx = input('Your choice : ')
        x = int(xx)
        if x == 0:
            break
        if x == 1:
            print('')
            Read20Registers()
        if x == 2:
            print('')
            MotorStatus()
        if x == 3:
            print('')
            StartMotor()
        if x == 4:
            print('')
            StopMotor()
        if x == 5:
            f = int(input('Frequency in range 0~10000 = 0~100.00% = 0~50Hz (default = 10000 = 50Hz) :') or "10000")
            SetFreq(f)
        if x == 6:
            print('')
            ReadFaultRegisters()
        if x == 7:
            a = int(input('Address (default = 0x7000) Hex: ') or "0x7000",16)
            b = int(input('Count  (default = 20       Dec: ') or "20")
            ReadAnyRegister(a, b)
        if x == 8:
            a = int(input('Address (default = 0x2000)          Hex: ') or "0x2000",16)
            b = int(input('Value  (default = 7 = Fault reset)  Dec: ') or "7")
            Write1Word(a, b)
        if x == 9:
            a = int(input('Refresh rate (seconds - default = 2)  : ') or "2")
            b = int(input('Cycles qt\'y (0=forever Ctrl-C to stop) (default = 2) : ') or "2")
            c = bool(int(input('extended (66 parameters) or not (15 main parameters) (default = 0  = False)  0 or 1 ? : ') or "0"))
            print('')
            Monitoring(a, b, c)

if SetFreq(10000):
    # Writing frequency setpoint is a way to test if we can talk with the vfd
    # And also to avoid to start the motor with setpoint=0 because this will freeze the pico!!!
    print('\nVFD is online :-) I\'ve set frequency setpoint at 10000 = 100.00% = 50Hz. Change it if you like')
    print('To read the first 20 registers, type : vfd.Read20Registers()')
    print('For motor status, type : vfd.MotorStatus()')
    print('To start motor, type :   vfd.StartMotor()')
    print('To stop  motor, type :   vfd.StopMotor()')
    print('To define frequency setpoint, type : vfd.SetFreq(x) with x in range 0..10000 = 0..100.00% of 50Hz')
    print('To read the fault registers, type : vfd.ReadFaultRegisters()')
    print('To read any registers, type : vfd.ReadAnyRegister(address, count) default to 0x7000, 20 if not given')
    print('To write 1 register, type : vfd.Write1Word(address, value) default to 0x2000, 7 if not given (fault reset)')
    print('To monitor the main parameters, type : vfd.Monitoring(refresh, count, extended)')
    print('         defaults: refresh=2s cycles=2 (0=forever Ctrl-C to stop extended=False')
    print('         extended lists 66 parameters not extended the 15 mains')
    print('To have interactive menu type, vfd.Menu()')
else:
    print('Something went wrong.. Exit')
