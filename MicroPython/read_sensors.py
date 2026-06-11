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
        self.sensor_crc_err     = []     #  crc errors counter by sensor
        self.sensor_other_err   = []     #  other errors counter by sensor
        self.count              = 0      #  total readings each sensor
        self.last_update        = 0      #  last measure timestamp
        self.flag_ready_to_read = False  #  True after sensor reading

sensors = SENSORS_GROUP()

sensors.sensor_id = [bytearray(b'(\xff\x88z \x17\x03\xfa'), \
    bytearray(b'(\xff* \xb0\x17\x05|'), bytearray(b'(\xff\xa6^Q\x17\x04\x19')]
sensors.sensor_name = ["PicoBox", "Moteur", "Eau"]
sensors.sensor_value = ["?", "?", "?"]
sensors.sensor_crc_err = [0, 0, 0]
sensors.sensor_other_err = [0, 0, 0]
# function asyncio to be used with a main asyncio as well (returns temperature)
async def get_sensors_value():
    for i, id in enumerate(sensors.sensor_id):
        try:
            sensors.sensor_value[i] = "?" # in case of read error we get a "?"
            ow.reset()  # I don't use the skip rom command but select each rom
            ow.writebyte(0x55)   # match rom command
            ow.write(id)         #  select this rom
            ow.writebyte(0x44)   # convert command
            await asyncio.sleep_ms(750)   # we wait at each iteration
            sensors.sensor_value[i] = str(ds.read_temp(id))
        except Exception as err:
            if str(err) == "CRC error":
                sensors.sensor_crc_err[i] +=1
            else:
                sensors.sensor_other_err[i] +=1
    sensors.count +=1
    sensors.last_update = time.time()
    sensors.flag_ready_to_read = True


# Non asyncio function (returns rom + temperature) ! Not used here !
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
