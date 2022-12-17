# Weatherstation Version 2

After having run the prior version of our weatherstation for over five years, a few of the sensors were no longer functioning properly, and I decided to rework some things.

## Design Choices

We started out with a handful of things that we wanted to *remove*.

- Solar Panels: We started out the last version with solar panels and an attempt to operate fully via solar power. That lasted about 1-2 months. Evidently, our little corner of East Tennessee doesn't get enough sun for a great enough part of the day over enough consecutive days to operate consistently. Additionally, the panels I had (four of them) were not the highest quality and severly degraded over time. I eventually ran an extension cord and set up shore power.

- Sunlight / IR / UV Sensor

- all of the battery charging/solr charging boards

- RPi Zero

Our new design, made some intentional choices:

- Power Over Ethernet (POE): During the intervening years, we have deployed an upgraded home network infrastructure which includes POE support. This has been great for a number of devices and, in the case of the weatherstation, would allow me to fully reboot the device (sometimes sensors seemed to 'lose their head') from the network management interface (rather than crawling up into the attic and disconnecting/reapplying power).

- "Normal" RPi: Due to supply chain issues at the moment, I cannot obtain a RPi 4 for a reasonable cost, but I have a number of RPi 3B+ boards lying around and I'm going to utilize one of them.

- Simple is better

I started out with the most recent, *lite* version of the RPi OS: `2022-09-22-raspios-bullseye-armhf-lite.img.xz`

## Preparing the device

Downloaded the rpimager from the raspberry pi website

ran it, used the settings cog to enable ssh, set the hostname, password, etc.

Selected the Rasbperry Pi OS Lite (32 bit) and wrote to the SD.

plugged in and waited awhile (need to let auto resize, ssh key generation, reboots, etc. occur)

- give it a full couple of minutes
- connect via ssh
- copy keys over via `ssh-copy-id`
- update/upgrade all existing packages
- reboot
- use sudo apt full-upgrade (ensures all dependencies and firmware are updated)
- sudo apt clean
- ran sudo raspi-config
  - enabled screen blanking
  - enabled I2c
  - rebooted and ensured everything was up/happy
- shut down
- disconnected all cables
- installed RPi POE Hat
- connected network cable and confirmed that the device powered up properly and was reachable over the network
- went into network management system and disabled POE for that port to confirm that it would properly turn off the device
  - this worked fine, but took 10 seconds for the command to get pushed out to the switch and to turn off the device
  - installed the CZH-LABS Breakout board
  - re-connected the ethernet cable
  - turned back on POE power via NMS

- connected the external temp/humidity sensor
  - http://adafru.it/5182
  - AM2315C
    - voltage 2.2v - 5.5v
    - Range 0-100% RH; -40-80 degree C
    - Accuracy +/- 2% RH; +/- 0.3 degree C
    - Digital output
    - Red: VCC
    - Black: Gnd
    - White: SCL
    - Yellow: SDA
  - sudo apt install i2c-tools
  - i2cdetect -y 1

```shell
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- 38 -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```







**NOTE**: I did all of these steps from a Mac - so you may need to adjust things slightly based on your OS

brew install xz
xz -d 022-09-22-raspios-bullseye-armhf-lite.img.xz

diskutil list

diskutil unmountDisk disk4

sudo dd if=2022-09-22-raspios-bullseye-armhf-lite.img of=/dev/disk4 bs=1m conv=fsync status=progress

diskutil eject disk4

physically remove and replug the device

cp headless/ssh /Volumes/boot
cp headless/config.txt /Volumes/boot

Connect to power, connect to switch

NOTE: Even though I had the POE hat installed, I needed to directly apply shore power for the initial setup to get software and firmware updated (to support the POE hat).

