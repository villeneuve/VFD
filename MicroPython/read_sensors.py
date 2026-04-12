from machine import Pin
import onewire
import time
import ds18x20
import asyncio

ow = onewire.OneWire(Pin(9))
ow.scan()
ow.reset()
ds = ds18x20.DS18X20(ow)

class SENSORS_GROUP:
    def __init__(self):
        self.sensor_id          = []     #  exemple: rom id 
        self.sensor_name        = []     #  exemple: motor temperature
        self.sensor_value       = []     #  exemple: "25.75"
        self.last_update        = 0      #  last measure timestamp
        self.flag_ready_to_read = False  #  True after sensor reading
                                         #  reset in main after getting value

sensors = SENSORS_GROUP()

sensors.sensor_id = ds.scan()
for i, id in enumerate(sensors.sensor_id):
    sensors.sensor_value.append("?")
    sensors.sensor_name.append("Temperature test " + str(i))


# function asyncio to be used with a main asyncio as well (returns temperature)
async def get_sensors_value():
    ds.convert_temp()
    await asyncio.sleep_ms(750)
    for i, id in enumerate(sensors.sensor_id):
        sensors.sensor_value[i] = str(ds.read_temp(id))
    sensors.flag_ready_to_read = True
    sensors.last_update = time.time()


# Non asyncio function (returns rom + temperature)
def read_temperature():
    ds.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        print(rom, ds.read_temp(rom))
    # To be used when needed to get returned values
    # return tuple(ds.read_temp(rom) for rom in roms)


# Get / Set DS18B20 temperature resolution (9~12 bits)
def resolution(rom, bits=None):
    config = bytearray(3)
    if bits is not None and 9 <= bits <= 12:
        config[2] = ((bits - 9) << 5) | 0x1f
        ds.write_scratch(rom, config)
        return bits
    else:
        data = ds.read_scratch(rom)
        return ((data[4] >> 5) & 0x03) + 9
