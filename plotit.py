#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import json
import matplotlib.pyplot as plt

raw_lines = []
crc_check = []
load_power = []
shunt_voltage_1 = []
shunt_voltage_2 = []
altitude = []
battery_voltage = []
internal_temp = []
battery_power = []
solar_power = []
solar_current = []
timestamp = []
load_current = []
bus_voltage_1 = []
pressure = []
bus_voltage_3 = []
bus_voltage_2 = []
sealevel_pressure = []
load_voltage = []
battery_charge = []
solar_voltage = []
outside_temp = []
outside_humidity = []
battery_current = []


def standard_plot(data, title, ylabel, file_name):
    plt.plot(data)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig('plot_' + file_name + '.png')
    plt.close()

with open('weather.log.sample', 'r') as data_file:
    for line in data_file:
        raw_lines.append(line)


for line in raw_lines:
    parsed = json.loads(line)
    crc_check.append(parsed['crc_check'])
    load_power.append(parsed['load_power'])
    shunt_voltage_1.append(parsed['shunt_voltage_1'])
    shunt_voltage_2.append(parsed['shunt_voltage_2'])
    altitude.append(parsed['altitude'])
    battery_voltage.append(parsed['battery_voltage'])
    internal_temp.append(parsed['internal_temp'])
    battery_power.append(parsed['battery_power'])
    solar_power.append(parsed['solar_power'])
    solar_current.append(parsed['solar_current'])
    timestamp.append(parsed['timestamp'])
    load_current.append(parsed['load_current'])
    bus_voltage_1.append(parsed['bus_voltage_1'])
    pressure.append(parsed['pressure'])
    bus_voltage_3.append(parsed['bus_voltage_3'])
    bus_voltage_2.append(parsed['bus_voltage_2'])
    sealevel_pressure.append(parsed['sealevel_pressure'])
    load_voltage.append(parsed['load_voltage'])
    battery_charge.append(parsed['battery_charge'])
    solar_voltage.append(parsed['solar_voltage'])
    outside_temp.append(parsed['outside_temp'])
    outside_humidity.append(parsed['outside_humidity'])
    battery_current.append(parsed['battery_current'])


print len(raw_lines)

# now let's plot something
standard_plot(crc_check, 'CRC Check', 'some numbers', 'crc_check')
standard_plot(outside_temp, 'Outside Temp', 'some numbers', 'outside_temp')
standard_plot(outside_humidity, 'Outside Humidity', 'some numbers', 'outside_humidity')

standard_plot(pressure, 'Pressure', 'some numbers', 'pressure')
standard_plot(sealevel_pressure, 'Sea Level Pressure', 'some numbers', 'sealevel_pressure')
standard_plot(altitude, 'Altitude', 'some numbers', 'altitude')
standard_plot(internal_temp, 'Internal Temp', 'some numbers', 'internal_temp')

standard_plot(load_power, 'Load Power', 'some numbers', 'load_power')
standard_plot(load_current, 'Load Current', 'some numbers', 'load_current')
standard_plot(load_voltage, 'Load Voltage', 'some numbers', 'load_voltage')

standard_plot(battery_voltage, 'Battery Voltage', 'some numbers', 'battery_voltage')
standard_plot(battery_power, 'Battery Power', 'some numbers', 'battery_power')
standard_plot(battery_charge, 'Battery Charge', 'some numbers', 'battery_charge')
standard_plot(battery_current, 'Battery Current', 'some numbers', 'battery_current')

standard_plot(solar_power, 'Solar Power', 'some numbers', 'solar_power')
standard_plot(solar_current, 'Solar Current', 'some numbers', 'solar_current')
standard_plot(solar_voltage, 'Solar Voltage', 'some numbers', 'solar_voltage')

standard_plot(bus_voltage_1, 'Bus Voltage 1', 'some numbers', 'bus_voltage_1')
standard_plot(bus_voltage_3, 'Bus Voltage 3', 'some numbers', 'bus_voltage_3')
standard_plot(bus_voltage_2, 'Bus Voltage 2', 'some numbers', 'bus_voltage_2')
standard_plot(shunt_voltage_1, 'Shunt Voltage 1', 'some numbers', 'shunt_voltage_1')
standard_plot(shunt_voltage_2, 'Shunt Voltage 2', 'some numbers', 'shunt_voltage_2')


