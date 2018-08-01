#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import logging
import pprint
import Queue
import time
from collections import deque
from datetime import datetime
from signal import SIGHUP, SIGTERM, signal
from thread import start_new_thread

import click


class WeatherStation(object):
    def __init__(self, settings_file='settings.json'):
        self._barometer = None
        self._outdoor_temp = None
        self._internal_humidity = None
        self._rtc = None
        self._weather_rack = None

        # setup queue for rain totals
        # length is set for 1 reading every 10s for 1 hour
        self._rain_last_60 = deque(maxlen=360)
        self._rain_today = 0
        self._rain_today_last_day = datetime.now().day
        self._threads = []

        # create queues for passing data between threads
        self._bmp280_queue = Queue.Queue()
        self._am2315_queue = Queue.Queue()


        self._current = {
            'timestamp' : str(datetime.utcnow().isoformat()),
            'internal_temp': 0.0,
            'internal_humidity': 0.0,
            'outside_temp': 0.0,
            'outside_humidity': 0.0,
            'dew_point': 0.0,
            'wind_speed': 0.0,
            'wind_gust': 0.0,
            'pressure': 0.0,
            'wind_direction': 0.0,
            'total_rain': 0.0,
            'rain_last_60': 0.0,
            'rain_today': 0.0,
            'altitude': 0.0,
            'sealevel_pressure': 0.0,
            'wind_direction_voltage': 0.0,
            'internal_temp_2': 0.0
        }

        # load settings
        try:
            with open(settings_file) as settings_data:
                self._config = json.load(settings_data)
            self._initialized = True
        except ValueError as val_error:
            logging.error("Unable to process settings data")
            logging.error(val_error.message)
            self._initialized = False

    def check_temp_and_humidity(self, shared_queue):
        temp = 0
        humidity = 0
        while True:
            temp += 1
            humidity += 0.5
            shared_queue.put((temp, humidity))
            time.sleep(6)


    def check_initialized(self):
        return self._initialized

    def test_sensors(self):
        tests_passed = True

        test_result = self.test_outdoor_temp()
        if not test_result:
            tests_passed = False

        return tests_passed


    def test_outdoor_temp(self):
        logging.info('Testing Outdoor Temperature Sensor (AM2315)...')
        try:
            crc_check = -1
            while crc_check <> 0:
                self._outdoor_temp = AM2315(0x5c, "/dev/i2c-1")
                outside_temperature, outside_humidity, crc_check = self._outdoor_temp.sense()
                time.sleep(0.5)
            logging.info("Outside Temperature: %0.1f F", (outside_temperature * 1.8) + 32)
            logging.info("Outside Humidity: %0.1f", outside_humidity)
            logging.info("CRC: %i", crc_check)
            logging.info('Outdoor Temperature Test was Successful (AM2315)')
            return True

        except Exception as exc:
            logging.error('Outdoor Temperature Test Failed')
            return False



    def run_loop(self):
        delay = self._config.get('loop_delay', 30)

        self._threads.append(start_new_thread(self.check_temp_and_humidity,(self._am2315_queue,)))

        while True:
            logging.info('Reporting sensor data...')
            # report here
            while not self._am2315_queue.empty():
                temp_humid = self._am2315_queue.get_nowait()
                if temp_humid:
                    self._current['outside_temp'] = temp_humid[0]
                    self._current['outside_humidity'] = temp_humid[1]
            pprint.pprint(self._current, width=2)
            logging.info('Sleeping for %d seconds', delay)
            time.sleep(delay)

    def shutdown(self):
        return True


def main():
    """ Main function for utility script """
    logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s', level=logging.INFO)
    logging.info('** GillenWx Weather Station System Starting **')
    start_time = time.time()
  
    def signal_handler(*args):
        """ handles shutting down via signals """
        if station:
            station.shutdown()

    try:
        signal(SIGTERM, signal_handler)
        signal(SIGHUP, signal_handler)


        station = WeatherStation()  
        if not station.check_initialized():
            logging.error('Initialization failed. Exiting...')
        else:
            result = station.test_sensors()
            if result:
                station.run_loop()
            else:
                logging.error('Sensor tests failed. Exiting...')

    except KeyboardInterrupt:
        logging.info('Shutdown requested. Cleaning up...')
        station.shutdown()

    logging.info("Script Finished")
    logging.info("Elapsed Time: %s seconds ", (time.time() - start_time))


if __name__ == '__main__':
    main()
