# bellows

[![Build Status](https://travis-ci.org/zigpy/bellows.svg?branch=master)](https://travis-ci.org/zigpy/bellows)
[![Coverage](https://coveralls.io/repos/github/zigpy/bellows/badge.svg?branch=master)](https://coveralls.io/github/zigpy/bellows?branch=master)

`bellows` is a Python 3 library implemention for the [zigpy](https://github.com/zigpy/zigpy) project to add Zigbee radio support for Silicon Labs EM35x ("Ember") and EFR32 ("Mighty Gecko") based Zigbee coordinator devices using the EZSP (EmberZNet Serial Protocol) interface.

The project can be used as a stand-alone library, however, the main goal of this project is to add native support for EmberZNet Zigbee radio based USB stick devices (a.k.a. "Ember" and "Mighty Gecko" based adapters/dongles/modules) to Home Assistant's built-in ZHA (Zigbee Home Automation) integration component, allowing Home Assistant with such hardware to nativly support direct control of compatible Zigbee devices, such as; Philips HUE, GE, Ledvance, Osram Lightify, Xiaomi/Aqara, IKEA Tradfri, Samsung SmartThings, and many more.

- https://www.home-assistant.io/integrations/zha/

bellows interacts with the Zigbee Network Coprocessor (NCP) with EmberZNet PRO Zigbee coordinator firmware using the EZSP protocol serial interface APIs via via UART for Silicon Labs EM35x and EFR32 Zigbee radio module/chips hardware. The library currectly supports the Silicon Labs EZSP (EmberZNet Serial Protocol) API versions v4/v5/v6/v7/v8 for Silabs older EM35x "Ember" and their newer EFR32 "Mighty Gecko" SoCs using ASH or SPI protocols over a serial interface. The implementation of the SPI protocol assumes that the SPI provides a TTY-like software interface to the application, or is otherwise abstracted via the ZigBeePort interface.

## Hardware requirement

EmberZNet based Zigbee radios using the EZSP protocol (via the [bellows](https://github.com/zigpy/bellows) library for zigpy)
 - [ITEAD Sonoff ZBBridge](https://www.itead.cc/smart-home/sonoff-zbbridge.html) (Note! This first have to be flashed with [Tasmota firmware and EmberZNet firmware](https://www.digiblur.com/2020/07/how-to-use-sonoff-zigbee-bridge-with.html))
 - [Nortek GoControl QuickStick Combo Model HUSBZB-1 (Z-Wave & Zigbee USB Adapter)](https://www.nortekcontrol.com/products/2gig/husbzb-1-gocontrol-quickstick-combo/)
 - [Elelabs Zigbee USB Adapter](https://elelabs.com/products/elelabs_usb_adapter.html)
 - [Elelabs Zigbee Raspberry Pi Shield](https://elelabs.com/products/elelabs_zigbee_shield.html)
 - Telegesis ETRX357USB (Note! This first have to be flashed with other EmberZNet firmware)
 - Telegesis ETRX357USB-LRS (Note! This first have to be flashed with other EmberZNet firmware)
 - Telegesis ETRX357USB-LRS+8M (Note! This first have to be flashed with other EmberZNet firmware)
 
## Firmware requirement

bellows requires that the Zigbee adapter/board/module is pre-flashed/flashed with compatible firmware with EmberZNet PRO Zigbee Stack that uses the standard Silicon Labs EZSP (EmberZNet Serial Protocol) APIs for ASH or SPI protocols over a serial interface.

Silabs did use to provide two main NCP images pre-build with firmware for EM35x, one image supported hardware flow control with a baud rate of 115200 and the other image supported software flow control with a rate of 57600.

Silicon Labs no longer provide pre-build firmware images, so now you have to build and compile firmware with their Simplicity Studio SDK for EmberZNet PRO Zigbee Protocol Stack Software. Simplicity Studio is a free download but building and compiling EmberZNet PRO Zigbee firmware images required that you have the serialnumber of an official Zigbee devkit registered to your Silicon Labs user account.

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
- To configure USB port path for your EZSP serial device, just specify the TTY (serial com) port, example : `/dev/ttyUSB1`
- To configure a networked-adapter like Sonoff ZBBridge enter `socket://adapter-IP>:8888` and use 115200 for the port speed.
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
