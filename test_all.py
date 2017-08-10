#!/usr/bin/env python
# -*- coding:utf-8 -*-

""" Simple test script to check for the presence of all sensors """
import logging


import SDL_Pi_TCA9545

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT)

# setup our constants
TCA9545_ADDRESS      =                (0x73)  # 1110011 (A0+A1=VDD)
TCA9545_REG_CONFIG   =                (0x00)  # config register (R/W)
TCA9545_CONFIG_BUS0  =                (0x01)  # 1 = enable, 0 = disable 
TCA9545_CONFIG_BUS1  =                (0x02)  # 1 = enable, 0 = disable 
TCA9545_CONFIG_BUS2  =                (0x04)  # 1 = enable, 0 = disable 
TCA9545_CONFIG_BUS3  =                (0x08)  # 1 = enable, 0 = disable 


try:
    tca9545 = SDL_Pi_TCA9545.SDL_Pi_TCA9545(addr=TCA9545_ADDRESS, bus_enable=TCA9545_CONFIG_BUS0)
    tca9545.write_control_register(TCA9545_CONFIG_BUS2)
    logging.info("I2C Mux is present and operating normally (TCA9545)")

except:
    logging.error("I2C Mux tests Failed")
