from machine import Pin
import onewire
import time
import ds18x20
import asyncio

ow = onewire.OneWire(Pin(9))
ow.scan()
ow.reset()
ds = ds18x20.DS18X20(ow)
roms = ds.scan()

value_list = ["?", "?"]  # unknown at init, will be populated when read
flag_ready_to_read = False  # will True after sensor reading and reset by
                            # reading the list (from main)

# function asyncio to be used with a main asyncio as well (returns temperature)
# async def get_sensors_value():
    # ds.convert_temp()
    # await asyncio.sleep_ms(750)
    # print(tuple(type(str(ds.read_temp(rom))) for rom in roms))

# function asyncio to be used with a main asyncio as well (returns temperature)
async def get_sensors_value():
    global flag_ready_to_read  # lists are mutable objects not booleans
    ds.convert_temp()          # so only the boolean needs global declaration
    await asyncio.sleep_ms(750)
    i = 0
    for rom in roms:
        value_list[i] = str(ds.read_temp(rom))
        i += 1
    flag_ready_to_read = True


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
