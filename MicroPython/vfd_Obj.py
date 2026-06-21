from umodbus.serial import Serial as ModbusRTUMaster
from machine import Pin, UART, PWM
from time import sleep, sleep_ms
from read_sensors import sensors
import _thread

bus_lock = _thread.allocate_lock()  # global lock
led = Pin("LED", Pin.OUT)

rtu_pins = (Pin(4), Pin(5))     # (TX, RX)
uart_id = 1

host = ModbusRTUMaster(
    pins=rtu_pins,      # given as tuple (TX, RX)
    # baudrate=9600,    # optional, default 9600
    # data_bits=8,      # optional, default 8
    stop_bits=2,        # optional, default 1
    # parity=None,      # optional, default None
    # ctrl_pin=12,      # optional, control DE/RE
    uart_id=uart_id     # optional, default 1, see port specific documentation
)

slave_addr = 1

contactor   = Pin(7, Pin.OUT)
disjoncteur = Pin(8, Pin.IN, Pin.PULL_UP)
fan = PWM(Pin(10), freq=5000, duty_u16=0)

class VFD:
    
    def __init__(self, host):
        self.host = host
        self.vfd_data = [
        # Here are the text and addresses of the 11 vfd monitoring 
        # parameters we are collecting. 
        # In order to communicate them on request.
        # this is a list of 11 text strings.
        # ["U0-00", "Running frequency (Hz)", "0.01 Hz", "0x7000", ""],
        # ["U0-01", "Set frequency (Hz)", "0.01 Hz", "0x7001", ""],
        # ["U0-02", "Bus voltage", "0.1 V", "0x7002", ""],
        # ["U0-03", "Output voltage", "1 V", "0x7003", ""],
        # ["U0-04", "Output current", "0.01 A", "0x7004", ""],
        # ["U0-05", "Output power", "0.1 kW", "0x7005", ""],
        # ["U0-06", "Output torque", "0.1%", "0x7006", ""]
        
        # ["U0-14", "Load speed", "1", "0x700E", ""],
        
        # ["U0-19", "Feedback speed", "0.01 Hz", "0x7013", ""],
        
        # ["U0-25", "Accumulative power-on time", "1 Min", "0x7019", ""],
        # ["U0-26", "Accumulative running time", "0.1 Min", "0x701A", ""]
        #
        # in 12th position (i=11)  vfd temperature is added
        # in 13th position (i=12)  motor_status is added
        #
        "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?"
        ]
        self.all_data = [
        # first parameter is vfd_status, followed by the 13 parameters of
        # vfd_data, followed by: contactor_status, disjoncteur (circuit beaker
        # in french) state, fan_speed, temperatures sensors measure + errors
        # counter: 3x3=9 parameters + total count, pico voltage VSYS.
        ]
        self.fan_temp_thres = [22, 26, 28, 30, 33, 35]  # temperature threshold
                                                        # for fan speed control

    def MotorStatus(self):
        with bus_lock:
            try:
                register_value = self.host.read_holding_registers(
                    slave_addr=slave_addr,
                    starting_addr=0x3000,
                    register_qty=1,
                    signed=False)
                return register_value[0]
            except Exception as e:
                print(repr(e))

    def StartMotor(self):
        with bus_lock:
            hreg_address = 0x2000
            new_hreg_val = 1
            try:
                operation_status = self.host.write_single_register(
                    slave_addr=slave_addr,
                    register_address=hreg_address,
                    register_value=new_hreg_val,
                    signed=False)
                return operation_status
            except Exception as e:
                print(repr(e))

    def StopMotor(self):
        with bus_lock:
            hreg_address = 0x2000
            new_hreg_val = 6
            try:
                operation_status = self.host.write_single_register(
                    slave_addr=slave_addr,
                    register_address=hreg_address,
                    register_value=new_hreg_val,
                    signed=False)
                return operation_status
            except Exception as e:
                print(repr(e))

    def SetFreqMax(self):
        self.SetFreq(10000)

    def SetFreq(self, f):
        r = False
        if isinstance(f, int):
            if 0 <= f <= 10000:
                with bus_lock:
                    hreg_address = 0x1000
                    new_hreg_val = f
                    try:
                        operation_status = self.host.write_single_register(
                            slave_addr=slave_addr,
                            register_address=hreg_address,
                            register_value=new_hreg_val,
                            signed=False)
                        r = operation_status
                    except Exception as e:
                        print(repr(e))
            else:
                print('Value out of range! Must be in 0..10000 = 0%..100.00%')
        else:
            print('Entered value is not an integer! Exit!')
        return r

    def ReadFaultRegisters(self):
        with bus_lock:
            hreg_address = 0x8000   # register to start reading
            register_qty = 2    # amount of registers to read
            try:
                register_value = self.host.read_holding_registers(
                    slave_addr=slave_addr,
                    starting_addr=hreg_address,
                    register_qty=register_qty,
                    signed=False)
                TextToPrint = 'VFD fault = ' + \
                              str(f"0x{register_value[0]:04X}")
                TextToPrint = TextToPrint + '\nCommunication fault = '
                TextToPrint = TextToPrint + str(f"0x{register_value[1]:04X}")
                return TextToPrint
            except Exception as e:
                print(repr(e))

    def ReadAnyRegister(self, addr=0x7000, count=20):
        with bus_lock:
            hreg_address = addr     # register to start reading
            register_qty = count    # amount of registers to read
            try:
                register_value = self.host.read_holding_registers(
                    slave_addr=slave_addr,
                    starting_addr=hreg_address,
                    register_qty=register_qty,
                    signed=False)
                ListToPrint = []
                for i in range(0, count):
                    # ListToPrint.append(str(addr+i) + ' ' + \
                    # str(f"0x{addr+i:04X}") + ' = ' + str(register_value[i]))
                    ListToPrint.append(str(register_value[i]))
                TextToPrint = '\n'.join(ListToPrint)
                return TextToPrint
            except Exception as e:
                print(repr(e))

    def Write1Word(self, addr=0x2000, value=7):
        with bus_lock:
            hreg_address = addr
            new_hreg_val = value
            try:
                operation_status = self.host.write_single_register(
                    slave_addr=slave_addr,
                    register_address=hreg_address,
                    register_value=new_hreg_val,
                    signed=False)
                return operation_status
            except Exception as e:
                print(repr(e))

    def CloseContactor(self):
        contactor.on()
        # fan.duty_u16(32768)  # set fan speed 50%
        
    def OpenContactor(self):
        contactor.off()
        # fan.duty_u16(0)  # stop fan
        
    def FanControl(self):
        # we have 6 fan speed : 0 ~ 5 = i in loop hereunder
        # fan duty = 13000 * i = 0 ~ 65000
        # we select the speed according tempertures in fan_temp_thres
        # to avoid frequent fan speed change we don't call this too often
        if self.isonline:
            try:
                for i, val in enumerate(self.fan_temp_thres):
                    if int(self.vfd_data[11]) < val:
                        break
                fan.duty_u16(i * 13000)
            except Exception as e:  
                # An error will happen seldom, only when vfd not yet offline 
                # and vfd temperature (vfd_data[11]) is '?'
                print('Err. in FanControl:', repr(e)) 
        else:
            fan.duty_u16(0)
        print("Fan control. VFD Temp:", self.vfd_data[11], \
        "Fan speed:", fan.duty_u16())
        
    def GetVfdData(self):
        if self.isonline:
            try:
                s = self.ReadAnyRegister(addr=0x7000, count=7)  
                # s = string we convert to list (reverse of
                # what is done in ReadAnyRegister!!!)
                self.vfd_data = s.split('\n')
                s = self.ReadAnyRegister(addr=0x700E, count=1) 
                self.vfd_data.append(s)
                s = self.ReadAnyRegister(addr=0x7013, count=1) 
                self.vfd_data.append(s)
                s = self.ReadAnyRegister(addr=0x7019, count=2) 
                ss = s.split('\n')
                self.vfd_data.append(ss[0])
                self.vfd_data.append(ss[1])
                # Now let's get vfd temperature
                s = self.ReadAnyRegister(addr=0xF707, count=1)
                self.vfd_data.append(s)
                # now let's add motor status
                self.vfd_data.append(str(self.MotorStatus()))
            except Exception as e:            # debug 
                print(repr(e))
        else:
            self.vfd_data = [
            "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?"]
            
    def GetAllData(self):
        if self.isonline:
            self.all_data = ["online"]
        else:
            self.all_data = ["offline"]
        self.GetVfdData()
        self.all_data.extend(self.vfd_data)
        self.all_data.append(str(self.contactor_status))
        self.all_data.append(str(disjoncteur.value()))  # 0:fault 1:ok
        self.all_data.append(str(fan.duty_u16()))
        for i, id in enumerate(sensors.sensor_id):
            self.all_data.append(sensors.sensor_value[i])  # already a string
            self.all_data.append(str(sensors.sensor_crc_err[i]))
            self.all_data.append(str(sensors.sensor_other_err[i]))
        self.all_data.append(str(sensors.count))
        
    @property
    def isonline(self):
        # if self.MotorStatus() != None:   corrigé par pycodestyle PEP-8 TBC
        if self.MotorStatus() is not None:
            return True
        else:
            return False

    @property
    def frequency_measured(self):
        return self.ReadAnyRegister(addr=0x1001, count=1)

    @property
    def frequency_setpoint(self):
        return self.ReadAnyRegister(addr=0x1000, count=1)

    @frequency_setpoint.setter
    def frequency_setpoint(self, value):
        # return True-False but useless because assignment isn't an expression
        return self.SetFreq(value)
        
    @property
    def contactor_status(self):
        return contactor.value()

    @property
    def disj_status(self):
        return not disjoncteur.value()  # contact open on fault => input = 0

# 1. Configuration de l'UART0 pour le PC Linux (GP0=TX, GP1=RX)
pc_uart = UART(0, baudrate=9600, stop=2, tx=Pin(0), rx=Pin(1), timeout=10)


def bridge_loop():
    global host
    vfd_uart = host._uart
    print("[Bridge] Gateway UART0 (PC) <-> UART1 (VFD) enabled with lock.")

    while True:
        try:
            if pc_uart.any():
                led.on()  # led on when pc is talking
                with bus_lock:
                    data_pc = pc_uart.read()
                    if data_pc:
                        vfd_uart.write(data_pc)
                        # On attend un peu la réponse
                        # pour que le PC la récupère
                        # sans que le REPL ne puisse interférer entre-temps
                        sleep_ms(100)
                        if vfd_uart.any():
                            data_vfd = vfd_uart.read()
                            if data_vfd:
                                pc_uart.write(data_vfd)
                led.off()
        except Exception:
            pass
        sleep_ms(5)


# Lancement du thread si l'initialisation précédente a réussi
if 'host' in globals():
    _thread.start_new_thread(bridge_loop, ())
print()  # just to get back to REPL prompt
