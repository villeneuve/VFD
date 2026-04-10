from umodbus.serial import Serial as ModbusRTUMaster
from machine import Pin, UART
from time import sleep, sleep_ms
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

class VFD:
    def __init__(self, host):
        self.host = host
        # print('Done')

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
        
    def OpenContactor(self):
        contactor.off()

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
        return disjoncteur.value()  # contact open on fault => input = 1

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
