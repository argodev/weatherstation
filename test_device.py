#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Utility script to test each of the sensor readings"""

import logging
import click
import sys
from time import sleep

from SDL_Pi_TCA9545 import i2c_mux
import SDL_Pi_WeatherRack as SDL_Pi_WeatherRack
from tentacle_pi.AM2315 import AM2315
import Adafruit_BMP.BMP280 as BMP280
import HTU21D
import SDL_DS3231

TCA9545_ADDRESS = (0x73)  # 1110011 (A0+A1=VDD)
TCA9545_REG_CONFIG = (0x00)  # config register (R/W)
TCA9545_CONFIG_BUS0 = (0x01)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS1 = (0x02)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS2 = (0x04)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS3 = (0x08)  # 1 = enable, 0 = disable
ANEMOMETER_PIN = 26
RAIN_PIN = 21
SDL_MODE_I2C_ADS1015 = 1    # internally, the library checks for ADS1115 or ADS1015 if found
SDL_MODE_SAMPLE = 0  # sample mode means return immediately.  THe wind speed is averaged at sampleTime or when you ask, whichever is longer
SDL_MODE_DELAY = 1  # Delay mode means to wait for sampleTime and the average after that time.



def test_i2c_mux():
    """Test the i2c mux/switch"""
    logging.info('Testing I2C 4 Channel Mux...')
    try:
        i2cmux = i2c_mux(addr=TCA9545_ADDRESS, bus_enable=TCA9545_CONFIG_BUS0)
        logging.info('Switching to bus 2...')
        i2cmux.write_control_register(TCA9545_CONFIG_BUS2)
        logging.info('Success!')
        sleep(1)
        logging.info('Switching back to bus 0...')
        i2cmux.write_control_register(TCA9545_CONFIG_BUS1)
        logging.info('Success!')
        logging.info('I2C Mux is present and operating normally (TCA9545)')
    except IOError as io_err:
        logging.error('I2C Mux tests Failed')
        logging.error('%d : %s', io_err.errno, io_err.strerror)

def test_weather_rack():
    logging.info('Testing Weather Rack (INA3221)...')
    weather_rack = SDL_Pi_WeatherRack.SDL_Pi_WeatherRack(ANEMOMETER_PIN, RAIN_PIN, 0,0, SDL_MODE_I2C_ADS1015)
    weather_rack.setWindMode(SDL_MODE_SAMPLE, 5.0)

    SDL_INTERRUPT_CLICKS = 1
    totalRain = 0
    rain60Minutes = 0

    currentWindSpeed = weather_rack.current_wind_speed()
    currentWindGust = weather_rack.get_wind_gust()
    totalRain = totalRain + weather_rack.get_current_rain_total()/SDL_INTERRUPT_CLICKS
    # if ((config.ADS1015_Present == True) or (config.ADS1115_Present == True)):
    currentWindDirection = weather_rack.current_wind_direction()
    currentWindDirectionVoltage = weather_rack.current_wind_direction_voltage()

    logging.info("Rain Total= %0.2f in", (totalRain/25.4))
    logging.info("Rain Last 60 Minutes= %0.2f in", (rain60Minutes/25.4))
    logging.info("Wind Speed= %0.2f MPH", (currentWindSpeed/1.6))
    logging.info("MPH wind_gust= %0.2f MPH", (currentWindGust/1.6))
    logging.info("Wind Direction= %0.2f Degrees", currentWindDirection)
    logging.info("Wind Direction Voltage= %0.3f V",  currentWindDirectionVoltage)

def set_wind_direction():
    logging.info('Setting Wind Direction...')
    weather_rack = SDL_Pi_WeatherRack.SDL_Pi_WeatherRack(ANEMOMETER_PIN, RAIN_PIN, 0,0, SDL_MODE_I2C_ADS1015)
    weather_rack.setWindMode(SDL_MODE_SAMPLE, 5.0)

    while True:
        currentWindDirection = weather_rack.current_wind_direction()
        currentWindDirectionVoltage = weather_rack.current_wind_direction_voltage()
        logging.info("%0.2f Degrees | %0.3f V", currentWindDirection, currentWindDirectionVoltage)
        sleep(0.25)

def test_rain_guage():
    logging.info('Testing Rain Guage...')
    weather_rack = SDL_Pi_WeatherRack.SDL_Pi_WeatherRack(ANEMOMETER_PIN, RAIN_PIN, 0,0, SDL_MODE_I2C_ADS1015)
    SDL_INTERRUPT_CLICKS = 1
    totalRain = 0
    rain60Minutes = 0

    while True:
        reading = weather_rack.get_current_rain_total()
        totalRain = totalRain + (reading/float(SDL_INTERRUPT_CLICKS))
        logging.info("Reading= %0.4f in", reading)
        logging.info("Rain Total= %0.2f in", (totalRain/25.4))
        logging.info("Rain Last 60 Minutes= %0.2f in", (rain60Minutes/25.4))
        sleep(1)

def test_outdoor_temp():
    logging.info('Testing Outdoor Temperature Sensor (AM2315)...')
    try:
        crc_check = -1
        while crc_check < 0:
            outdoor_temp = AM2315(0x5c,"/dev/i2c-1")
            outside_temperature, outside_humidity, crc_check = outdoor_temp.sense()
            sleep(0.5)
        logging.info("Outside Temperature: %0.1f F", (outside_temperature * 1.8) + 32)
        logging.info("Outside Humidity: %0.1f", outside_humidity)
        logging.info("CRC: %i", crc_check)
        logging.info('Outdoor Temperature Test was Successful (AM2315)')

    except Exception as exc:
        logging.error('Outdoor Temperature Test Failed')


def test_barometric_pressure():
    logging.info('Testing Barometric Pressure Sensor (BMP280)...')
    try:
        barometer = BMP280.BMP280()
        logging.info('Temp = %.2f *F', (barometer.read_temperature()*1.8) + 32)
        logging.info('Pressure = %.2f Pa', barometer.read_pressure())
        logging.info('Altitude = %.2f m', barometer.read_altitude())
        logging.info('Sealevel Pressure = %.2f Pa', barometer.read_sealevel_pressure())
        logging.info('Barometric Pressure Test was Successful (BMP280)')

    except Exception as exc:
        logging.error('Barometric Pressure Test Failed')

def test_internal_humidity():
    logging.info('Testing HTU21D-F Humidity Sensor...')
    try:
        internal_humidity = HTU21D.HTU21D()
        temp = ((internal_humidity.read_temperature()*1.8) + 32)
        logging.info("Internal Temp: %s F", temp)
        logging.info("Humid: %s %% rH", internal_humidity.read_humidity())
        logging.info('Humidity Sensor Test was Successful (HTU21D-F)')

    except Exception as exc:
        logging.error('Humidity Sensor Test Failed')
        print exc

def test_real_time_clock():
    logging.info('Testing Real Time Clock (DS3231)...')
    try:
        rtc = SDL_DS3231.SDL_DS3231(1, 0x68)

        rtc.write_now()
        rtc.read_datetime()
        logging.info("DS3231= %s" % rtc.read_datetime())
        logging.info('Real Time Clock Test was Successful (DS3231)')

    except Exception as exc:
        logging.error('Real Time Clock Test Failed')


@click.command()
@click.option('--test-i2c', default=False, help='Test I2C Mux', is_flag=True)
@click.option('--test-rack', default=False, help='Test Weather Rack', is_flag=True)
@click.option('--test-temp', default=False, help='Test Outdoor Temp', is_flag=True)
@click.option('--test-pressure', default=False, help='Test Barometric Pressure', is_flag=True)
@click.option('--test-internal', default=False, help='Test Internals', is_flag=True)
@click.option('--test-clock', default=False, help='Test Clock', is_flag=True)
@click.option('--set-dir', default=False, help='Set direction for wind vane', is_flag=True)
@click.option('--test-rain', default=False, help='Test Rain Guage', is_flag=True)
# @click.option('--load-proctors', default=False, help='Should proctor data be loaded', is_flag=True)
# @click.option('--load-votes', default=False, help='Load session interest voting data', is_flag=True)
# @click.option('--load-surveys', default=False, help='Load session survey data', is_flag=True)
# @click.option('--generate-markdown', default=False, help='Generate Markdown Reports', is_flag=True)
# @click.option('--convert-pdf', default=False, help='Convert Markdown Reports to PDF', is_flag=True)
# @click.option('--send-emails', default=False, help='Send reports to speakers', is_flag=True)
def main(test_i2c, test_rack, test_temp, test_pressure, test_internal, test_clock, set_dir, test_rain):
    """Utility script to test each of the sensor readings"""
    log_format = '[%(asctime)s] %(levelname)s %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
    logging.info('Weather Station Test Utility')
    logging.info('Press ctrl+c to exit')

    try:
        # while True:
        if test_i2c:
            test_i2c_mux()
        if test_rack:
            test_weather_rack()
        if test_temp:
            test_outdoor_temp()
        if test_pressure:
            test_barometric_pressure()
        if test_internal:
            test_internal_humidity()
        if test_clock:
            test_real_time_clock()
        if set_dir:
            set_wind_direction()
        if test_rain:
            test_rain_guage()
            # sleep(1)


    except KeyboardInterrupt:
        print('\n')
        logging.info('Shutting Down...')
        logging.info('Exiting')
        sys.exit()


if __name__ == '__main__':
    main()
