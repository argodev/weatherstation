import time
from ISStreamer.Streamer import Streamer 

device_file = '/sys/bus/w1/devices/28-000004f4553f/w1_slave'

streamer = Streamer(bucket_key='8a2348e8-e892-47a6-bacb-48a002245e59',
                    access_key='vbDL1QllVbnvKpv234WtuLRAT4K40Jqp')

def read_temp_raw():
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines


def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equal_pos = lines[1].find('t=')
    if equal_pos != 1:
        temp_string = lines[1][equal_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f


while True:
    temps = read_temp()
    print(temps[1])
    streamer.log("outdoor_temp", temps[1])
    streamer.flush()
    time.sleep(120)

