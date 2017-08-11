#!/usr/bin/env python
# -*- coding:utf-8 -*-

""" Simple test script to check for the presence of all sensors """
import logging
import time

import Image

import Adafruit_SSD1306
import Adafruit_HTU21D as HTU21D
import SDL_Pi_TCA9545
import SDL_Pi_SI1145.SDL_Pi_SI1145 as SI1145
from SDL_Pi_SI1145 import SI1145Lux


# setup our constants
TCA9545_ADDRESS = (0x73)  # 1110011 (A0+A1=VDD)
TCA9545_REG_CONFIG = (0x00)  # config register (R/W)
TCA9545_CONFIG_BUS0 = (0x01)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS1 = (0x02)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS2 = (0x04)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS3 = (0x08)  # 1 = enable, 0 = disable
RST = 24  # Raspberry Pi pin configuration


class WeatherStation(object):

    def __init__(self):
        self._i2cmux = None
        self._oled = None
        self._sunlight = None


    def test_i2c_mux(self):
        logging.info('Testing I2C 4 Channel Mux...')
        try:
            self._i2cmux = SDL_Pi_TCA9545.SDL_Pi_TCA9545(addr=TCA9545_ADDRESS, bus_enable=TCA9545_CONFIG_BUS0)
            self._i2cmux.write_control_register(TCA9545_CONFIG_BUS2)
            logging.info('I2C Mux is present and operating normally (TCA9545)')
        except:
            logging.error('I2C Mux tests Failed')


    def test_oled_display(self):
        if self._i2cmux is None:
            self.test_i2c_mux()

        self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)

        logging.info('Testing OLED Display...')
        try:
            self._oled = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)
            self._oled.begin()
            self._oled.clear()
            self._oled.display()

            image = Image.open('happycat_oled_64.ppm').convert('1')
            self._oled.image(image)
            self._oled.display()
            time.sleep(1)
            self._oled.clear()
            self._oled.display()
            logging.info('OLED Display Test was Successful (SSD1306)')
        except:
            logging.error('OLED Display Test Failed')


    def test_sunlight_sensor(self):
        if self._i2cmux is None:
            self.test_i2c_mux()

        self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)

        logging.info('Testing SI1145 Sunlight Sensor...')
        try:
            self._sunlight = SI1145.SDL_Pi_SI1145()
            time.sleep(1)  # pause to let the sensor be enabled

            sunlight_visible = SI1145Lux.SI1145_VIS_to_Lux(self._sunlight.readVisible())
            sunlight_ir = SI1145Lux.SI1145_IR_to_Lux(self._sunlight.readIR())
            sunlight_uv = self._sunlight.readUV()
            sunlight_uv_index = sunlight_uv / 100.0
            logging.info('Sunlight Visible: %f', sunlight_visible)
            logging.info('Sunlight IR: %f', sunlight_ir)
            logging.info('Sunlight UV: %f', sunlight_uv)
            logging.info('Sunlight UV Index: %f', sunlight_uv_index)

        except Exception as exc:
            logging.error('Sunlight Sensor Test Failed')


# # enable I2C Bus 0
# tca9545.write_control_register(TCA9545_CONFIG_BUS0)

# logging.info('Testing HTU21D-F Humidity Sensor...')
# try:
#     htu21d = HTU21D.HTU21D()
#     print 'Temp = {0:0.2f} *C'.format(htu21d.read_temperature())
#     print 'Humidity  = {0:0.2f} %'.format(htu21d.read_humidity())
#     print 'Dew Point = {0:0.2f} *C'.format(htu21d.read_dewpoint())
#     logging.info('Humidity Sensor Test was Successful (HTU21D-F)')
# except Exception as exc:
#     logging.error('Humidity Sensor Test Failed')
#     print exc
























def main():
    """Primary entry point for the test application"""
    log_format = '[%(asctime)s] %(levelname)s %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
    logging.info('** Weather Station System Test Starting **')

    station = WeatherStation()
    station.test_i2c_mux()
    station.test_oled_display()
    station.test_sunlight_sensor()

    logging.info('** Weather Station System Test Complete **')


if __name__ == "__main__":
    main()
