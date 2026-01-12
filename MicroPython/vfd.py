from umodbus.serial import Serial as ModbusRTUMaster
from machine import Pin

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
    #print("End exit..")

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
        print(TextToPrint + '  DONE! Command successful')
    except Exception as e: print(repr(e))
    #print("End exit..")

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
    #print("End exit..")

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
    #print("End exit..")

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
    #print("End exit..")

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
    #print("End exit..")

if SetFreq(10000):
    # Writing frequency setpoint is a way to test if we can talk with the vfd
    # And also to avoid to start the motor with setpoint=0 because this will freeze the pico!!!
    print('\nVFD is online :-) I\'ve set frequency setpoint at 10000 = 100.00% = 50Hz. Change it if you like')
    print('To read the first 20 registers, type : vfd.Read20Registers()')
    print('For motor status, type : vfd.MotorStatus()')
    print('To start motor, type :   vfd.StartMotor()')
    print('To stop  motor, type :   vfd.StopMotor()')
    print('To define frequency setpoint type : vfd.SetFreq(x) with x in range 0..10000 = 0..100.00% of 50Hz')
    print('To read the fault registers, type : vfd.ReadFaultRegisters()')
    print('To read any registers, type : vfd.ReadAnyRegister(address, count) default to 0x7000, 20 if not given')
    
    print('----')
else:
    print('Something went wrong.. Exit')












