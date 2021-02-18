# bellows

[![Build](https://github.com/zigpy/bellows/workflows/CI/badge.svg?branch=dev)](https://github.com/zigpy/bellows/workflows/CI/badge.svg?branch=dev)
[![Coverage](https://coveralls.io/repos/github/zigpy/bellows/badge.svg?branch=dev)](https://coveralls.io/github/zigpy/bellows?branch=dev)

`bellows` is a Python 3 library implementation for the [zigpy](https://github.com/zigpy/zigpy) project to add Zigbee radio support for Silicon Labs EM35x ("Ember") and EFR32 ("Mighty Gecko") based Zigbee coordinator devices using the EZSP (EmberZNet Serial Protocol) interface.

The project can be used as a stand-alone library, however, the main goal of this project is to add native support for EmberZNet Zigbee radio based USB stick devices (a.k.a. "Ember" and "Mighty Gecko" based adapters/dongles/modules) to Home Assistant's built-in ZHA (Zigbee Home Automation) integration component, allowing Home Assistant with such hardware to nativly support direct control of compatible Zigbee devices, such as; Philips HUE, GE, Ledvance, Osram Lightify, Xiaomi/Aqara, IKEA Tradfri, Samsung SmartThings, and many more.

- https://www.home-assistant.io/integrations/zha/

bellows interacts with the Zigbee Network Coprocessor (NCP) with EmberZNet PRO Zigbee coordinator firmware using the EZSP protocol serial interface APIs via via UART for Silicon Labs EM35x and EFR32 Zigbee radio module/chips hardware. The library currently supports the Silicon Labs EZSP (EmberZNet Serial Protocol) API versions v4/v5/v6/v7/v8 for Silabs older EM35x "Ember" and their newer EFR32 "Mighty Gecko" SoCs using ASH protocols over a serial interface.

## Hardware requirement

EmberZNet based Zigbee radios using the EZSP protocol (via the [bellows](https://github.com/zigpy/bellows) library for zigpy)
 - [ITEAD Sonoff ZBBridge](https://www.itead.cc/smart-home/sonoff-zbbridge.html) (Note! This first have to be flashed with [Tasmota firmware and EmberZNet firmware](https://www.digiblur.com/2020/07/how-to-use-sonoff-zigbee-bridge-with.html))
 - [Nortek GoControl QuickStick Combo Model HUSBZB-1 (Z-Wave & Zigbee Ember 3581 USB Adapter)](https://www.nortekcontrol.com/products/2gig/husbzb-1-gocontrol-quickstick-combo/) (Note! Not a must but recommend [upgrade the EmberZNet NCP application firmware](https://github.com/walthowd/husbzb-firmware))
 - [Elelabs Zigbee USB Adapter](https://elelabs.com/products/elelabs_usb_adapter.html) (Note! Not a must but recommend [upgrade the EmberZNet NCP application firmware](https://github.com/Elelabs/elelabs-zigbee-ezsp-utility))
 - [Elelabs Zigbee Raspberry Pi Shield](https://elelabs.com/products/elelabs_zigbee_shield.html) (Note! Not a must but recommend [upgrade the EmberZNet NCP application firmware](https://github.com/Elelabs/elelabs-zigbee-ezsp-utility))
 - [DEFARO SprutStick Pro (also known as Defaro SprutStick ZigBee 2 Pro)](https://defaro.ru/index.php/product/89-controllers/257-sprutstick-pro)
 - Telegesis ETRX357USB (Note! This first have to be [flashed with other EmberZNet firmware](https://github.com/walthowd/husbzb-firmware))
 - Telegesis ETRX357USB-LRS (Note! This first have to be [flashed with other EmberZNet firmware](https://github.com/walthowd/husbzb-firmware))
 - Telegesis ETRX357USB-LRS+8M (Note! This first have to be [flashed with other EmberZNet firmware](https://github.com/walthowd/husbzb-firmware))
 - [IKEA Billy EZSP](https://github.com/MattWestb/IKEA-TRADFRI-ICC-A-1-Module).
 - [Tuya TYGWZ01 and with labeled (Silvercrest / Lidl) Smart Home Gateway](https://paulbanks.org/projects/lidl-zigbee/).  

### Warning about Zigbee to WiFi bridges

zigpy requires a robust connection between the zigpy radio library and the serial port of the Zigbee radio. With solutions such as _ITEAD Sonoff ZBBridge_ or a Ser2Net serial proxy connection over a WiFi network it is expected to see `NCP entered failed state. Requesting APP controller restart` in the logs. This is a normal part of the operation and indicates there was a drop in communication which caused packet loss to occurred between the zigpy radio library and the Zigbee radio. The use of serial network proxies/bridges/servers over WiFi is therefore not recommended when wanting a stable Zigbee environment with zigpy.

## Firmware requirement

bellows requires that the Zigbee adapter/board/module is pre-flashed/flashed with compatible firmware with EmberZNet PRO Zigbee Stack that uses the standard Silicon Labs EZSP (EmberZNet Serial Protocol) APIs for ASH or SPI protocols over a serial interface.

Silabs used to provide two main NCP images pre-build with firmware for EM35x, one image supported hardware flow control with a baud rate of 115200 and the other image supported software flow control with a rate of 57600.

Silicon Labs no longer provide pre-build firmware images, so now you have to build and compile firmware with their Simplicity Studio SDK for EmberZNet PRO Zigbee Protocol Stack Software. Simplicity Studio is a free download but building and compiling EmberZNet PRO Zigbee firmware images required that you have the serialnumber of an official Zigbee devkit registered to your Silicon Labs user account.

#### Firmware upgrade resources
-  For firmware requirements and recommended firmware see the [Zigpy Wiki](https://github.com/zigpy/zigpy/wiki/Coordinator-Firmware-Updates).
-  [Elelabs EZSP Firmware Update Utility (should work with most EFR32 based Zigbee coordinators with Silicon Labs standard bootloader)](https://github.com/Elelabs/elelabs-zigbee-ezsp-utility).
-  [Docker firmware updater image by walthowd upgrading Nortek/GoControl/Linear HUSBZB-1 and Telegesis ETRX357 Zigbee coordinator adapters](https://github.com/walthowd/husbzb-firmware).

### EmberZNet and EZSP Protocol Version

Silicon Labs does not currently have a consolidated list of changes by EmberZNet SDK or EZSP protocol version. The EZSP additions, changes and deletions have only ever been listed in the "Zigbee EmberZNet Release Notes" (EmberZNet SDK) under the "New items" section as well as the matching UG100 EZSP Reference Guide included with each EmberZNet SDK release.

The largest change was between EZSP v4 (first added in EmberZNet 4.7.2 SDK) and EZSP v5 that was added in EmberZNet 5.9.0 SDK which requires the Legacy Frame ID 0xFF. The change from EZSP v5 to EZSP v6 was done in EmberZNet 6.0.0 SDK. The change from EZSP v6 to EZSP v7 was in EmberZNet 6.4.0 SDK. EmberZNet 6.7.0 SDK added EZSP v8 (and Secure EZSP Protocol Version 2).

Perhaps more important to know today is that EZSP v5, v6 and v7 (EmberZNet 6.6.x.x) use the same framing format, but EmberZNet 6.7.x.x/EZSP v8 introduced new framing format and expanded command id field from 8 bits to 16 bits.

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
## Configuration

### Port configuration
- To configure USB port path for your EZSP serial device, just specify the TTY (serial com) port, example : `/dev/ttyUSB1`
- To configure a networked-adapter like Sonoff ZBBridge enter `socket://adapter-IP>:8888` and use 115200 for the port speed.
- It is worth noting that EM3588 devices that have an embedded USB core will likely work with any baud rate, where dongles using external USB interface (eg CP2102 used with an EM3581) will likely require a specific baud rate. Currently there are two main NCP images - one that supports hardware flow control with a baud rate of 115200, and one that supports software flow control with a rate of 57600.

### NVRAM Backup and restore

Warning! Please note that this is a highly experimental feature! Theoretically this allows backing up and restoring NCP state between the hardware version.

NVRAM backup can be performed to migrate between different radio hardware as long as they **based on the same chip**. Anything else will not work. If this is done between different hardwares, the EUI64 is going to be different on the new hardware meaning the binding tables on all the devices are going to be wrong.

```console
To export TC config, see bellows backup --help usually it is just bellows backup > your-backup-file.txt. 
The backup contains your network key, so you probably should keep that file secure.
To import, see bellows restore --backup-file your-backup-file.txt
```

Note! The restoration does not restore NCP children and relies on children just to find a new parent. You either have to reconfigure all the devices (recommended so the bindings are updated) or alternatively you could override the EUI64 on the new hardware, essentially producing a clone. Be very careful if you decide to go with the latter route. You can change the EUI64 only once and once you set it it is impossible to change it without a specialized hardware (SWD programmer).

Tested migrations:

 - To-Do

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
