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

hreg_address = 0x3000   # register to start reading
register_qty = 1    # amount of registers to read
slave_addr = 1

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
print("End exit..")
















