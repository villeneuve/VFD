from umodbus.serial import Serial as ModbusRTUMaster
from machine import Pin

# RTU Host/Master setup

# the following definition is for a RP2
#rtu_pins = (Pin(0), Pin(1))     # (TX, RX)
#uart_id = 0
#
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

#coil_status = host.read_coils(slave_addr=10, starting_addr=123, coil_qty=1)
#print('Status of coil 123: {}'.format(coil_status))

hreg_address = 0x1000   # register to start reading
register_qty = 20    # amount of registers to read
slave_addr = 1

register_value = host.read_holding_registers(
    slave_addr=slave_addr,
    starting_addr=hreg_address,
    register_qty=register_qty,
    signed=False)

print('Status of HREG {}: {}'.format(hreg_address, register_value))
