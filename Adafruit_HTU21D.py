# Copyright (c) 2015 Massimo Gaggero
# Author: Massimo Gaggero
import logging
import math
import time

# HTU21D default address.
HTU21D_I2CADDR = 0x40

# Operating Modes
HTU21D_HOLDMASTER = 0x00
HTU21D_NOHOLDMASTER = 0x10

# HTU21D Commands
HTU21D_TRIGGERTEMPCMD = 0xF3 # 0xE3  # Trigger Temperature Measurement
HTU21D_TRIGGERHUMIDITYCMD = 0xE5  # Trigger Humidity Measurement
HTU21D_WRITEUSERCMD = 0xE6  # Write user register
HTU21D_READUSERCMD = 0xE7  # Read user register
HTU21D_SOFTRESETCMD = 0xFE  # Soft reset

# HTU21D Constants for Dew Point calculation
HTU21D_A = 8.1332
HTU21D_B = 1762.39
HTU21D_C = 235.66


class HTU21DException(Exception):
    pass


class HTU21D(object):
    def __init__(self, mode=HTU21D_HOLDMASTER, address=HTU21D_I2CADDR, i2c=None, **kwargs):
        self._logger = logging.getLogger('Adafruit_HTU21D.HTU21D')
        print "h1"
        # Check that mode is valid.
        if mode not in [HTU21D_HOLDMASTER, HTU21D_NOHOLDMASTER]:
            raise ValueError('Unexpected mode value {0}.  Set mode to one of HTU21D_HOLDMASTER, HTU21D_NOHOLDMASTER'.format(mode))
        self._mode = mode
        # Create I2C device.
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)

        # reset the device
        print 'here!!!'
        self._device.writeRaw8(HTU21D_SOFTRESETCMD) # Soft reset
        time.sleep(.1)
        print 'here too'

    def crc_check(self, msb, lsb, crc):
        remainder = ((msb << 8) | lsb) << 8
        remainder |= crc
        divsor = 0x988000
        for i in range(0, 16):
            if remainder & 1 << (23 - i):
                remainder ^= divsor
            divsor >>= 1
        if remainder == 0:
            return True
        else:
            return False

    def read_raw_temp(self):
        """Reads the raw temperature from the sensor."""
        print('d1')
        self._device.writeRaw8(HTU21D_TRIGGERTEMPCMD)
        print('d2')
        time.sleep(.05)
        print('d3')
        #msb, lsb, chsum = self._device.readList(HTU21D_TRIGGERTEMPCMD, 3)
        msb = self._device.readRaw8()
        print('d3.1')
        lsb = self._device.readRaw8()
        print('d3.2')
        chsum = self._device.readRaw8()

        #msb, lsb, chsum = self._device.readList(HTU21D_TRIGGERTEMPCMD, 3)
        print('d4')
        if self.crc_check(msb, lsb, chsum) is False:
            raise HTU21DException("CRC Exception")
        raw = (msb << 8) + lsb
        raw &= 0xFFFC
        self._logger.info('Raw temp 0x{0:X} ({1})'.format(raw & 0xFFFF, raw))
        return raw

    def read_raw_humidity(self):
        """Reads the raw relative humidity from the sensor."""
        msb, lsb, chsum = self._device.readList(HTU21D_TRIGGERHUMIDITYCMD, 3)
        if self.crc_check(msb, lsb, chsum) is False:
            raise HTU21DException("CRC Exception")
        raw = (msb << 8) + lsb
        raw &= 0xFFFC
        self._logger.info('Raw relative humidity 0x{0:04X} ({1})'.format(raw & 0xFFFF, raw))
        return raw

    def read_temperature(self):
        """Gets the temperature in degrees celsius."""
        print ('h2.1')
        raw = self.read_raw_temp()
        print ('h2.2')
        temp = float(raw)/65536 * 175.72
        print ('h2.3')
        temp -= 46.85
        print ('h2.4')
        self._logger.info('Temperature {0:.2f} C'.format(temp))
        print ('h2.5')
        return temp

    def read_humidity(self):
        """Gets the relative humidity."""
        raw = self.read_raw_humidity()
        rh = float(raw)/65536 * 125
        rh -= 6
        self._logger.info('Relative Humidity {0:.2f} %'.format(rh))
        return rh

    def read_dewpoint(self):
        """Calculates the dew point temperature."""
        # Calculation taken straight from datasheet.
        ppressure = self.read_partialpressure()
        humidity = self.read_humidity()
        den = math.log10(humidity * ppressure / 100) - HTU21D_A
        dew = -(HTU21D_B / den + HTU21D_C)
        self._logger.info('Dew Point {0:.2f} C'.format(dew))
        return dew

    def read_partialpressure(self):
        """Calculate the partial pressure in mmHg at ambient temperature."""
        Tamb = self.read_temperature()
        exp = HTU21D_B / (Tamb + HTU21D_C)
        exp = HTU21D_A - exp
        pp = 10 ** exp
        self._logger.info('Partial Pressure {0:.2f} mmHg'.format(pp))
        return pp