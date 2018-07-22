#! /usr/bin/python
# -*- coding: utf-8 -*-

''' 
Sends weather data to Weather Underground

Modified version of code originally created by SwitchDoc Labs September, 2016
- modified November 2016 - Luksmann - changed to request library to improve reliability

'''

import sys
import requests

def sendWeatherUndergroundData(currentWindSpeed, outsideTemperature, outsideHumidity, currentWindDirection, rain60Minutes, bmp180SeaLevel): 

	# https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=KCASANFR5&PASSWORD=XXXXXX&dateutc=2000-01-01+10%3A32%3A35&winddir=230&windspeedmph=12&windgustmph=12&tempf=70&rainin=0&baromin=29.1&dewptf=68.2&humidity=90&weather=&clouds=&softwaretype=vws%20versionxx&action=updateraw	

	# build the URL
	myURL = "ID="+"KTNKNOXV230"
	myURL += "&PASSWORD="+"o4c21o1u"
	myURL += "&dateutc=now"

	# now weather station variables

	#myURL += "&winddir=%i" % currentWindDirection
	#print "cws=|",currentWindSpeed

	myURL += "&windspeedmph=%0.2f" % (currentWindSpeed/1.6) 

	myURL += "&humidity=%i" % outsideHumidity
	myURL += "&tempf=%0.2f" % outsideTemperature

   	#dewpoint =  outsideTemperature - ((100.0 - outsideHumidity) / 5.0);
	#dewpointf = ((dewpoint*9.0/5.0)+32.0)
	#myURL += "&dewptf=%0.2f" % dewpointf 

	myURL += "&rainin=%0.2f" % ((rain60Minutes)/25.4)
	myURL += "&baromin=%0.2f" % ((bmp180SeaLevel) * 0.2953)

	myURL += "&software=GillenWx"

	print "myURL=", myURL
	#send it
	r = requests.get("https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php", params=myURL)

	print(r.url)
	print(r.text)
	print "GET sent"


def main():
    current_wind_speed = 12.0
    outside_temp = 83.1
    outside_humidity = 56.7
    current_wind_dir = 'NW'
    rain_60 = 0.0

    sendWeatherUndergroundData(current_wind_speed, outside_temp, outside_humidity, current_wind_dir, rain_60)

if __name__ == '__main__':
    main()
