#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import requests

BASE_URL = 'https://dweet.io'
THING_NAME = 'argo_weather'

def send_dweet(payload):
    url = '{0}/dweet/for/{1}'.format(BASE_URL, THING_NAME)
    data = json.dumps(payload)
    headers = {'Content-type': 'application/json'}

    request_func = getattr(requests, 'post')
    response = request_func(url, data=data, headers=headers)

    # raise an exception if request is not successful
    print response.status_code
    # if not response.status_code == requests.codes.ok:
    #     print'HTTP {0} response'.format(response.status_code)
    #     # raise DweepyError('HTTP {0} response'.format(response.status_code))
    response_json = response.json()
    if response_json['this'] == 'failed':
        print response_json['because']
        # raise DweepyError(response_json['because'])
    return response_json['with']



# my_data = '{"crc_check": 0, "load_power": 0.702336, "shunt_voltage_1": 0.0, "shunt_voltage_2": 0.0, "altitude": 255.713153117349, "battery_voltage": 4.208, "internal_temp": 76.51400000000001, "battery_power": 0.0, "solar_power": 0.0, "solar_current": 0.0, "timestamp": "2017-08-14T06:22:20.417934", "load_current": 141.6, "bus_voltage_1": 4.208, "pressure": 98291.0, "bus_voltage_3": 4.96, "bus_voltage_2": 0.064, "sealevel_pressure": 98289.0, "load_voltage": 4.96, "battery_charge": 100.0, "solar_voltage": 0.064, "outside_temp": 71.96000137329102, "outside_humidity": 90.0999984741211, "battery_current": 0.0}'

# my_data_parsed = json.loads(my_data)
# send_dweet(my_data_parsed)


with open('weather.log.sample', 'r') as data_file:
    for line in data_file:
        if len(line) > 3:
            my_data = json.loads(line)
            send_dweet(my_data)
            time.sleep(10)
