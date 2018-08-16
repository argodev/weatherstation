#!/usr/bin/env python
# -*- coding:utf-8 -*-

""" Simple test script to check for the presence of all sensors """
import json
import logging
import time
from collections import deque
from datetime import datetime
from signal import SIGHUP, SIGTERM, signal

import requests

import Adafruit_BMP.BMP280 as BMP280  # Pressure / Internal Temp
import HTU21D  # internal humidity sensor
import SDL_DS3231   # real-time clock
import SDL_Pi_WeatherRack as SDL_Pi_WeatherRack  # wind speed/dir + rain
from influxdb import InfluxDBClient  # Send to Influx
from tentacle_pi.AM2315 import AM2315 # Outdoor Temp/Humidity

import SDL_Pi_INA3221 # this is needed for the ADC used for wind direction


ANEMOMETER_PIN = 26
RAIN_PIN = 21
SDL_MODE_I2C_ADS1015 = 1    # internally, the library checks for ADS1115 or ADS1015 if found
SDL_MODE_SAMPLE = 0  # sample mode means return immediately.  The wind speed is averaged at sampleTime or when you ask, whichever is longer
SDL_MODE_DELAY = 1  # Delay mode means to wait for sampleTime and the average after that time.


class WeatherStation(object):

    def __init__(self):
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
        self._rain_today = 0.
        self._rain_today_last_day = datetime.now().day
        if datetime.now().year == 2018 and datetime.now().month==8 and datetime.now().day==16:
            self._rain_today = 0.03


    def test_barometric_pressure(self):
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
            logging.error(exc.message)


    def test_outdoor_temp(self):
        logging.info('Testing Outdoor Temperature Sensor (AM2315)...')
        try:
            crc_check = -1
            while crc_check <> 1:
                self._outdoor_temp = AM2315(0x5c,"/dev/i2c-1")
                outside_temperature, outside_humidity, crc_check = self._outdoor_temp.sense()
                time.sleep(0.5)
            logging.info("Outside Temperature: %0.1f F", (outside_temperature * 1.8) + 32)
            logging.info("Outside Humidity: %0.1f", outside_humidity)
            logging.info("CRC: %i", crc_check)
            logging.info('Outdoor Temperature Test was Successful (AM2315)')

        except Exception as exc:
            logging.error('Outdoor Temperature Test Failed')
            logging.error(exc.message)


    def test_real_time_clock(self):
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
            logging.error(exc.message)


    def test_internal_humidity(self):
        logging.info('Testing HTU21D-F Humidity Sensor...')
        try:
            self._internal_humidity = HTU21D.HTU21D()
            temp = ((self._internal_humidity.read_temperature()*1.8) + 32)
            logging.info("\tInternal Temp: %s F", temp)
            logging.info("\tHumid: %s %% rH", self._internal_humidity.read_humidity())
            logging.info('\tHumidity Sensor Test was Successful (HTU21D-F)')

        except Exception as exc:
            logging.error('\tHumidity Sensor Test Failed')
            logging.error('\t' + exc.message)

    def test_weather_rack(self):
        logging.info('Testing Weather Rack (INA3221)...')
        self._weather_rack = SDL_Pi_WeatherRack.SDL_Pi_WeatherRack(ANEMOMETER_PIN, RAIN_PIN, 0,0, SDL_MODE_I2C_ADS1015)
        self._weather_rack.setWindMode(SDL_MODE_SAMPLE, 5.0)

        SDL_INTERRUPT_CLICKS = 1
        totalRain = 0
        rain60Minutes = 0

        currentWindSpeed = self._weather_rack.current_wind_speed()
        currentWindGust = self._weather_rack.get_wind_gust()
        totalRain = totalRain + self._weather_rack.get_current_rain_total()/SDL_INTERRUPT_CLICKS
        currentWindDirection = self._weather_rack.current_wind_direction()
        currentWindDirectionVoltage = self._weather_rack.current_wind_direction_voltage()

        logging.info("\tRain Total= %0.2f in", (totalRain/25.4))
        logging.info("\tRain Last 60 Minutes= %0.2f in", (rain60Minutes/25.4))
        logging.info("\tWind Speed= %0.2f MPH", (currentWindSpeed/1.6))
        logging.info("\tMPH wind_gust= %0.2f MPH", (currentWindGust/1.6))
        logging.info("\tWind Direction= %0.2f Degrees", currentWindDirection)
        logging.info("\tWind Direction Voltage= %0.3f V",  currentWindDirectionVoltage)

    def test_lightning_detector(self):
        pass

    def send_to_influxdb(self, data):
        """Helper to package and send to influxdb"""
        user = 'weather'
        password = 'eQuest123!'
        dbname = 'homedb'
        host = '192.168.2.143'
        port = 8086

        json_body = [{
            "measurement": "local_weather",
            "time": datetime.utcnow().isoformat(),
        }]

        json_body[0]['fields'] = data

        client = InfluxDBClient(host, port, user, password, dbname)
        client.write_points(json_body)
        client.close()


    def sendWeatherUndergroundData(self, currentWindSpeed, currentWindGust, outsideTemperature, outsideHumidity, currentWindDirection, rain60Minutes, bmp180SeaLevel, dewpointf, dailyrainin): 

        # https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=KCASANFR5&PASSWORD=XXXXXX&dateutc=2000-01-01+10%3A32%3A35&winddir=230&windspeedmph=12&windgustmph=12&tempf=70&rainin=0&baromin=29.1&dewptf=68.2&humidity=90&weather=&clouds=&softwaretype=vws%20versionxx&action=updateraw	

        # build the URL
        myURL = "ID="+"KTNKNOXV230"
        myURL += "&PASSWORD="+"o4c21o1u"
        myURL += "&dateutc=now"

        # now weather station variables
        # convert wind direction based on actual direction...
        currentWindDirection = (currentWindDirection + 90)
        if (currentWindDirection >= 360):
            currentWindDirection - 360

        myURL += "&winddir=%i" % currentWindDirection
        myURL += "&windspeedmph=%0.2f" % currentWindSpeed 
        myURL += "&windgustmph=%0.2f" % currentWindGust
        myURL += "&humidity=%i" % outsideHumidity
        myURL += "&tempf=%0.2f" % outsideTemperature
        myURL += "&dewptf=%0.2f" % dewpointf
        myURL += "&dailyrainin=%0.2f" % dailyrainin
        myURL += "&rainin=%0.2f" % rain60Minutes
        myURL += "&baromin=%0.2f" % ((bmp180SeaLevel) * 0.2953)
        myURL += "&softwaretype=GillenWx"
        
        # send it
        r = requests.get("https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php", params=myURL)
        #print(r.url)

    def run_loop(self):
        BMP280_Altitude_Meters = 282.85
        logging.info('Temp  Humid Press  DewPt Wind Gust Dir R60 RDay')

        while True:
            try:
                if self._barometer:
                    internal_temp = (self._barometer.read_temperature()*1.8) + 32
                    pressure = self._barometer.read_pressure()
                    altitude = self._barometer.read_altitude()
                    sealevel_pressure = self._barometer.read_sealevel_pressure(BMP280_Altitude_Meters)/1000
                else:
                    internal_temp = 0.00
                    pressure = 0.00
                    altitude = 0.00
                    sealevel_pressure = 0.00
                    self.test_barometric_pressure()

                outside_temperature, outside_humidity, crc_check = self._outdoor_temp.sense()
                # calculate dew_point while still in C
                dew_point =  outside_temperature - ((100.0 - outside_humidity) / 5.0)
                dew_point = ((dew_point * 9.0 / 5.0) + 32.0)                 
                outside_temperature = (outside_temperature * 1.8) + 32
                wind_speed = self._weather_rack.current_wind_speed()/1.6
                wind_gust = self._weather_rack.get_wind_gust()/1.6
                wind_direction = float(self._weather_rack.current_wind_direction())
                wind_direction_voltage = self._weather_rack.current_wind_direction_voltage()
                total_rain_raw = self._weather_rack.get_current_rain_total()
                total_rain = total_rain_raw/25.4
                self._rain_last_60.append(total_rain_raw)
                rain_last_60 = sum(self._rain_last_60)/25.4
                
                if datetime.now().day == self._rain_today_last_day:
                    #print('adding')
                    self._rain_today += total_rain
                else:
                    #print('new')
                    self._rain_today = total_rain
                    self._rain_today_last_day = datetime.now().day

                internal_temp_2 = ((self._internal_humidity.read_temperature()*1.8) + 32)
                internal_humidity = self._internal_humidity.read_humidity()

                readings = {
                    'timestamp' : str(datetime.utcnow().isoformat()),
                    'internal_temp': internal_temp,
                    'internal_humidity': internal_humidity,
                    'outside_temp': outside_temperature,
                    'outside_humidity': outside_humidity,
                    'dew_point': dew_point,
                    'wind_speed': wind_speed,
                    'wind_gust': wind_gust,
                    'pressure': pressure,
                    'wind_direction': wind_direction,
                    'total_rain': total_rain,
                    'rain_last_60': rain_last_60,
                    'rain_today': self._rain_today,
                    'altitude': altitude,
                    'sealevel_pressure': ((sealevel_pressure) * 0.2953),
                    'wind_direction_voltage': wind_direction_voltage,
                    'internal_temp_2': internal_temp_2,
                    'crc_check': crc_check
                }

                logging.info('%.02f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f', outside_temperature, outside_humidity, sealevel_pressure, dew_point, wind_speed, wind_gust, wind_direction, rain_last_60, self._rain_today)

                try:
                    if crc_check:
                        self.sendWeatherUndergroundData(wind_speed, wind_gust, outside_temperature, outside_humidity, wind_direction, rain_last_60, sealevel_pressure, dew_point, self._rain_today)
                except Exception as e:
                    logging.error(e.message)



                # except:
                #     pass
                
                #print readings
                if crc_check:
                    self.send_to_influxdb(readings)
                    # if counter >= :
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
    logging.info('** GillenWx Weather Station System Starting **')
    start_time = time.time()

    def signal_handler(*args):
        """ handles shutting down via signals """
        if station:
            pass

    try:
        signal(SIGTERM, signal_handler)
        signal(SIGHUP, signal_handler)

        station = WeatherStation()   
        station.test_internal_humidity()
        station.test_barometric_pressure()
        station.test_outdoor_temp()
        station.test_real_time_clock()
        station.test_weather_rack()
        logging.info('** Weather Station System Test Complete **')
        station.run_loop()

        # lightning detetor

    except KeyboardInterrupt:
        logging.info('Shutdown requested. Cleaning up...')

    logging.info("Script Finished")
    logging.info("Elapsed Time: %s seconds ", (time.time() - start_time))

if __name__ == "__main__":
    main()
