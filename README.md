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

## Release packages available via PyPI

Packages of tagged versions are also released via PyPI
  - https://pypi.org/project/bellows-homeassistant/

## Reference documentation

 * EZSP UART Gateway Protocol Reference:
   https://www.silabs.com/Support%20Documents/TechnicalDocs/UG101.pdf
 * EZSP Reference Guide:
   http://www.silabs.com/Support%20Documents/TechnicalDocs/UG100-EZSPReferenceGuide.pdf

## How to contribute

If you are looking to make a contribution to this project we suggest that you follow the steps in these guides:
- https://github.com/firstcontributions/first-contributions/blob/master/README.md
- https://github.com/firstcontributions/first-contributions/blob/master/github-desktop-tutorial.md

Some developers might also be interested in receiving donations in the form of hardware such as Zigbee modules or devices, and even if such donations are most often donated with no strings attached it could in many cases help the developers motivation and indirect improve the development of this project.

## Related projects

### Zigpy
[Zvigpy](https://github.com/zigpy/zigpy)** is **[Zigbee protocol stack](https://en.wikipedia.org/wiki/Zigbee)** integration project to implement the **[Zigbee Home Automation](https://www.zigbee.org/)** standard as a Python 3 library. Zigbee Home Automation integration with zigpy allows you to connect one of many off-the-shelf Zigbee adapters using one of the available Zigbee radio library modules compatible with zigpy to control Zigbee based devices. There is currently support for controlling Zigbee device types such as binary sensors (e.g., motion and door sensors), sensors (e.g., temperature sensors), lightbulbs, switches, and fans. A working implementation of zigbe exist in **[Home Assistant](https://www.home-assistant.io)** (Python based open source home automation software) as part of its **[ZHA component](https://www.home-assistant.io/components/zha/)**

### ZHA Device Handlers
ZHA deviation handling in Home Assistant relies on on the third-party [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) project. Zigbee devices that deviate from or do not fully conform to the standard specifications set by the [Zigbee Alliance](https://www.zigbee.org) may require the development of custom [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) (ZHA custom quirks handler implementation) to for all their functions to work properly with the ZHA component in Home Assistant. These ZHA Device Handlers for Home Assistant can thus be used to parse custom messages to and from non-compliant Zigbee devices. The custom quirks implementations for zigpy implemented as ZHA Device Handlers for Home Assistant are a similar concept to that of [Hub-connected Device Handlers for the SmartThings Classics platform](https://docs.smartthings.com/en/latest/device-type-developers-guide/) as well as that of [Zigbee-Shepherd Converters as used by Zigbee2mqtt](https://www.zigbee2mqtt.io/how_tos/how_to_support_new_devices.html), meaning they are each virtual representations of a physical device that expose additional functionality that is not provided out-of-the-box by the existing integration between these platforms.

### ZHA Map
[zha-map](https://github.com/zha-ng/zha-map) project allow Home Assistant to build a ZHA network topology map.

### zha-network-visualization-card
[zha-network-visualization-card](https://github.com/dmulcahey/zha-network-visualization-card) is a custom Lovelace element for visualizing the ZHA Zigbee network in Home Assistant.

### ZHA Network Card
[zha-network-card](https://github.com/dmulcahey/zha-network-card) is a custom Lovelace card that displays ZHA network and device information in Home Assistant
