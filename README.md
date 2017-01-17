# bellows

`bellows` is a Python 3 project to implement ZigBee support for EmberZNet
devices using the EZSP protocol.

The goal is to use this project to add support for the ZigBee Network
Coprocessor (NCP) in devices like the [Linear/Nortek/GoControl HubZ/QuickStick
Combo (HUSBZB-1)][HubZ] device to [Home Assistant][hass].

[Hubz]: http://www.gocontrol.com/detail.php?productId=6
[hass]: https://home-assistant.io/

## Status

This project is in early stages, so even items marked as implemented may be
drastically changed, 

 * implemented: EZSP UART Gateway Protocol
 * implemented: EZSP application protocol
 * implemented: CLI wrapping basic ZigBee network operations (eg, scanning and
   forming a network)

No work towards implementation of the application layers of ZigBee - that is,
ZHA, ZLL or other application profiles is done yet.

## Reference documentation

 * EZSP UART Gateway Protocol Reference:
   https://www.silabs.com/Support%20Documents/TechnicalDocs/UG101.pdf
 * EZSP Reference Guide:
   http://www.silabs.com/Support%20Documents/TechnicalDocs/UG100-EZSPReferenceGuide.pdf
