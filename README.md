# Home Weather Station
This is the code repository supporting the weather station my son and I built as a summer project. The hardware for this project is mostly from the [SwitchDoc Labs Weather Pi project](http://www.switchdoc.com/2016/12/tutorial-part-1-building-a-solar-powered-raspberry-pi-weather-station-groveweatherpi/). The code in this repository is a hodge podge... much of it is hand-rolled or custom, though it leverages a number of other projects in part, or at least as inspiration. I've tried to list these projects below:

- [Software for the new GroveWeatherPI Solar Powered Weather Station with Grove Connections](https://github.com/switchdoclabs/SDL_Pi_GroveWeatherPi)
- [Drivers for Grove Sunlight Sensor based on SI1145](https://github.com/switchdoclabs/SDL_Pi_SI1145)


## Parts List:




## Sensors:

### Grove Sunlight / IR / UV I2C Sensor
The Grove Sunlight and UV I2C sensor can monitor sunlight intensity, IR intensity and UV intensity.  All in one sensor. The sensor is a multi-channel digital light sensor, which has the ability to detect UV-light, visible light and infrared light.

This device is based on SI1145, a new sensor from SiLabs. The Si1145 is a low-power, reflectance-based, infrared proximity, UV index and ambient light sensor with I2C digital interface and programmable-event interrupt output. This device offers excellent performance under a wide dynamic range and a variety of light sources including direct sunlight.

The Si1145 appears as ID 0x3C (60) on I2C Bus 1


### I2C 4 Channel I2C Bus Mux
This appears as ID 0x49 (73) on the RPI's I2C Bus 1

This is the TCA9545 and the drivers come with a test script - `testSDL_Pi_TCA9545.py1` that was run and verified it was operating properly.


### Bus 0
+ 0x3c - SSD1306 OLED Screen
- 0x40 - HTU21D-F Humidity Sensor
- 0x48 - ADS1115 Analog to Digital Converter
+ 0x5c - AM2315 Outdoor Temp / Humidity
+ 0x68 - DS3231 Real Time Clock
+ 0x73 - TCA9545 I2C 4 Channel I2C Bus Mux
+ 0x77 - BMP280 Barometric Pressure

- ??? 0x56 - ATC EEPROM ???
- ??? 0x50 - FRAM non-volatile storage ???

### Bus 1
- 0x03 - Embedded Adventures Lightning Detector
+ 0x73 - TCA9545 I2C 4 Channel I2C Bus Mux

### Bus 2
+ 0x40 - INA3221 3 Channel Voltage / Current Monitor
- 0x48 - ADS1015 SunAir Plus
+ 0x73 - TCA9545 I2C 4 Channel I2C Bus Mux

### Bus 3
+ 0x73 - TCA9545 I2C 4 Channel I2C Bus Mux


> why does the temp look like x5c and x57?



## Test Script
There is a test script (`test_all.py`) that simply walks through each of the devices, tests it, and reports the status of the device. It is assumed that everything is connected properly as there are not many air bags. The test process is as follows:

- TCA9545 / I2C 4-Channel Mux
  - Enables the mux on channel 0
  - Switches to channel 2.
  - Assuming no errors, reports success.
- SSD1306 OLED Screen:
  - Ensure I2C Mux has channel 0 enabled
  - clears the screen
  - displays a cat picture
  - holds for 10s
  - clears the screen
  - Assuming no errors, report success
- HTU21D-F Humidity Sensor
  - Ensure I2C Mux has channel 0 enabled



```Shell
-----------BUS 0-------------------
tca9545 control register B3-B0 = 0x1
ignore Interrupts if INT3' - INT0' not connected
tca9545 control register Interrupts = 0x0
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
40: 40 -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- 57 -- -- -- -- -- -- -- --
60: 60 -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
70: -- -- -- 73 -- -- -- 77

-----------------------------------

-----------BUS 1-------------------
tca9545 control register B3-B0 = 0x2
ignore Interrupts if INT3' - INT0' not connected
tca9545 control register Interrupts = 0x0
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: 60 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- 73 -- -- -- --

-----------------------------------

-----------BUS 2-------------------
tca9545 control register B3-B0 = 0x4
ignore Interrupts if INT3' - INT0' not connected
tca9545 control register Interrupts = 0x0
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: 40 -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: 60 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- 73 -- -- -- --

-----------------------------------

-----------BUS 3-------------------
tca9545 control register B3-B0 = 0x8
ignore Interrupts if INT3' - INT0' not connected
tca9545 control register Interrupts = 0x0
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: 60 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- 73 -- -- -- --

-----------------------------------
```
