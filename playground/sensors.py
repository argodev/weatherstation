#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import smbus
from datetime import datetime
import signal
import sys
import pickle

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import Adafruit_BMP.BMP085 as BMP085
import Adafruit_SSD1306
import picamera

BMP085_ADDR = 0x77
TSL2561_ADDR = 0x39
SSD1306_ADDR = 0x3C

DISPLAY = None
RST = None  # on the PiOLED this pin isnt used

# setup to handle termination requests
def signal_handler(signal, frame):
    print '\nClosing nicely...\n'
    clear_screen()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# get the i2c bus
bus = smbus.SMBus(1)

# power on the light sensor
# select the control register (0x00) with the command register (0x80)
# and set power on (0x03)
bus.write_byte_data(TSL2561_ADDR, 0x00 | 0x80, 0x03)

# select the timing register (0x01) with the command register (0x80)
# and set the nominal integration time (0x02) - 402ms
bus.write_byte_data(TSL2561_ADDR, 0x01 | 0x80, 0x02)

bmp_sensor = BMP085.BMP085()

DISPLAY = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
DISPLAY.begin()
DISPLAY.clear()
DISPLAY.display()

# create blank image for ddrawing
# make sure to create image with mode '1' for 1-bit color
display_width = DISPLAY.width
display_height = DISPLAY.height
image = Image.new('1', (display_width, display_height))

# get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image
draw.rectangle((0,0,display_width, display_height), outline=0, fill=0)

# define some constants to make drawing easier
padding = -2
top = padding
bottom = display_height - padding
x = 0
Y_SPACE = 9

# load the default font
font = ImageFont.load_default()

#configure the camera
camera = picamera.PiCamera()
camera.hflip = True
camera.vflip = True
camera.resolution = (1024,768)

# sleep to ensure settings are in place 
time.sleep(0.5)
counter = 0


def clear_screen():
    # draw a black filled box to clear the image
    draw.rectangle((0,0,display_width, display_height), outline=0, fill=0)

    # display image
    DISPLAY.image(image)
    DISPLAY.display()
    

# this goes into a while loop...
while True:
    # Read the data back from 0x0C with the command register, 2 bytes of data
    # ch0 LSB, ch0 MSB
    data = bus.read_i2c_block_data(TSL2561_ADDR, 0x0C | 0x80, 2)

    # Read the data back from 0x0E with the command register, 2 bytes of data
    # ch1 LSB, ch1 MSB
    data1 = bus.read_i2c_block_data(TSL2561_ADDR, 0x0E | 0x80, 2)

    # Convert the data
    ch0 = data[1] * 256 + data[0]
    ch1 = data1[1] * 256 + data1[0]

    counter += 1
    if (counter % 60) == 0:
        image_name = time.strftime("%Y%m%d-%H%M%S") + '.jpg'
        camera.capture(image_name)
    

    full_spectrum = ch0
    infrared = ch1
    visible = ch0 - ch1
    temp_degrees = (bmp_sensor.read_temperature() * 1.8) + 32
    pressure = bmp_sensor.read_pressure()
    altitude = bmp_sensor.read_altitude()
    timestamp = datetime.utcnow()

    rec = {
        'full_spectrum': full_spectrum,
        'infrared': infrared,
        'visible': visible,
        'temp_degrees': temp_degrees,
        'pressure': pressure,
        'altitude': altitude,
        'timestamp': timestamp
    }

    with open('data.pickle', 'ab') as data_file:
        pickle.dump(rec, data_file, pickle.HIGHEST_PROTOCOL)

    # Output data to screen
    # print 'Full Spectrum (IR + Visible):  {0:0.2f} lux'.format(ch0)
    # print 'Infrared Value:                {0:0.2f} lux'.format(ch1)
    # print 'Visible Value:                 {0:0.2f} lux'.format(ch0 - ch1)
    # print 'Temp:                          {0:0.2f} F'.format((bmp_sensor.read_temperature()*1.8) + 32)
    # print 'Pressure:                      {0:0.2f} Pa'.format(bmp_sensor.read_pressure())
    # print 'Altitude:                      {0:0.2f} m'.format(bmp_sensor.read_altitude())
    # print 'Time:                          {0}'.format(datetime.utcnow().isoformat())

    # draw a black filled box to clear the image
    draw.rectangle((0,0,display_width, display_height), outline=0, fill=0)

    draw.text((x, top+Y_SPACE*0), 'Spectrum: {0:0.0f} lux'.format(full_spectrum), font=font, fill=255)
    draw.text((x, top+Y_SPACE*1), 'Infrared: {0:0.0f} lux'.format(infrared), font=font, fill=255)
    draw.text((x, top+Y_SPACE*2), 'Visible:  {0:0.0f} lux'.format(visible), font=font, fill=255)
    draw.text((x, top+Y_SPACE*3), 'Temp:     {0:0.1f} F'.format(temp_degrees), font=font, fill=255)
    draw.text((x, top+Y_SPACE*4), 'Pressure: {0:0.2f} Pa'.format(pressure), font=font, fill=255)
    draw.text((x, top+Y_SPACE*5), 'Altitude: {0:0.2f} m'.format(altitude), font=font, fill=255)
    draw.text((x, top+Y_SPACE*6), timestamp.strftime('%Y-%m-%d %H:%M:%S'), font=font, fill=255)

    # display image
    DISPLAY.image(image)
    DISPLAY.display()

    time.sleep(1)

