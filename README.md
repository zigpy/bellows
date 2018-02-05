# bellows

[![Build Status](https://travis-ci.org/zigpy/bellows.svg?branch=master)](https://travis-ci.org/zigpy/bellows)
[![Coverage](https://coveralls.io/repos/github/zigpy/bellows/badge.svg?branch=master)](https://coveralls.io/github/zigpy/bellows?branch=master)

`bellows` is a Python 3 project to implement support for EmberZNet devices
using the EZSP protocol.

The goal is to use this project to add support for the ZigBee Network
Coprocessor (NCP) in devices like the [Linear/Nortek/GoControl HubZ/QuickStick
Combo (HUSBZB-1)][HubZ] device to [Home Assistant][hass].

[Hubz]: http://www.gocontrol.com/detail.php?productId=6
[hass]: https://home-assistant.io/

## Status

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

## Reference documentation

 * EZSP UART Gateway Protocol Reference:
   https://www.silabs.com/Support%20Documents/TechnicalDocs/UG101.pdf
 * EZSP Reference Guide:
   http://www.silabs.com/Support%20Documents/TechnicalDocs/UG100-EZSPReferenceGuide.pdf
