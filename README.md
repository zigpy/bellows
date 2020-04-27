# bellows

[![Build Status](https://travis-ci.org/zigpy/bellows.svg?branch=master)](https://travis-ci.org/zigpy/bellows)
[![Coverage](https://coveralls.io/repos/github/zigpy/bellows/badge.svg?branch=master)](https://coveralls.io/github/zigpy/bellows?branch=master)

`bellows` is a Python 3 project to implement support for EmberZNet devices using the EZSP protocol.

The goal is to use this project to add support for the ZigBee Network
Coprocessor (NCP) in devices like the [Linear/Nortek/GoControl HubZ/QuickStick
Combo (HUSBZB-1)][HubZ] device to [Home Assistant][hass].

[Hubz]: http://www.gocontrol.com/detail.php?productId=6
[hass]: https://home-assistant.io/

## Compatible hardware

EmberZNet based Zigbee radios using the EZSP protocol (via the [bellows](https://github.com/zigpy/bellows) library for zigpy)
 - [Nortek GoControl QuickStick Combo Model HUSBZB-1 (Z-Wave & Zigbee USB Adapter)](https://www.nortekcontrol.com/products/2gig/husbzb-1-gocontrol-quickstick-combo/)
 - [Elelabs Zigbee USB Adapter](https://elelabs.com/products/elelabs_usb_adapter.html)
 - [Elelabs Zigbee Raspberry Pi Shield](https://elelabs.com/products/elelabs_zigbee_shield.html)
 - Telegesis ETRX357USB (Note! This first have to be flashed with other EmberZNet firmware)
 - Telegesis ETRX357USB-LRS (Note! This first have to be flashed with other EmberZNet firmware)
 - Telegesis ETRX357USB-LRS+8M (Note! This first have to be flashed with other EmberZNet firmware)

## Project status

This project is in early stages, so it is likely that APIs will change.

Currently implemented features are:

 * EZSP UART Gateway Protocol
 * EZSP application protocol
 * CLI wrapping basic ZigBee network operations (eg, scanning and forming a
   network)
 * ZDO functionality (with CLI)
 * ZCL functionality (with CLI)
 * An application framework with device state persistence

An example use of the CLI:

```
$ export EZSP_DEVICE=/dev/ttyUSB1
$ bellows devices
Device:
  NWK: 0x1ee4
  IEEE: 00:0d:6f:00:05:7d:2d:34
  Endpoints:
    1: profile=0x104, device_type=None, clusters=[0, 1, 3, 32, 1026, 1280, 2821]
    2: profile=0xc2df, device_type=None, clusters=[0, 1, 3, 2821]
Device:
  NWK: 0x64a6
  IEEE: d0:52:a8:00:e0:be:00:05
  Endpoints:
    1: profile=0x104, device_type=None, clusters=[0]
    2: profile=0xfc01, device_type=None, clusters=[]
$ bellows zdo 00:0d:6f:00:05:7d:2d:34 get_endpoint 1
<SimpleDescriptor endpoint=1 profile=260 device_type=1026 device_version=0 input_clusters=[0, 1, 3, 32, 1026, 1280, 2821] output_clusters=[25]>
$ bellows zcl 00:0d:6f:00:05:7d:2d:34 1 1026 read_attribute 0
0=1806
```

## Port configuration
- To configure usb port path for your EZSP serial device, just specify the TTY (serial com) port, example : `/dev/ttyUSB1`
- It is worth noting that EM3588 devices that have an embedded USB core will likely work with any baud rate, where dongles using external USB interface (eg CP2102 used with an EM3581) will likely require a specific baud rate. Currently there are two main NCP images - one that supports hardware flow control with a baud rate of 115200, and one that supports software flow control with a rate of 57600.

## Testing new releases

Testing a new release of the bellows library before it is released in Home Assistant.

If you are using Supervised Home Assistant (formerly known as the Hassio/Hass.io distro):
- Add https://github.com/home-assistant/hassio-addons-development as "add-on" repository
- Install "Custom deps deployment" addon
- Update config like: 
  ```
  pypi:
    - bellows==0.16.0
  apk: []
  ```
  where 0.16.0 is the new version
- Start the addon

If you are instead using some custom python installation of Home Assistant then do this:
- Activate your python virtual env
- Update package with ``pip``
  ```
  pip install bellows==0.16.0

## Release packages available via PyPI

New packages of tagged versions are also released via the "bellows" project on PyPI
  - https://pypi.org/project/bellows/

Older packages of tagged versions are still available on the "bellows-homeassistant" project on PyPI
  - https://pypi.org/project/bellows-homeassistant/

## Reference documentation

 * EZSP UART Gateway Protocol Reference:
   https://www.silabs.com/Support%20Documents/TechnicalDocs/UG101.pdf
 * EZSP Reference Guide:
   http://www.silabs.com/Support%20Documents/TechnicalDocs/UG100-EZSPReferenceGuide.pdf
 * EZSP UART Host Interfacing Reference Guide: https://www.silabs.com/documents/public/application-notes/an706-ezsp-uart-host-interfacing-guide.pdf
  * Silicon Labs forum https://www.silabs.com/community/wireless/zigbee-and-thread/forum

## How to contribute

If you are looking to make a contribution to this project we suggest that you follow the steps in these guides:
- https://github.com/firstcontributions/first-contributions/blob/master/README.md
- https://github.com/firstcontributions/first-contributions/blob/master/github-desktop-tutorial.md

Some developers might also be interested in receiving donations in the form of hardware such as Zigbee modules or devices, and even if such donations are most often donated with no strings attached it could in many cases help the developers motivation and indirect improve the development of this project.
