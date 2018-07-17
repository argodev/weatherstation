#!/usr/bin/env python
# -*- coding:utf-8 -*-

""" Simple test script to check for the presence of all sensors """
import logging
import time
from datetime import datetime
import json
import requests

import Image
from influxdb import InfluxDBClient

import Adafruit_BMP.BMP280 as BMP280
import Adafruit_SSD1306
#import Adafruit_HTU21D as HTU21D
import HTU21D
from tentacle_pi.AM2315 import AM2315
# import SDL_Pi_TCA9545
from SDL_Pi_TCA9545 import i2c_mux
import SDL_Pi_SI1145.SDL_Pi_SI1145 as SI1145
from SDL_Pi_SI1145 import SI1145Lux
import SDL_DS3231
import SDL_Pi_INA3221
import SDL_Pi_WeatherRack as SDL_Pi_WeatherRack
import Scroll_SSD1306
from ISStreamer.Streamer import Streamer
import paho.mqtt.client as paho

from collections import deque
# setup our constants
# BASE_URL = 'https://dweet.io'
# THING_NAME = 'argo_weather'

TCA9545_ADDRESS = (0x73)  # 1110011 (A0+A1=VDD)
TCA9545_REG_CONFIG = (0x00)  # config register (R/W)
TCA9545_CONFIG_BUS0 = (0x01)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS1 = (0x02)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS2 = (0x04)  # 1 = enable, 0 = disable
TCA9545_CONFIG_BUS3 = (0x08)  # 1 = enable, 0 = disable
RST = 24  # Raspberry Pi pin configuration
LIPO_BATTERY_CHANNEL = 1
SOLAR_CELL_CHANNEL   = 2
OUTPUT_CHANNEL       = 3
SUNAIRLED = 25
ANEMOMETER_PIN = 26
RAIN_PIN = 21
SDL_MODE_INTERNAL_AD = 0
SDL_MODE_I2C_ADS1015 = 1    # internally, the library checks for ADS1115 or ADS1015 if found
SDL_MODE_SAMPLE = 0  # sample mode means return immediately.  THe wind speed is averaged at sampleTime or when you ask, whichever is longer
SDL_MODE_DELAY = 1  # Delay mode means to wait for sampleTime and the average after that time.



# TB_ACCESS_TOKEN = "P9ByHW2cd0HXAWekp7Zj"

# MQTT_BROKER = "192.168.2.143"
# MQTT_PORT = 1883
# MQTT_USERNAME = "weatherpi"
# MQTT_PASSWORD = "eQuest123!"

# def publish_mqtt(topic, value):
#     logging.info('mqtt')
#     pass
#     #mqtt = paho.Client("weatherpi")
#     #mqtt.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
#     #mqtt.connect(MQTT_BROKER)
#     #mqtt.publish(topic, value)

class WeatherStation(object):

    def __init__(self):
        self._i2cmux = None
        self._sunlight = None
        self._barometer = None
        self._outdoor_temp = None
        self._internal_humidity = None
        self._rtc = None
        self._sun_air_plus = None
        self._weather_rack = None

        # setup queue for rain totals
        # length is set for 1 reading every 10s for 1 hour
        self._rain_last_60 = deque(maxlen=360)


    def _returnPercentLeftInBattery(self, current_voltage, max_volt):
        scaled_volts = current_voltage / max_volt

        if (scaled_volts > 1.0):
            scaled_volts = 1.0

        if (scaled_volts > .9686):
            return_percent = 10*(1-(1.0-scaled_volts)/(1.0-.9686))+90
            return return_percent

        if (scaled_volts > 0.9374):
            return_percent = 10*(1-(0.9686-scaled_volts)/(0.9686-0.9374))+80
            return return_percent

        if (scaled_volts > 0.9063):
            return_percent = 30*(1-(0.9374-scaled_volts)/(0.9374-0.9063))+50
            return return_percent

        if (scaled_volts > 0.8749):
            return_percent = 20*(1-(0.8749-scaled_volts)/(0.9063-0.8749))+11
            return return_percent

        if (scaled_volts > 0.8437):
            return_percent = 15*(1-(0.8437-scaled_volts)/(0.8749-0.8437))+1
            return return_percent

        if (scaled_volts > 0.8126):
            return_percent = 7*(1-(0.8126-scaled_volts)/(0.8437-0.8126))+2
            return return_percent

        if (scaled_volts > 0.7812):
            return_percent = 4*(1-(0.7812-scaled_volts)/(0.8126-0.7812))+1
            return return_percent

        return 0



    def test_i2c_mux(self):
        logging.info('Testing I2C 4 Channel Mux...')
        # try:
        #     self._i2cmux = SDL_Pi_TCA9545.SDL_Pi_TCA9545(addr=TCA9545_ADDRESS, bus_enable=TCA9545_CONFIG_BUS0)
        #     self._i2cmux.write_control_register(TCA9545_CONFIG_BUS2)
        #     logging.info('I2C Mux is present and operating normally (TCA9545)')
        # except:
        #     logging.error('I2C Mux tests Failed')


    def test_sunlight_sensor(self):
        # if self._i2cmux is None:
        #     self.test_i2c_mux()

        # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS1)

        logging.info('Testing Sunlight Sensor (SI1145)...')
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
            logging.info('Sunlight Sensor Test was Successful (SI1145)')

        except Exception as exc:
            logging.error('Sunlight Sensor Test Failed')


    def test_barometric_pressure(self):
        # if self._i2cmux is None:
        #     self.test_i2c_mux()

        # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)
        logging.info('Testing Barometric Pressure Sensor (BMP280)...')
        try:
            self._barometer = BMP280.BMP280()
            logging.info('Temp = %.2f *F', (self._barometer.read_temperature()*1.8) + 32)
            logging.info('Pressure = %.2f Pa', self._barometer.read_pressure())
            logging.info('Altitude = %.2f m', self._barometer.read_altitude())
            logging.info('Sealevel Pressure = %.2f Pa', self._barometer.read_sealevel_pressure())
            logging.info('Barometric Pressure Test was Successful (BMP280)')

        except Exception as exc:
            logging.error('Barometric Pressure Test Failed')


    def test_outdoor_temp(self):
        # if self._i2cmux is None:
        #     self.test_i2c_mux()

        # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)

        logging.info('Testing Outdoor Temperature Sensor (AM2315)...')
        try:
            crc_check = -1
            while crc_check < 0:
                self._outdoor_temp = AM2315(0x5c,"/dev/i2c-1")
                outside_temperature, outside_humidity, crc_check = self._outdoor_temp.sense()
                time.sleep(0.5)
            logging.info("Outside Temperature: %0.1f F", (outside_temperature * 1.8) + 32)
            logging.info("Outside Humidity: %0.1f", outside_humidity)
            logging.info("CRC: %i", crc_check)
            logging.info('Outdoor Temperature Test was Successful (AM2315)')

        except Exception as exc:
            logging.error('Outdoor Temperature Test Failed')


    def test_real_time_clock(self):
        # if self._i2cmux is None:
        #     self.test_i2c_mux()

        # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)

        logging.info('Testing Real Time Clock (DS3231)...')
        try:
            # start_time = datetime.utcnow()
            self._rtc = SDL_DS3231.SDL_DS3231(1, 0x68)

            self._rtc.write_now()
            self._rtc.read_datetime()
            logging.info("DS3231= %s" % self._rtc.read_datetime())
            logging.info('Real Time Clock Test was Successful (DS3231)')

        except Exception as exc:
            logging.error('Real Time Clock Test Failed')

    def test_internal_humidity(self):
        # if self._i2cmux is None:
        #     self.test_i2c_mux()

        # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)

        logging.info('Testing HTU21D-F Humidity Sensor...')
        try:
            self._internal_humidity = HTU21D.HTU21D()
            temp = ((self._internal_humidity.read_temperature()*1.8) + 32)
            logging.info("Internal Temp: %s F", temp)
            logging.info("Humid: %s %% rH", self._internal_humidity.read_humidity())
            logging.info('Humidity Sensor Test was Successful (HTU21D-F)')

        except Exception as exc:
            logging.error('Humidity Sensor Test Failed')
            print exc

    def test_solar_power_controller(self):
        # if self._i2cmux is None:
        #     self.test_i2c_mux()

        # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS2)
        logging.info('Testing Solar Power Controller (INA3221)...')
        # try:
        #     self._sun_air_plus = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
        #     bus_voltage_1 = self._sun_air_plus.getBusVoltage_V(LIPO_BATTERY_CHANNEL)
        #     logging.info('Bus Voltage 1: %.2f', bus_voltage_1)

        #     shunt_voltage_1 = self._sun_air_plus.getShuntVoltage_mV(LIPO_BATTERY_CHANNEL)
        # 	# minus is to get the "sense" right.   - means the battery is charging, + that it is discharging
        #     battery_current = self._sun_air_plus.getCurrent_mA(LIPO_BATTERY_CHANNEL)
        #     battery_voltage = bus_voltage_1 + (shunt_voltage_1 / 1000)
        #     battery_power = battery_voltage * (battery_current/1000)
        #     logging.info('Battery Current: %.2f mA', battery_current)

        #     bus_voltage_2 = self._sun_air_plus.getBusVoltage_V(SOLAR_CELL_CHANNEL)
        #     shunt_voltage_2 = self._sun_air_plus.getShuntVoltage_mV(SOLAR_CELL_CHANNEL)
        #     solar_current = -self._sun_air_plus.getCurrent_mA(SOLAR_CELL_CHANNEL)
        #     solar_voltage = bus_voltage_2 + (shunt_voltage_2 / 1000)
        #     solar_power = solar_voltage * (solar_current/1000)
        #     logging.info('Solar Current: %.2f mA', solar_current)

        #     bus_voltage_3 = self._sun_air_plus.getBusVoltage_V(OUTPUT_CHANNEL)
        #     shunt_voltage_3 = self._sun_air_plus.getShuntVoltage_mV(OUTPUT_CHANNEL)
        #     load_current = self._sun_air_plus.getCurrent_mA(OUTPUT_CHANNEL)
        #     load_voltage = bus_voltage_3
        #     load_power = load_voltage * (load_current/1000)

        #     battery_charge = self._returnPercentLeftInBattery(battery_voltage, 4.19)
        #     logging.info('Battery Charge: %.2f', battery_charge)
        #     logging.info('Solar Power Controller Test was Successful (INA3221)')

        # except Exception as exc:
        #     logging.error('Solar Power Controller Test Failed')

    def test_weather_rack(self):
        # if self._i2cmux is None:
        #     self.test_i2c_mux()

        # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)
        logging.info('Testing Weather Rack (INA3221)...')
        self._weather_rack = SDL_Pi_WeatherRack.SDL_Pi_WeatherRack(ANEMOMETER_PIN, RAIN_PIN, 0,0, SDL_MODE_I2C_ADS1015)
        self._weather_rack.setWindMode(SDL_MODE_SAMPLE, 5.0)

        SDL_INTERRUPT_CLICKS = 1
        totalRain = 0
        rain60Minutes = 0

        currentWindSpeed = self._weather_rack.current_wind_speed()
        currentWindGust = self._weather_rack.get_wind_gust()
        totalRain = totalRain + self._weather_rack.get_current_rain_total()/SDL_INTERRUPT_CLICKS
        # if ((config.ADS1015_Present == True) or (config.ADS1115_Present == True)):
        currentWindDirection = self._weather_rack.current_wind_direction()
        currentWindDirectionVoltage = self._weather_rack.current_wind_direction_voltage()

        logging.info("Rain Total= %0.2f in", (totalRain/25.4))
        logging.info("Rain Last 60 Minutes= %0.2f in", (rain60Minutes/25.4))
        logging.info("Wind Speed= %0.2f MPH", (currentWindSpeed/1.6))
        logging.info("MPH wind_gust= %0.2f MPH", (currentWindGust/1.6))
        logging.info("Wind Direction= %0.2f Degrees", currentWindDirection)
        logging.info("Wind Direction Voltage= %0.3f V",  currentWindDirectionVoltage)

    def test_lightning_detector(self):
        pass


    # def send_dweet(self, payload):
    #     url = '{0}/dweet/for/{1}'.format(BASE_URL, THING_NAME)
    #     data = json.dumps(payload)
    #     headers = {'Content-type': 'application/json'}

    #     request_func = getattr(requests, 'post')
    #     response = request_func(url, data=data, headers=headers)

    #     # raise an exception if request is not successful
    #     #print response.status_code
    #     # if not response.status_code == requests.codes.ok:
    #     #     print'HTTP {0} response'.format(response.status_code)
    #     #     # raise DweepyError('HTTP {0} response'.format(response.status_code))
    #     response_json = response.json()
    #     if response_json['this'] == 'failed':
    #         print response_json['because']
    #         # raise DweepyError(response_json['because'])
    #     return response_json['with']

    # def send_to_thingsboard(self, payload):
    #     url = 'http://data.robgillen.com:8080/api/v1/{0}/telemetry'.format(TB_ACCESS_TOKEN)

    #     # remove the timestamp from the payload
    #     payload.pop('timestamp')

    #     tb_wrapper = {
    #         'ts': int(time.time() * 1000),
    #         'values': payload
    #     }

    #     data = json.dumps(tb_wrapper)
    #     headers = {'Content-type': 'application/json'}
    #     request_func = getattr(requests, 'post')
    #     response = request_func(url, data=data, headers=headers)

    #     # raise an exception if request is not successful
    #     #print response.status_code
    #     # if not response.status_code == requests.codes.ok:
    #     #     print'HTTP {0} response'.format(response.status_code)
    #     #     # raise DweepyError('HTTP {0} response'.format(response.status_code))
    #     # response_json = response.json()
    #     # if response_json['this'] == 'failed':
    #     #     print response_json['because']
    #     #     # raise DweepyError(response_json['because'])

    def send_to_influxdb(self, data):
        """Helper to package and send to influxdb"""
        user = 'weather'
        password = 'eQuest123!'
        dbname = 'homedb'
        host = '192.168.2.143'
        port = 8086

        json_body = [
            {
                "measurement": "local_weather",
                "time": datetime.utcnow().isoformat(),
            }
        ]

        json_body[0]['fields'] = data

        client = InfluxDBClient(host, port, user, password, dbname)
        client.write_points(json_body)

        client.close()



    def run_loop(self):
        counter = 0
        #outside_temperature = 0
        #outside_humidity = 0


        while True:
            try:
                # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)

                if self._barometer:
                    internal_temp = (self._barometer.read_temperature()*1.8) + 32
                    pressure = self._barometer.read_pressure()
                    altitude = self._barometer.read_altitude()
                    sealevel_pressure = self._barometer.read_sealevel_pressure()
                else:
                    internal_temp = 0.00
                    pressure = 0.00
                    altitude = 0.00
                    sealevel_pressure = 0.00
                    self.test_barometric_pressure()


                crc_check = -1
                while crc_check <> 0:
                    outside_temperature, outside_humidity, crc_check = self._outdoor_temp.sense()
                    logging.info("pausing for temperature...")
                    time.sleep(1)
                outside_temperature = (outside_temperature * 1.8) + 32
                wind_speed = self._weather_rack.current_wind_speed()/1.6
                wind_gust = self._weather_rack.get_wind_gust()/1.6
                wind_direction = float(self._weather_rack.current_wind_direction())
                wind_direction_voltage = self._weather_rack.current_wind_direction_voltage()
                total_rain_raw = self._weather_rack.get_current_rain_total()
                logging.info("total_rain_raw: %f", total_rain_raw)
                total_rain = total_rain_raw/25.4
                logging.info("total_rain: %f", total_rain)
                self._rain_last_60.append(total_rain_raw)
                rain_last_60 = sum(self._rain_last_60)/25.4
                logging.info("rain_last_60: %f", rain_last_60)


                internal_temp_2 = ((self._internal_humidity.read_temperature()*1.8) + 32)
                internal_humidity = self._internal_humidity.read_humidity()
                # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS2)
                # bus_voltage_1 = self._sun_air_plus.getBusVoltage_V(LIPO_BATTERY_CHANNEL)
                # shunt_voltage_1 = self._sun_air_plus.getShuntVoltage_mV(LIPO_BATTERY_CHANNEL)
                # # minus is to get the "sense" right.   - means the battery is charging, + that it is discharging
                # battery_current = self._sun_air_plus.getCurrent_mA(LIPO_BATTERY_CHANNEL)
                # battery_voltage = bus_voltage_1 + (shunt_voltage_1 / 1000)
                # battery_power = battery_voltage * (battery_current/1000)
                # bus_voltage_2 = self._sun_air_plus.getBusVoltage_V(SOLAR_CELL_CHANNEL)
                # shunt_voltage_2 = self._sun_air_plus.getShuntVoltage_mV(SOLAR_CELL_CHANNEL)
                # solar_current = abs(self._sun_air_plus.getCurrent_mA(SOLAR_CELL_CHANNEL))
                # solar_voltage = bus_voltage_2 + (shunt_voltage_2 / 1000)
                # solar_power = abs(solar_voltage * (solar_current/1000))
                # bus_voltage_3 = self._sun_air_plus.getBusVoltage_V(OUTPUT_CHANNEL)
                # shunt_voltage_3 = self._sun_air_plus.getShuntVoltage_mV(OUTPUT_CHANNEL)
                # load_current = self._sun_air_plus.getCurrent_mA(OUTPUT_CHANNEL)
                # load_voltage = bus_voltage_3
                # load_power = load_voltage * (load_current/1000)
                # battery_charge = self._returnPercentLeftInBattery(battery_voltage, 4.19)

                sunlight_visible = 0 #SI1145Lux.SI1145_VIS_to_Lux(self._sunlight.readVisible())
                sunlight_ir = 0 #SI1145Lux.SI1145_IR_to_Lux(self._sunlight.readIR())
                sunlight_uv = 0 #self._sunlight.readUV()
                sunlight_uv_index = 0 #sunlight_uv / 100.0

                readings = {
                    'timestamp' : str(datetime.utcnow().isoformat()),
                    'internal_temp': internal_temp,
                    'internal_humidity': internal_humidity,
                    'outside_temp': outside_temperature,
                    'outside_humidity': outside_humidity,
                    # 'battery_charge': float(battery_charge),
                    'wind_speed': wind_speed,
                    'wind_gust': wind_gust,

                    # 'battery_power': battery_power,
                    # 'solar_power': solar_power,
                    # 'load_power': load_power,

                    # 'battery_current': battery_current,
                    # 'load_current': load_current,
                    # 'solar_current': solar_current,

                    # 'load_voltage': load_voltage,
                    # 'solar_voltage': solar_voltage,
                    # 'battery_voltage': battery_voltage,
                    'pressure': pressure,
                    'wind_direction': wind_direction,

                    'total_rain': total_rain,
                    'rain_last_60': rain_last_60,

                    'altitude': altitude,
                    'sealevel_pressure': sealevel_pressure,


                    # 'sunlight_visible': sunlight_visible,
                    # 'sunlight_ir': sunlight_ir,
                    # 'sunlight_uv': sunlight_uv,
                    # 'sunlight_uv_index': sunlight_uv_index,


                    # 'bus_voltage_1': bus_voltage_1,
                    # 'shunt_voltage_1': shunt_voltage_1,
                    # 'bus_voltage_2': bus_voltage_2,
                    # 'shunt_voltage_2': shunt_voltage_2,
                    # 'bus_voltage_3': bus_voltage_3,
                    'wind_direction_voltage': wind_direction_voltage,
                    'internal_temp_2': internal_temp_2,
                    'crc_check': crc_check
                }

                # self._i2cmux.write_control_register(TCA9545_CONFIG_BUS0)

                #print readings
                if crc_check == 0:
                    self.send_to_influxdb(readings)
                    # if counter >= 12:
                        # with open('weather.log', 'a') as logfile:
                        #     logfile.write(json.dumps(readings) + '\n')
                        # self._streamer.log_object(readings, key_prefix="some_dict")
                        # self.send_dweet(readings)
                        #self.send_to_thingsboard(readings)
                else:
                    logging.info("CRC Failed: %i", crc_check)

                time.sleep(10)

            except IOError as ioerr:
                logging.warn('Unable to read values due to an IO Error... Retrying')
                logging.warn(ioerr.errno)
                logging.warn(ioerr.message)
                time.sleep(5)


def main():
    """Primary entry point for the test application"""
    log_format = '[%(asctime)s] %(levelname)s %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
    logging.info('** Weather Station System Test Starting **')

    station = WeatherStation()
    # station.test_i2c_mux()
    # station.test_sunlight_sensor()
    
    station.test_internal_humidity()
    station.test_barometric_pressure()
    station.test_outdoor_temp()
    station.test_real_time_clock()
    station.test_solar_power_controller()
    station.test_weather_rack()
    logging.info('** Weather Station System Test Complete **')

    station.run_loop()

    # lightning detetor

    # rain bucket


if __name__ == "__main__":
    main()
