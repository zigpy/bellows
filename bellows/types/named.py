from __future__ import annotations

import logging

import zigpy.types as ztypes
import zigpy.zdo.types as zdo_t

from . import basic

LOGGER = logging.getLogger(__name__)

Channels = ztypes.Channels
EmberEUI64 = ztypes.EUI64
EUI64 = ztypes.EUI64
NWK = ztypes.NWK
BroadcastAddress = ztypes.BroadcastAddress


class NcpResetCode(basic.enum8):
    # Reset and Error Codes for NCP
    RESET_UNKNOWN_REASON = 0x00
    RESET_EXTERNAL = 0x01
    RESET_POWER_ON = 0x02
    RESET_WATCHDOG = 0x03
    RESET_ASSERT = 0x06
    RESET_BOOTLOADER = 0x09
    RESET_SOFTWARE = 0x0B
    ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT = 0x51
    ERROR_UNKNOWN_EM3XX_ERROR = 0x80


class ExtendedPanId(ztypes.ExtendedPanId):
    """Extended PAN ID."""


class EmberNodeId(basic.uint16_t, repr="hex"):
    # 16-bit ZigBee network address.
    pass


class EmberPanId(basic.uint16_t, repr="hex"):
    # 802.15.4 PAN ID.
    pass


class EmberMulticastId(basic.uint16_t, repr="hex"):
    # 16-bit ZigBee multicast group identifier.
    pass


class EmberGpSecurityLevel(basic.uint8_t):
    # The security level of the GPD.
    pass


class EmberGpKeyType(basic.uint8_t):
    # The type of security key to use for the GPD.
    pass


class Bool(basic.enum8):
    # Boolean type with values true and false.

    false = 0x00  # An alias for zero, used for clarity.
    true = 0x01  # An alias for one, used for clarity.


class EzspExtendedValueId(basic.enum8):
    # Identifies a value based on specified characteristics. Each set of characteristics
    # is unique to that value and is specified during the call to get the extended
    # value.

    # The flags field associated with the specified endpoint.
    EXTENDED_VALUE_ENDPOINT_FLAGS = 0x00
    # This is the reason for the node to leave the network as well as the device that
    # told it to leave. The leave reason is the 1st byte of the value while the node
    # ID is the 2nd and 3rd byte. If the leave was caused due to an API call rather than
    # an over the air message, the node ID will be UNKNOWN_NODE_ID (0xFFFD).
    EXTENDED_VALUE_LAST_LEAVE_REASON = 0x01
    # This number of bytes of overhead required in the network frame for source routing
    # to a particular destination.
    EXTENDED_VALUE_GET_SOURCE_ROUTE_OVERHEAD = 0x02


class EzspEndpointFlags(basic.enum16):
    # Flags associated with the endpoint data configured on the NCP.

    # Indicates that the endpoint is disabled and NOT discoverable via ZDO.
    ENDPOINT_DISABLED = 0x00
    # Indicates that the endpoint is enabled and discoverable via ZDO.
    ENDPOINT_ENABLED = 0x01


class EmberConfigTxPowerMode(basic.enum16):
    # Values for CONFIG_TX_POWER_MODE.

    # Normal power mode and bi-directional RF transmitter output.
    TX_POWER_MODE_DEFAULT = 0x00
    # Enable boost power mode. This is a high performance radio mode which
    # offers increased receive sensitivity and transmit power at the cost of an
    # increase in power consumption.
    TX_POWER_MODE_BOOST = 0x01
    # Enable the alternate transmitter output. This allows for simplified
    # connection to an external power amplifier via the RF_TX_ALT_P and
    # RF_TX_ALT_N pins.  TX_POWER_MODE_BOOST_AND_ALTERNATE 0x03 Enable both
    # boost mode and the alternate transmitter output.
    TX_POWER_MODE_ALTERNATE = 0x02
    # Enable both boost mode and the alternate transmitter output.
    TX_POWER_MODE_BOOST_AND_ALTERNATE = 0x03


class EzspMfgTokenId(basic.enum8):
    # Manufacturing token IDs used by ezspGetMfgToken().

    # Custom version (2 bytes).
    MFG_CUSTOM_VERSION = 0x00
    # Manufacturing string (16 bytes).
    MFG_STRING = 0x01
    # Board name (16 bytes).
    MFG_BOARD_NAME = 0x02
    # Manufacturing ID (2 bytes).
    MFG_MANUF_ID = 0x03
    # Radio configuration (2 bytes).
    MFG_PHY_CONFIG = 0x04
    # Bootload AES key (16 bytes).
    MFG_BOOTLOAD_AES_KEY = 0x05
    # ASH configuration (40 bytes).
    MFG_ASH_CONFIG = 0x06
    # EZSP storage (8 bytes).
    MFG_STORAGE = 0x07
    # Radio calibration data (64 bytes). 4 bytes are stored for each of the 16
    # channels. This token is not stored in the Flash Information Area. It is
    # updated by the stack each time a calibration is performed.
    STACK_CAL_DATA = 0x08
    # Certificate Based Key Exchange (CBKE) data (92 bytes).
    MFG_CBKE_DATA = 0x09
    # Installation code (20 bytes).
    MFG_INSTALLATION_CODE = 0x0A
    # Radio channel filter calibration data (1 byte). This token is not stored
    # in the Flash Information Area. It is updated by the stack each time a
    # calibration is performed.
    STACK_CAL_FILTER = 0x0B
    # Custom EUI64 MAC address (8 bytes).
    MFG_CUSTOM_EUI_64 = 0x0C
    # CTUNE value (2 byte).
    MFG_CTUNE = 0x0D


class EzspStatus(basic.enum8):
    # Status values used by EZSP.

    # Success.
    SUCCESS = 0x00
    # Fatal error.
    SPI_ERR_FATAL = 0x10
    # The Response frame of the current transaction indicates the NCP has
    # reset.
    SPI_ERR_NCP_RESET = 0x11
    # The NCP is reporting that the Command frame of the current transaction is
    # oversized (the length byte is too large).
    SPI_ERR_OVERSIZED_FRAME = 0x12
    # The Response frame of the current transaction indicates the previous
    # transaction was aborted (nSSEL deasserted too soon).
    SPI_ERR_ABORTED_TRANSACTION = 0x13
    # The Response frame of the current transaction indicates the frame
    # terminator is missing from the Command frame.
    SPI_ERR_MISSING_FRAME_TERMINATOR = 0x14
    # The NCP has not provided a Response within the time limit defined by
    # WAIT_SECTION_TIMEOUT.
    SPI_ERR_WAIT_SECTION_TIMEOUT = 0x15
    # The Response frame from the NCP is missing the frame terminator.
    SPI_ERR_NO_FRAME_TERMINATOR = 0x16
    # The Host attempted to send an oversized Command (the length byte is too
    # large) and the AVR's spi-protocol.c blocked the transmission.
    SPI_ERR_COMMAND_OVERSIZED = 0x17
    # The NCP attempted to send an oversized Response (the length byte is too
    # large) and the AVR's spi-protocol.c blocked the reception.
    SPI_ERR_RESPONSE_OVERSIZED = 0x18
    # The Host has sent the Command and is still waiting for the NCP to send a
    # Response.
    SPI_WAITING_FOR_RESPONSE = 0x19
    # The NCP has not asserted nHOST_INT within the time limit defined by
    # WAKE_HANDSHAKE_TIMEOUT.
    SPI_ERR_HANDSHAKE_TIMEOUT = 0x1A
    # The NCP has not asserted nHOST_INT after an NCP reset within the time
    # limit defined by STARTUP_TIMEOUT.
    SPI_ERR_STARTUP_TIMEOUT = 0x1B
    # The Host attempted to verify the SPI Protocol activity and version
    # number, and the verification failed.
    SPI_ERR_STARTUP_FAIL = 0x1C
    # The Host has sent a command with a SPI Byte that is unsupported by the
    # current mode the NCP is operating in.
    SPI_ERR_UNSUPPORTED_SPI_COMMAND = 0x1D
    # Operation not yet complete.
    ASH_IN_PROGRESS = 0x20
    # Fatal error detected by host.
    HOST_FATAL_ERROR = 0x21
    # Fatal error detected by NCP.
    ASH_NCP_FATAL_ERROR = 0x22
    # Tried to send DATA frame too long.
    DATA_FRAME_TOO_LONG = 0x23
    # Tried to send DATA frame too short.
    DATA_FRAME_TOO_SHORT = 0x24
    # No space for tx'ed DATA frame.
    NO_TX_SPACE = 0x25
    # No space for rec'd DATA frame.
    NO_RX_SPACE = 0x26
    # No receive data available.
    NO_RX_DATA = 0x27
    # Not in Connected state.
    NOT_CONNECTED = 0x28
    # The NCP received a command before the EZSP version had been set.
    ERROR_VERSION_NOT_SET = 0x30
    # The NCP received a command containing an unsupported frame ID.
    ERROR_INVALID_FRAME_ID = 0x31
    # The direction flag in the frame control field was incorrect.
    ERROR_WRONG_DIRECTION = 0x32
    # The truncated flag in the frame control field was set, indicating there
    # was not enough memory available to complete the response or that the
    # response would have exceeded the maximum EZSP frame length.
    ERROR_TRUNCATED = 0x33
    # The overflow flag in the frame control field was set, indicating one or
    # more callbacks occurred since the previous response and there was not
    # enough memory available to report them to the Host.
    ERROR_OVERFLOW = 0x34
    # Insufficient memory was available.
    ERROR_OUT_OF_MEMORY = 0x35
    # The value was out of bounds.
    ERROR_INVALID_VALUE = 0x36
    # The configuration id was not recognized.
    ERROR_INVALID_ID = 0x37
    # Configuration values can no longer be modified.
    ERROR_INVALID_CALL = 0x38
    # The NCP failed to respond to a command.
    ERROR_NO_RESPONSE = 0x39
    # The length of the command exceeded the maximum EZSP frame length.
    ERROR_COMMAND_TOO_LONG = 0x40
    # The UART receive queue was full causing a callback response to be dropped.
    ERROR_QUEUE_FULL = 0x41
    # The command has been filtered out by NCP.
    ERROR_COMMAND_FILTERED = 0x42
    # EZSP Security Key is already set
    ERROR_SECURITY_KEY_ALREADY_SET = 0x43
    # EZSP Security Type is invalid
    ERROR_SECURITY_TYPE_INVALID = 0x44
    # EZSP Security Parameters are invalid
    ERROR_SECURITY_PARAMETERS_INVALID = 0x45
    # EZSP Security Parameters are already set
    ERROR_SECURITY_PARAMETERS_ALREADY_SET = 0x46
    # EZSP Security Key is not set
    ERROR_SECURITY_KEY_NOT_SET = 0x47
    # EZSP Security Parameters are not set
    ERROR_SECURITY_PARAMETERS_NOT_SET = 0x48
    # Received frame with unsupported control byte
    ERROR_UNSUPPORTED_CONTROL = 0x49
    # Received frame is insecure, when security is established
    ERROR_UNSECURE_FRAME = 0x4A
    # Incompatible ASH version
    ASH_ERROR_VERSION = 0x50
    # Exceeded max ACK timeouts
    ASH_ERROR_TIMEOUTS = 0x51
    # Timed out waiting for RSTACK
    ASH_ERROR_RESET_FAIL = 0x52
    # Unexpected ncp reset
    ASH_ERROR_NCP_RESET = 0x53
    # Serial port initialization failed
    ERROR_SERIAL_INIT = 0x54
    # Invalid ncp processor type
    ASH_ERROR_NCP_TYPE = 0x55
    # Invalid ncp reset method
    ASH_ERROR_RESET_METHOD = 0x56
    # XON/XOFF not supported by host driver
    ASH_ERROR_XON_XOFF = 0x57
    # ASH protocol started
    ASH_STARTED = 0x70
    # ASH protocol connected
    ASH_CONNECTED = 0x71
    # ASH protocol disconnected
    ASH_DISCONNECTED = 0x72
    # Timer expired waiting for ack
    ASH_ACK_TIMEOUT = 0x73
    # Frame in progress cancelled
    ASH_CANCELLED = 0x74
    # Received frame out of sequence
    ASH_OUT_OF_SEQUENCE = 0x75
    # Received frame with CRC error
    ASH_BAD_CRC = 0x76
    # Received frame with comm error
    ASH_COMM_ERROR = 0x77
    # Received frame with bad ackNum
    ASH_BAD_ACKNUM = 0x78
    # Received frame shorter than minimum
    ASH_TOO_SHORT = 0x79
    # Received frame longer than maximum
    ASH_TOO_LONG = 0x7A
    # Received frame with illegal control byte
    ASH_BAD_CONTROL = 0x7B
    # Received frame with illegal length for its type
    ASH_BAD_LENGTH = 0x7C
    # Received ASH Ack
    ASH_ACK_RECEIVED = 0x7D
    # Sent ASH Ack
    ASH_ACK_SENT = 0x7E
    # Received ASH Nak
    ASH_NAK_RECEIVED = 0x7F
    # Sent ASH Nak
    ASH_NAK_SENT = 0x80
    # Received ASH RST
    ASH_RST_RECEIVED = 0x81
    # Sent ASH RST
    ASH_RST_SENT = 0x82
    # ASH Status
    ASH_STATUS = 0x83
    # ASH TX
    ASH_TX = 0x84
    # ASH RX
    ASH_RX = 0x85
    # Failed to connect to CPC daemon or failed to open CPC endpoint
    CPC_ERROR_INIT = 0x86
    # No reset or error
    NO_ERROR = 0xFF


class EmberStatus(basic.enum8):
    # Return type for stack functions.

    # The generic 'no error' message.
    SUCCESS = 0x00
    # The generic 'fatal error' message.
    ERR_FATAL = 0x01
    # An invalid value was passed as an argument to a function
    BAD_ARGUMENT = 0x02
    # The requested information was not found.
    NOT_FOUND = 0x03
    # The manufacturing and stack token format in nonvolatile memory is
    # different than what the stack expects (returned at initialization).
    EEPROM_MFG_STACK_VERSION_MISMATCH = 0x04
    # The static memory definitions in ember-staticmemory.h are incompatible
    # with this stack version.
    INCOMPATIBLE_STATIC_MEMORY_DEFINITIONS = 0x05
    # The manufacturing token format in non-volatile memory is different than
    # what the stack expects (returned at initialization).
    EEPROM_MFG_VERSION_MISMATCH = 0x06
    # The stack token format in non-volatile memory is different than what the
    # stack expects (returned at initialization).
    EEPROM_STACK_VERSION_MISMATCH = 0x07
    # There are no more buffers.
    NO_BUFFERS = 0x18
    # Packet is dropped by packet-handoff callbacks.
    PACKET_HANDOFF_DROP_PACKET = 0x19
    # Specified an invalid baud rate.
    SERIAL_INVALID_BAUD_RATE = 0x20
    # Specified an invalid serial port.
    SERIAL_INVALID_PORT = 0x21
    # Tried to send too much data.
    SERIAL_TX_OVERFLOW = 0x22
    # There was not enough space to store a received character and the
    # character was dropped.
    SERIAL_RX_OVERFLOW = 0x23
    # Detected a UART framing error.
    SERIAL_RX_FRAME_ERROR = 0x24
    # Detected a UART parity error.
    SERIAL_RX_PARITY_ERROR = 0x25
    # There is no received data to process.
    SERIAL_RX_EMPTY = 0x26
    # The receive interrupt was not handled in time, and a character was
    # dropped.
    SERIAL_RX_OVERRUN_ERROR = 0x27
    # The MAC transmit queue is full.
    MAC_TRANSMIT_QUEUE_FULL = 0x39
    # MAC header FCR error on receive.
    MAC_UNKNOWN_HEADER_TYPE = 0x3A
    # MAC ACK header received.
    MAC_ACK_HEADER_TYPE = 0x3B
    # The MAC can't complete this task because it is scanning.
    MAC_SCANNING = 0x3D
    # No pending data exists for device doing a data poll.
    MAC_NO_DATA = 0x31
    # Attempt to scan when we are joined to a network.
    MAC_JOINED_NETWORK = 0x32
    # Scan duration must be 0 to 14 inclusive. Attempt was made to scan with an
    # incorrect duration value.
    MAC_BAD_SCAN_DURATION = 0x33
    # emberStartScan was called with an incorrect scan type.
    MAC_INCORRECT_SCAN_TYPE = 0x34
    # emberStartScan was called with an invalid channel mask.
    MAC_INVALID_CHANNEL_MASK = 0x35
    # Failed to scan current channel because we were unable to transmit the
    # relevant MAC command.
    MAC_COMMAND_TRANSMIT_FAILURE = 0x36
    # We expected to receive an ACK following the transmission, but the MAC
    # level ACK was never received.
    MAC_NO_ACK_RECEIVED = 0x40
    # MAC failed to transmit a message because it could not successfully perform a radio
    # network switch.
    MAC_RADIO_NETWORK_SWITCH_FAILED = 0x41
    # Indirect data message timed out before polled.
    MAC_INDIRECT_TIMEOUT = 0x42
    # The Simulated EEPROM is telling the application that there is at least
    # one flash page to be erased.  The GREEN status means the current page has
    # not filled above the ERASE_CRITICAL_THRESHOLD.  The application should
    # call the function halSimEepromErasePage when it can to erase a page.
    SIM_EEPROM_ERASE_PAGE_GREEN = 0x43
    # The Simulated EEPROM is telling the application that there is at least
    # one flash page to be erased.  The RED status means the current page has
    # filled above the ERASE_CRITICAL_THRESHOLD. Due to the shrinking
    # availability of write space, there is a danger of data loss. The
    # application must call the function halSimEepromErasePage as soon as
    # possible to erase a page.
    SIM_EEPROM_ERASE_PAGE_RED = 0x44
    # The Simulated EEPROM has run out of room to write any new data and the
    # data trying to be set has been lost. This error code is the result of
    # ignoring the SIM_EEPROM_ERASE_PAGE_RED error code.  The application must
    # call the function halSimEepromErasePage to make room for any further
    # calls to set a token.
    SIM_EEPROM_FULL = 0x45
    # A fatal error has occurred while trying to write data to the Flash. The
    # target memory attempting to be programmed is already programmed. The
    # flash write routines were asked to flip a bit from a 0 to 1, which is
    # physically impossible and the write was therefore inhibited. The data in
    # the flash cannot be trusted after this error.
    ERR_FLASH_WRITE_INHIBITED = 0x46
    # A fatal error has occurred while trying to write data to the Flash and
    # the write verification has failed. The data in the flash cannot be
    # trusted after this error, and it is possible this error is the result of
    # exceeding the life cycles of the flash.
    ERR_FLASH_VERIFY_FAILED = 0x47
    # Attempt 1 to initialize the Simulated EEPROM has failed. This failure
    # means the information already stored in Flash (or a lack thereof), is
    # fatally incompatible with the token information compiled into the code
    # image being run.
    SIM_EEPROM_INIT_1_FAILED = 0x48
    # Attempt 2 to initialize the Simulated EEPROM has failed. This failure
    # means Attempt 1 failed, and the token system failed to properly reload
    # default tokens and reset the Simulated EEPROM.
    SIM_EEPROM_INIT_2_FAILED = 0x49
    # Attempt 3 to initialize the Simulated EEPROM has failed. This failure
    # means one or both of the tokens TOKEN_MFG_NVDATA_VERSION or
    # TOKEN_STACK_NVDATA_VERSION were incorrect and the token system failed to
    # properly reload default tokens and reset the Simulated EEPROM.
    SIM_EEPROM_INIT_3_FAILED = 0x4A
    # A fatal error has occurred while trying to write data to the flash,
    # possibly due to write protection or an invalid address. The data in the
    # flash cannot be trusted after this error, and it is possible this error
    # is the result of exceeding the life cycles of the flash.
    ERR_FLASH_PROG_FAIL = 0x4B
    # A fatal error has occurred while trying to erase flash, possibly due to
    # write protection. The data in the flash cannot be trusted after this
    # error, and it is possible this error is the result of exceeding the life
    # cycles of the flash.
    ERR_FLASH_ERASE_FAIL = 0x4C
    # The Simulated EEPROM is repairing itself. While there's nothing for an app to do
    # when the SimEE is going to repair itself (SimEE has to be fully functional for
    # the rest of the system to work), alert the application to the fact that repair is
    # occurring.  There are debugging scenarios where an app might want to know that
    # repair is happening, such as monitoring frequency.
    SIM_EEPROM_REPAIRING = 0x4D
    # The bootloader received an invalid message (failed attempt to go into
    # bootloader).
    ERR_BOOTLOADER_TRAP_TABLE_BAD = 0x58
    # Bootloader received an invalid message (failed attempt to go into
    # bootloader).
    ERR_BOOTLOADER_TRAP_UNKNOWN = 0x59
    # The bootloader cannot complete the bootload operation because either an
    # image was not found or the image exceeded memory bounds.
    ERR_BOOTLOADER_NO_IMAGE = 0x5A
    # The APS layer attempted to send or deliver a message, but it failed.
    DELIVERY_FAILED = 0x66
    # This binding index is out of range of the current binding table.
    BINDING_INDEX_OUT_OF_RANGE = 0x69
    # This address table index is out of range for the current address table.
    ADDRESS_TABLE_INDEX_OUT_OF_RANGE = 0x6A
    # An invalid binding table index was given to a function.
    INVALID_BINDING_INDEX = 0x6C
    # The API call is not allowed given the current state of the stack.
    INVALID_CALL = 0x70
    # The link cost to a node is not known.
    COST_NOT_KNOWN = 0x71
    # The maximum number of in-flight messages (i.e.
    # APS_UNICAST_MESSAGE_COUNT) has been reached.
    MAX_MESSAGE_LIMIT_REACHED = 0x72
    # The message to be transmitted is too big to fit into a single over-the-
    # air packet.
    MESSAGE_TOO_LONG = 0x74
    # The application is trying to delete or overwrite a binding that is in
    # use.
    BINDING_IS_ACTIVE = 0x75
    # The application is trying to overwrite an address table entry that is in
    # use.
    ADDRESS_TABLE_ENTRY_IS_ACTIVE = 0x76
    # An attempt was made to transmit during the suspend period.
    TRANSMISSION_SUSPENDED = 0x77
    # Security match.
    MATCH = 0x78
    # Drop frame.
    DROP_FRAME = 0x79
    # TODO: no docs
    PASS_UNPROCESSED = 0x7A
    # TODO: no docs
    TX_THEN_DROP = 0x7B
    # TODO: no docs
    NO_SECURITY = 0x7C
    # TODO: no docs
    COUNTER_FAILURE = 0x7D
    # TODO: no docs
    AUTH_FAILURE = 0x7E
    # TODO: no docs
    UNPROCESSED = 0x7F
    # Conversion is complete.
    ADC_CONVERSION_DONE = 0x80
    # Conversion cannot be done because a request is being processed.
    ADC_CONVERSION_BUSY = 0x81
    # Conversion is deferred until the current request has been processed.
    ADC_CONVERSION_DEFERRED = 0x82
    # No results are pending.
    ADC_NO_CONVERSION_PENDING = 0x84
    # Sleeping (for a duration) has been abnormally interrupted and exited
    # prematurely.
    SLEEP_INTERRUPTED = 0x85
    # The transmit attempt failed because the radio scheduler could not find a slot to
    # transmit this packet in or a higher priority event interrupted it.
    PHY_TX_SCHED_FAIL = 0x87
    # The transmit hardware buffer underflowed.
    PHY_TX_UNDERFLOW = 0x88
    # The transmit hardware did not finish transmitting a packet.
    PHY_TX_INCOMPLETE = 0x89
    # An unsupported channel setting was specified.
    PHY_INVALID_CHANNEL = 0x8A
    # An unsupported power setting was specified.
    PHY_INVALID_POWER = 0x8B
    # The packet cannot be transmitted because the physical MAC layer is
    # currently transmitting a packet.  (This is used for the MAC backoff
    # algorithm.) PHY_TX_CCA_FAIL 0x8D The transmit attempt failed because all
    # CCA attempts indicated that the channel was busy
    PHY_TX_BUSY = 0x8C
    # The transmit attempt failed because all CCA attempts indicated that the channel
    # was busy
    PHY_TX_CCA_FAIL = 0x8D
    # The transmit attempt was blocked from going over the air. Typically this is due to
    # the Radio Hold Off (RHO) or Coexistence plugins as they can prevent transmits
    # based on external signals.
    PHY_TX_BLOCKED = 0x8E
    # The expected ACK was received after the last transmission.
    PHY_ACK_RECEIVED = 0x8F
    # The stack software has completed initialization and is ready to send and
    # receive packets over the air.
    NETWORK_UP = 0x90
    # The network is not operating.
    NETWORK_DOWN = 0x91
    # An attempt to join a network failed.
    JOIN_FAILED = 0x94
    # After moving, a mobile node's attempt to re-establish contact with the
    # network failed.
    MOVE_FAILED = 0x96
    # An attempt to join as a router failed due to a ZigBee versus ZigBee Pro
    # incompatibility. ZigBee devices joining ZigBee Pro networks (or vice
    # versa) must join as End Devices, not Routers.
    CANNOT_JOIN_AS_ROUTER = 0x98
    # The local node ID has changed. The application can obtain the new node ID
    # by calling emberGetNodeId().
    NODE_ID_CHANGED = 0x99
    # The local PAN ID has changed. The application can obtain the new PAN ID
    # by calling emberGetPanId().
    PAN_ID_CHANGED = 0x9A
    # The channel has changed.
    CHANNEL_CHANGED = 0x9B
    # The network has been opened for joining.
    NETWORK_OPENED = 0x9C
    # The network has been closed for joining.
    NETWORK_CLOSED = 0x9D
    # An attempt to join or rejoin the network failed because no router beacons
    # could be heard by the joining node.
    NO_BEACONS = 0xAB
    # An attempt was made to join a Secured Network using a pre-configured key,
    # but the Trust Center sent back a Network Key in-the-clear when an
    # encrypted Network Key was required.
    RECEIVED_KEY_IN_THE_CLEAR = 0xAC
    # An attempt was made to join a Secured Network, but the device did not
    # receive a Network Key.
    NO_NETWORK_KEY_RECEIVED = 0xAD
    # After a device joined a Secured Network, a Link Key was requested but no
    # response was ever received.
    NO_LINK_KEY_RECEIVED = 0xAE
    # An attempt was made to join a Secured Network without a pre-configured
    # key, but the Trust Center sent encrypted data using a pre-configured key.
    PRECONFIGURED_KEY_REQUIRED = 0xAF
    # The node has not joined a network.
    NOT_JOINED = 0x93
    # The chosen security level (the value of SECURITY_LEVEL) is not supported
    # by the stack.
    INVALID_SECURITY_LEVEL = 0x95
    # A message cannot be sent because the network is currently overloaded.
    NETWORK_BUSY = 0xA1
    # The application tried to send a message using an endpoint that it has not
    # defined.
    INVALID_ENDPOINT = 0xA3
    # The application tried to use a binding that has been remotely modified
    # and the change has not yet been reported to the application.
    BINDING_HAS_CHANGED = 0xA4
    # An attempt to generate random bytes failed because of insufficient random
    # data from the radio.
    INSUFFICIENT_RANDOM_DATA = 0xA5
    # There was an error in trying to encrypt at the APS Level. This could
    # result from either an inability to determine the long address of the
    # recipient from the short address (no entry in the binding table) or there
    # is no link key entry in the table associated with the destination, or
    # there was a failure to load the correct key into the encryption core.
    APS_ENCRYPTION_ERROR = 0xA6
    # There was an attempt to form a network using commercial security without setting
    # the Trust Center master key first.
    TRUST_CENTER_MASTER_KEY_NOT_SET = 0xA7
    # There was an attempt to form or join a network with security without
    # calling emberSetInitialSecurityState() first.
    SECURITY_STATE_NOT_SET = 0xA8
    # There was an attempt to set an entry in the key table using an invalid
    # long address. An entry cannot be set using either the local device's or
    # Trust Center's IEEE address. Or an entry already exists in the table with
    # the same IEEE address. An Address of all zeros or all F's are not valid
    # addresses in 802.15.4.
    KEY_TABLE_INVALID_ADDRESS = 0xB3
    # There was an attempt to set a security configuration that is not valid
    # given the other security settings.
    SECURITY_CONFIGURATION_INVALID = 0xB7
    # There was an attempt to broadcast a key switch too quickly after
    # broadcasting the next network key. The Trust Center must wait at least a
    # period equal to the broadcast timeout so that all routers have a chance
    # to receive the broadcast of the new network key.
    TOO_SOON_FOR_SWITCH_KEY = 0xB8
    # The message could not be sent because the link key corresponding to the
    # destination is not authorized for use in APS data messages. APS Commands
    # (sent by the stack) are allowed. To use it for encryption of APS data
    # messages it must be authorized using a key agreement protocol (such as
    # CBKE).
    KEY_NOT_AUTHORIZED = 0xBB
    # The security data provided was not valid, or an integrity check failed.
    SECURITY_DATA_INVALID = 0xBD
    # A ZigBee route error command frame was received indicating that a source
    # routed message from this node failed en route.
    SOURCE_ROUTE_FAILURE = 0xA9
    # A ZigBee route error command frame was received indicating that a message
    # sent to this node along a many-to-one route failed en route. The route
    # error frame was delivered by an ad-hoc search for a functioning route.
    MANY_TO_ONE_ROUTE_FAILURE = 0xAA
    # A critical and fatal error indicating that the version of the stack
    # trying to run does not match with the chip it is running on. The software
    # (stack) on the chip must be replaced with software that is compatible
    # with the chip.
    STACK_AND_HARDWARE_MISMATCH = 0xB0
    # An index was passed into the function that was larger than the valid
    # range.
    INDEX_OUT_OF_RANGE = 0xB1
    # The passed key data is not valid. A key of all zeros or all F's are reserved
    # values and cannot be used.
    KEY_INVALID = 0xB2
    # There are no empty entries left in the table.
    TABLE_FULL = 0xB4
    # The requested table entry has been erased and contains no valid data.
    TABLE_ENTRY_ERASED = 0xB6
    # The requested function cannot be executed because the library that
    # contains the necessary functionality is not present.
    LIBRARY_NOT_PRESENT = 0xB5
    # The received signature corresponding to the message that was passed to the CBKE
    # Library failed verification and is not valid.
    SIGNATURE_VERIFY_FAILURE = 0xB9
    # The stack accepted the command and is currently processing the request.
    # The results will be returned via an appropriate handler.
    OPERATION_IN_PROGRESS = 0xBA
    # The EUI of the Trust center has changed due to a successful rejoin. The device may
    # need to perform other authentication to verify the new TC is authorized to take
    # over.
    TRUST_CENTER_EUI_HAS_CHANGED = 0xBC
    # An error occurred when trying to encrypt at the APS Level. To APS encrypt an
    # outgoing packet, the sender needs to know the EUI64 of the destination. This
    # error occurs because the EUI64 of the destination can't be determined from the
    # short address (no entry in the neighbor, child, binding or address tables).
    IEEE_ADDRESS_DISCOVERY_IN_PROGRESS = 0xBE
    # NVM3 is telling the application that the initialization was aborted as no valid
    # NVM3 page was found.
    NVM3_TOKEN_NO_VALID_PAGES = 0xC0
    # NVM3 is telling the application that the initialization was aborted as the NVM3
    # instance was already opened with other parameters.
    NVM3_ERR_OPENED_WITH_OTHER_PARAMETERS = 0xC1
    # NVM3 is telling the application that the initialization was aborted as the NVM3
    # instance is not aligned properly in memory.
    NVM3_ERR_ALIGNMENT_INVALID = 0xC2
    # NVM3 is telling the application that the initialization was aborted as the size of
    # the NVM3 instance is too small.
    NVM3_ERR_SIZE_TOO_SMALL = 0xC3
    # NVM3 is telling the application that the initialization was aborted as the NVM3
    # page size is not supported.
    NVM3_ERR_PAGE_SIZE_NOT_SUPPORTED = 0xC4
    # NVM3 is telling the application that there was an error initializing some of the
    # tokens.
    NVM3_ERR_TOKEN_INIT = 0xC5
    # NVM3 is telling the application there has been an error when attempting to upgrade
    # SimEE tokens.
    NVM3_ERR_UPGRADE = 0xC6
    # NVM3 is telling the application that there has been an unknown error.
    NVM3_ERR_UNKNOWN = 0xC7
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_0 = 0xF0
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_1 = 0xF1
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_2 = 0xF2
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_3 = 0xF3
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_4 = 0xF4
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_5 = 0xF5
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_6 = 0xF6
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_7 = 0xF7
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_8 = 0xF8
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_9 = 0xF9
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_10 = 0xFA
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_11 = 0xFB
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_12 = 0xFC
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_13 = 0xFD
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_14 = 0xFE
    # This error is reserved for customer application use.  This will never be
    # returned from any portion of the network stack or HAL.
    APPLICATION_ERROR_15 = 0xFF


class EmberEventUnits(basic.enum8):
    # Either marks an event as inactive or specifies the units for the event
    # execution time.

    # The event is not scheduled to run.
    EVENT_INACTIVE = 0x00
    # The execution time is in approximate milliseconds.
    EVENT_MS_TIME = 0x01
    # The execution time is in 'binary' quarter seconds (256 approximate milliseconds
    # each).
    EVENT_QS_TIME = 0x02
    # The execution time is in 'binary' minutes (65536 approximate milliseconds each).
    EVENT_MINUTE_TIME = 0x03
    # The event is scheduled to run at the earliest opportunity.
    EVENT_ZERO_DELAY = 0x04


class EmberNodeType(basic.enum8):
    # The type of the node.

    # Device is not joined.
    UNKNOWN_DEVICE = 0x00
    # Will relay messages and can act as a parent to other nodes.
    COORDINATOR = 0x01
    # Will relay messages and can act as a parent to other nodes.
    ROUTER = 0x02
    # Communicates only with its parent and will not relay messages.
    END_DEVICE = 0x03
    # An end device whose radio can be turned off to save power. The
    # application must poll to receive messages.
    SLEEPY_END_DEVICE = 0x04
    # A sleepy end device that can move through the network.
    MOBILE_END_DEVICE = 0x05
    # RF4CE target node.
    RF4CE_TARGET = 0x06
    # RF4CE controller node.
    RF4CE_CONTROLLER = 0x07
    # Device is not joined or no network is formed.
    UNKNOWN_NODE_TYPE = 0xFF

    @property
    def zdo_logical_type(self) -> zdo_t.LogicalType:
        """Convert EmberNodetype to ZDO Node descriptor logical type."""
        if self in (
            EmberNodeType.COORDINATOR,
            EmberNodeType.END_DEVICE,
            EmberNodeType.ROUTER,
        ):
            return zdo_t.LogicalType(self - 1)

        return zdo_t.LogicalType(7)


class EmberNetworkStatus(basic.enum8):
    # The possible join states for a node.

    # The node is not associated with a network in any way.
    NO_NETWORK = 0x00
    # The node is currently attempting to join a network.
    JOINING_NETWORK = 0x01
    # The node is joined to a network.
    JOINED_NETWORK = 0x02
    # The node is an end device joined to a network but its parent is not
    # responding.
    JOINED_NETWORK_NO_PARENT = 0x03
    # The node is in the process of leaving its current network.
    LEAVING_NETWORK = 0x04


class EmberIncomingMessageType(basic.enum8):
    # Incoming message types.

    # Unicast.
    INCOMING_UNICAST = 0x00
    # Unicast reply.
    INCOMING_UNICAST_REPLY = 0x01
    # Multicast.
    INCOMING_MULTICAST = 0x02
    # Multicast sent by the local device.
    INCOMING_MULTICAST_LOOPBACK = 0x03
    # Broadcast.
    INCOMING_BROADCAST = 0x04
    # Broadcast sent by the local device.
    INCOMING_BROADCAST_LOOPBACK = 0x05
    # Many to one route request.
    INCOMING_MANY_TO_ONE_ROUTE_REQUEST = 0x06


class EmberOutgoingMessageType(basic.enum8):
    # Outgoing message types.

    # Unicast sent directly to an EmberNodeId.
    OUTGOING_DIRECT = 0x00
    # Unicast sent using an entry in the address table.
    OUTGOING_VIA_ADDRESS_TABLE = 0x01
    # Unicast sent using an entry in the binding table.
    OUTGOING_VIA_BINDING = 0x02
    # Multicast message. This value is passed to emberMessageSentHandler()
    # only. It may not be passed to emberSendUnicast().
    OUTGOING_MULTICAST = 0x03
    # Aliased multicast message. This value is passed to emberMessageSentHandler() only.
    # It may not be passed to emberSendUnicast().
    OUTGOING_MULTICAST_WITH_ALIAS = 0x04
    # Aliased Broadcast message. This value is passed to emberMessageSentHandler() only.
    # It may not be passed to emberSendUnicast().
    OUTGOING_BROADCAST_WITH_ALIAS = 0x05
    # Broadcast message. This value is passed to emberMessageSentHandler()
    # only. It may not be passed to emberSendUnicast().
    OUTGOING_BROADCAST = 0x06


class EmberMacPassthroughType(basic.bitmap8):
    # MAC passthrough message type flags.

    # No MAC passthrough messages.
    MAC_PASSTHROUGH_NONE = 0x00
    # SE InterPAN messages.
    MAC_PASSTHROUGH_SE_INTERPAN = 0x01
    # Legacy EmberNet messages.
    MAC_PASSTHROUGH_EMBERNET = 0x02
    # Legacy EmberNet messages filtered by their source address.
    MAC_PASSTHROUGH_EMBERNET_SOURCE = 0x04
    MAC_PASSTHROUGH_APPLICATION = 0x08
    MAC_PASSTHROUGH_CUSTOM = 0x10
    MAC_PASSTHROUGH_INTERNAL_GP = 0x40
    MAC_PASSTHROUGH_INTERNAL = 0x80


class EmberBindingType(basic.enum8):
    # Binding types.

    # A binding that is currently not in use.
    UNUSED_BINDING = 0x00
    # A unicast binding whose 64-bit identifier is the destination EUI64.
    UNICAST_BINDING = 0x01
    # A unicast binding whose 64-bit identifier is the aggregator EUI64.
    MANY_TO_ONE_BINDING = 0x02
    # A multicast binding whose 64-bit identifier is the group address. A
    # multicast binding can be used to send messages to the group and to
    # receive messages sent to the group.
    MULTICAST_BINDING = 0x03


class EmberApsOption(basic.bitmap16):
    # Options to use when sending a message.

    # No options.
    APS_OPTION_NONE = 0x0000
    # Encrypt with Transient Key
    APS_OPTION_ENCRYPT_WITH_TRANSIENT_KEY = 0x0001
    # Use alias Sequence number
    APS_OPTION_USE_ALIAS_SEQUENCE_NUMBER = 0x0002
    # UNKNOWN: Discovered while receiving data
    APS_OPTION_UNKNOWN = 0x0008
    # This signs the application layer message body (APS Frame not included)
    # and appends the ECDSA signature to the end of the message.  Needed by
    # Smart Energy applications.  This requires the CBKE and ECC libraries.
    # The ::emberDsaSignHandler() function is called after DSA signing
    # is complete but before the message has been sent by the APS layer.
    # Note that when passing a buffer to the stack for DSA signing, the final
    # byte in the buffer has special significance as an indicator of how many
    # leading bytes should be ignored for signature purposes.  Refer to API
    # documentation of emberDsaSign() or the dsaSign EZSP command for further
    # details about this requirement.
    APS_OPTION_DSA_SIGN = 0x0010
    # Send the message using APS Encryption, using the Link Key shared with the
    # destination node to encrypt the data at the APS Level.
    APS_OPTION_ENCRYPTION = 0x0020
    # Resend the message using the APS retry mechanism.
    APS_OPTION_RETRY = 0x0040
    # Causes a route discovery to be initiated if no route to the destination
    # is known.
    APS_OPTION_ENABLE_ROUTE_DISCOVERY = 0x0100
    # Causes a route discovery to be initiated even if one is known.
    APS_OPTION_FORCE_ROUTE_DISCOVERY = 0x0200
    # Include the source EUI64 in the network frame.
    APS_OPTION_SOURCE_EUI64 = 0x0400
    # Include the destination EUI64 in the network frame.
    APS_OPTION_DESTINATION_EUI64 = 0x0800
    # Send a ZDO request to discover the node ID of the destination, if it is
    # not already know.
    APS_OPTION_ENABLE_ADDRESS_DISCOVERY = 0x1000
    # Reserved.
    APS_OPTION_POLL_RESPONSE = 0x2000
    # This incoming message is a ZDO request not handled by the EmberZNet
    # stack, and the application is responsible for sending a ZDO response.
    # This flag is used only when the ZDO is configured to have requests
    # handled by the application. See the CONFIG_APPLICATION_ZDO_FLAGS
    # configuration parameter for more information.
    APS_OPTION_ZDO_RESPONSE_REQUIRED = 0x4000
    # This message is part of a fragmented message. This option may only be set
    # for unicasts. The groupId field gives the index of this fragment in the
    # low-order byte. If the low-order byte is zero this is the first fragment
    # and the high-order byte contains the number of fragments in the message.
    APS_OPTION_FRAGMENT = 0x8000


class EzspNetworkScanType(basic.enum8):
    # Network scan types.

    # An energy scan scans each channel for its RSSI value.
    ENERGY_SCAN = 0x00
    # An active scan scans each channel for available networks.
    ACTIVE_SCAN = 0x01


class EmberJoinDecision(basic.enum8):
    # Decision made by the trust center when a node attempts to join.

    # Allow the node to join. The joining node should have a pre-configured
    # key. The security data sent to it will be encrypted with that key.
    USE_PRECONFIGURED_KEY = 0x00
    # Allow the node to join. Send the necessary key (the Network Key in
    # Standard Security mode, the Trust Center Master in High Security mode)
    # in-the-clear to the joining device.
    SEND_KEY_IN_THE_CLEAR = 0x01
    # Deny join.
    DENY_JOIN = 0x02
    # Take no action.
    NO_ACTION = 0x03


class EmberInitialSecurityBitmask(basic.bitmap16):
    # This is the Initial Security Bitmask that controls the use of various
    # security features.

    # This enables ZigBee Standard Security on the node.
    STANDARD_SECURITY_MODE = 0x0000
    # This enables Distributed Trust Center Mode for the device forming the
    # network. (Previously known as NO_TRUST_CENTER_MODE)
    DISTRIBUTED_TRUST_CENTER_MODE = 0x0002
    # This enables a Global Link Key for the Trust Center. All nodes will share
    # the same Trust Center Link Key.
    TRUST_CENTER_GLOBAL_LINK_KEY = 0x0004
    # This enables devices that perform MAC Association with a pre-configured
    # Network Key to join the network. It is only set on the Trust Center.
    PRECONFIGURED_NETWORK_KEY_MODE = 0x0008
    # This denotes that the ::EmberInitialSecurityState::preconfiguredTrustCenterEui64
    # has a value in it containing the trust center EUI64.  The device will only join a
    # network and accept commands from a trust center with that EUI64.  Normally this
    # bit is NOT set, and the EUI64 of the trust center is learned during the join
    # process.  When commissioning a device to join onto an existing network that is
    # using a trust center, and without sending any messages, this bit must be set and
    # the field ::EmberInitialSecurityState::preconfiguredTrustCenterEui64 must be
    # populated with the appropriate EUI64.
    HAVE_TRUST_CENTER_EUI64 = 0x0040
    # This denotes that the preconfiguredKey is not the actual Link Key but a
    # Secret Key known only to the Trust Center.  It is hashed with the IEEE
    # Address of the destination device in order to create the actual Link Key
    # used in encryption. This is bit is only used by the Trust Center. The
    # joining device need not set this.
    TRUST_CENTER_USES_HASHED_LINK_KEY = 0x0084
    # This denotes that the preconfiguredKey element has valid data that should
    # be used to configure the initial security state.
    HAVE_PRECONFIGURED_KEY = 0x0100
    # This denotes that the networkKey element has valid data that should be
    # used to configure the initial security state.
    HAVE_NETWORK_KEY = 0x0200
    # This denotes to a joining node that it should attempt to acquire a Trust
    # Center Link Key during joining. This is only necessary if the device does
    # not have a pre-configured key.
    GET_LINK_KEY_WHEN_JOINING = 0x0400
    # This denotes that a joining device should only accept an encrypted
    # network key from the Trust Center (using its preconfigured key). A key
    # sent in-the-clear by the Trust Center will be rejected and the join will
    # fail. This option is only valid when utilizing a pre-configured key.
    REQUIRE_ENCRYPTED_KEY = 0x0800
    # This denotes whether the device should NOT reset its outgoing frame
    # counters (both NWK and APS) when ::emberSetInitialSecurityState() is
    # called. Normally it is advised to reset the frame counter before joining
    # a new network. However in cases where a device is joining to the same
    # network a again (but not using ::emberRejoinNetwork()) it should keep the
    # NWK and APS frame counters stored in its tokens.
    NO_FRAME_COUNTER_RESET = 0x1000
    # This denotes that the device should obtain its preconfigured key from an
    # installation code stored in the manufacturing token. The token contains a
    # value that will be hashed to obtain the actual preconfigured key. If that
    # token is not valid, then the call to emberSetInitialSecurityState() will
    # fail.
    GET_PRECONFIGURED_KEY_FROM_INSTALL_CODE = 0x2000


class EmberCurrentSecurityBitmask(basic.bitmap16):
    # This is the Current Security Bitmask that details the use of various
    # security features.

    # This denotes that the device is running in a network with ZigBee Standard
    # Security.
    STANDARD_SECURITY_MODE = 0x0000
    # This denotes that the device is running in a network with ZigBee High
    # Security.
    HIGH_SECURITY_MODE = 0x0001
    # This denotes that the device is running in a network without a
    # centralized Trust Center.
    DISTRIBUTED_TRUST_CENTER_MODE = 0x0002
    # This denotes that the device has a Global Link Key. The Trust Center Link
    # Key is the same across multiple nodes.
    GLOBAL_LINK_KEY = 0x0004
    # This denotes that the node has a Trust Center Link Key.
    HAVE_TRUST_CENTER_LINK_KEY = 0x0010
    # TODO: 0x0020 is unknown
    # TODO: 0x0040 is unknown
    # This denotes that the Trust Center is using a Hashed Link Key.
    TRUST_CENTER_USES_HASHED_LINK_KEY = 0x0084


class EmberKeyStructBitmask(basic.bitmap16):
    # Describes the presence of valid data within the EmberKeyStruct structure.

    # The key has a sequence number associated with it.
    KEY_HAS_SEQUENCE_NUMBER = 0x0001
    # The key has an outgoing frame counter associated with it.
    KEY_HAS_OUTGOING_FRAME_COUNTER = 0x0002
    # The key has an incoming frame counter associated with it.
    KEY_HAS_INCOMING_FRAME_COUNTER = 0x0004
    # The key has a Partner IEEE address associated with it.
    KEY_HAS_PARTNER_EUI64 = 0x0008
    # This indicates the key is authorized for use in APS data messages.
    # If the key is not authorized for use in APS data messages it has not
    # yet gone through a key agreement protocol, such as CBKE (i.e. ECC)
    KEY_IS_AUTHORIZED = 0x0010
    # This indicates that the partner associated with the link is a sleepy
    # end device.  This bit is set automatically if the local device
    # hears a device announce from the partner indicating it is not
    # an 'RX on when idle' device.
    KEY_PARTNER_IS_SLEEPY = 0x0020
    # This indicates that the transient key which is being added is unconfirmed. This
    # bit is set when we add a transient key while the EmberTcLinkKeyRequestPolicy is
    # EMBER_ALLOW_TC_LINK_KEY_REQUEST_AND_GENERATE_NEW_KEY
    UNCONFIRMED_TRANSIENT_KEY = 0x0040
    # This indicates that the actual key data is stored in PSA, and the respective PSA
    # ID is recorded in the psa_id field.
    KEY_HAS_PSA_ID = 0x0080
    # This indicates that the keyData field has valid data. On certain parts and
    # depending on the security configuration, keys may live in secure storage and are
    # not exportable. In such cases, keyData will not house the actual key contents.
    KEY_HAS_KEY_DATA = 0x0100


class EmberKeyStatus(basic.enum8):
    # The status of the attempt to establish a key.

    KEY_STATUS_NONE = 0x00
    APP_LINK_KEY_ESTABLISHED = 0x01
    APP_MASTER_KEY_ESTABLISHED = 0x02  # removed in ver. 5
    TRUST_CENTER_LINK_KEY_ESTABLISHED = 0x03
    KEY_ESTABLISHMENT_TIMEOUT = 0x04
    KEY_TABLE_FULL = 0x05
    TC_RESPONDED_TO_KEY_REQUEST = 0x06
    TC_APP_KEY_SENT_TO_REQUESTER = 0x07
    TC_RESPONSE_TO_KEY_REQUEST_FAILED = 0x08
    TC_REQUEST_KEY_TYPE_NOT_SUPPORTED = 0x09
    TC_NO_LINK_KEY_FOR_REQUESTER = 0x0A
    TC_REQUESTER_EUI64_UNKNOWN = 0x0B
    TC_RECEIVED_FIRST_APP_KEY_REQUEST = 0x0C
    TC_TIMEOUT_WAITING_FOR_SECOND_APP_KEY_REQUEST = 0x0D
    TC_NON_MATCHING_APP_KEY_REQUEST_RECEIVED = 0x0E
    TC_FAILED_TO_SEND_APP_KEYS = 0x0F
    TC_FAILED_TO_STORE_APP_KEY_REQUEST = 0x10
    TC_REJECTED_APP_KEY_REQUEST = 0x11
    TC_FAILED_TO_GENERATE_NEW_KEY = 0x12
    TC_FAILED_TO_SEND_TC_KEY = 0x13
    TRUST_CENTER_IS_PRE_R21 = 0x1E
    TC_REQUESTER_VERIFY_KEY_TIMEOUT = 0x32
    TC_REQUESTER_VERIFY_KEY_FAILURE = 0x33
    TC_REQUESTER_VERIFY_KEY_SUCCESS = 0x34
    VERIFY_LINK_KEY_FAILURE = 0x64
    VERIFY_LINK_KEY_SUCCESS = 0x65


class EmberZdoConfigurationFlags(basic.bitmap8):
    # Flags for controlling which incoming ZDO requests are passed to the
    # application. To see if the application is required to send a ZDO response
    # to an incoming message, the application must check the APS options
    # bitfield within the incomingMessageHandler callback to see if the
    # APS_OPTION_ZDO_RESPONSE_REQUIRED flag is set.

    # Set this flag in order to receive supported ZDO request messages via the
    # incomingMessageHandler callback. A supported ZDO request is one that is
    # handled by the EmberZNet stack. The stack will continue to handle the
    # request and send the appropriate ZDO response even if this configuration
    # option is enabled.
    APP_RECEIVES_SUPPORTED_ZDO_REQUESTS = 0x01
    # Set this flag in order to receive unsupported ZDO request messages via
    # the incomingMessageHandler callback. An unsupported ZDO request is one
    # that is not handled by the EmberZNet stack, other than to send a 'not
    # supported' ZDO response. If this configuration option is enabled, the
    # stack will no longer send any ZDO response, and it is the application's
    # responsibility to do so.
    APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS = 0x02
    # Set this flag in order to receive the following ZDO request messages via
    # the incomingMessageHandler callback: SIMPLE_DESCRIPTOR_REQUEST,
    # MATCH_DESCRIPTORS_REQUEST, and ACTIVE_ENDPOINTS_REQUEST. If this
    # configuration option is enabled, the stack will no longer send any ZDO
    # response for these requests, and it is the application's responsibility
    # to do so.
    APP_HANDLES_ZDO_ENDPOINT_REQUESTS = 0x04
    # Set this flag in order to receive the following ZDO request messages via
    # the incomingMessageHandler callback: BINDING_TABLE_REQUEST, BIND_REQUEST,
    # and UNBIND_REQUEST. If this configuration option is enabled, the stack
    # will no longer send any ZDO response for these requests, and it is the
    # application's responsibility to do so.
    APP_HANDLES_ZDO_BINDING_REQUESTS = 0x08


class EmberConcentratorType(basic.enum16):
    # Type of concentrator.

    # A concentrator with insufficient memory to store source routes for the
    # entire network. Route records are sent to the concentrator prior to every
    # inbound APS unicast.
    LOW_RAM_CONCENTRATOR = 0xFFF8
    # A concentrator with sufficient memory to store source routes for the
    # entire network. Remote nodes stop sending route records once the
    # concentrator has successfully received one.
    HIGH_RAM_CONCENTRATOR = 0xFFF9


class EmberZllState(basic.enum16):
    # ZLL device state identifier.

    # No state.
    ZLL_STATE_NONE = 0x0000
    # The device is factory new.
    ZLL_STATE_FACTORY_NEW = 0x0001
    # The device is capable of assigning addresses to other devices.
    ZLL_STATE_ADDRESS_ASSIGNMENT_CAPABLE = 0x0002
    # The device is initiating a link operation.
    ZLL_STATE_LINK_INITIATOR = 0x0010
    # The device is requesting link priority.
    ZLL_STATE_LINK_PRIORITY_REQUEST = 0x0020
    # The device is on a non-ZLL network.
    ZLL_STATE_NON_ZLL_NETWORK = 0x0100


class EmberZllKeyIndex(basic.enum8):
    # ZLL key encryption algorithm enumeration.

    # Key encryption algorithm for use during development.
    ZLL_KEY_INDEX_DEVELOPMENT = 0x00
    # Key encryption algorithm shared by all certified devices.
    ZLL_KEY_INDEX_MASTER = 0x04
    # Key encryption algorithm for use during development and certification.
    ZLL_KEY_INDEX_CERTIFICATION = 0x0F


class EzspZllNetworkOperation(basic.enum8):
    # Differentiates among ZLL network operations.

    ZLL_FORM_NETWORK = 0x00  # ZLL form network command.
    ZLL_JOIN_TARGET = 0x01  # ZLL join target command.


class EzspSourceRouteOverheadInformation(basic.enum8):
    # Validates Source Route Overhead Information cached.

    # Ezsp source route overhead unknown
    SOURCE_ROUTE_OVERHEAD_UNKNOWN = 0xFF


EmberKeyData = ztypes.KeyData
KeyData = ztypes.KeyData


class EmberCertificateData(basic.FixedList[basic.uint8_t, 48]):
    """The implicit certificate used in CBKE."""


class EmberPublicKeyData(basic.FixedList[basic.uint8_t, 22]):
    """The public key data used in CBKE."""


class EmberPrivateKeyData(basic.FixedList[basic.uint8_t, 21]):
    """The private key data used in CBKE."""


class EmberSmacData(basic.FixedList[basic.uint8_t, 16]):
    """The Shared Message Authentication Code data used in CBKE."""


class EmberSignatureData(basic.FixedList[basic.uint8_t, 42]):
    """An ECDSA signature."""


class EmberCertificate283k1Data(basic.FixedList[basic.uint8_t, 74]):
    """The implicit certificate used in CBKE."""


class EmberPublicKey283k1Data(basic.FixedList[basic.uint8_t, 37]):
    """The 283k1 public key data used in CBKE."""


class EmberPrivateKey283k1Data(basic.FixedList[basic.uint8_t, 36]):
    """The 283k1 private key data used in CBKE."""


class EmberSignature283k1Data(basic.FixedList[basic.uint8_t, 72]):
    """An 283k1 ECDSA signature data."""


class EmberMessageDigest(basic.FixedList[basic.uint8_t, 16]):
    """The calculated digest of a message"""


class sl_Status(basic.enum32):
    ## Generic Errors
    # No error.
    OK = 0x0000
    # Generic error.
    FAIL = 0x0001

    ## State Errors
    # Generic invalid state error.
    INVALID_STATE = 0x0002
    # Module is not ready for requested operation.
    NOT_READY = 0x0003
    # Module is busy and cannot carry out requested operation.
    BUSY = 0x0004
    # Operation is in progress and not yet complete (pass or fail).
    IN_PROGRESS = 0x0005
    # Operation aborted.
    ABORT = 0x0006
    # Operation timed out.
    TIMEOUT = 0x0007
    # Operation not allowed per permissions.
    PERMISSION = 0x0008
    # Non-blocking operation would block.
    WOULD_BLOCK = 0x0009
    # Operation/module is Idle, cannot carry requested operation.
    IDLE = 0x000A
    # Operation cannot be done while construct is waiting.
    IS_WAITING = 0x000B
    # No task/construct waiting/pending for that action/event.
    NONE_WAITING = 0x000C
    # Operation cannot be done while construct is suspended.
    SUSPENDED = 0x000D
    # Feature not available due to software configuration.
    NOT_AVAILABLE = 0x000E
    # Feature not supported.
    NOT_SUPPORTED = 0x000F
    # Initialization failed.
    INITIALIZATION = 0x0010
    # Module has not been initialized.
    NOT_INITIALIZED = 0x0011
    # Module has already been initialized.
    ALREADY_INITIALIZED = 0x0012
    # Object/construct has been deleted.
    DELETED = 0x0013
    # Illegal call from ISR.
    ISR = 0x0014
    # Illegal call because network is up.
    NETWORK_UP = 0x0015
    # Illegal call because network is down.
    NETWORK_DOWN = 0x0016
    # Failure due to not being joined in a network.
    NOT_JOINED = 0x0017
    # Invalid operation as there are no beacons.
    NO_BEACONS = 0x0018

    ## Allocation/ownership Errors
    # Generic allocation error.
    ALLOCATION_FAILED = 0x0019
    # No more resource available to perform the operation.
    NO_MORE_RESOURCE = 0x001A
    # Item/list/queue is empty.
    EMPTY = 0x001B
    # Item/list/queue is full.
    FULL = 0x001C
    # Item would overflow.
    WOULD_OVERFLOW = 0x001D
    # Item/list/queue has been overflowed.
    HAS_OVERFLOWED = 0x001E
    # Generic ownership error.
    OWNERSHIP = 0x001F
    # Already/still owning resource.
    IS_OWNER = 0x0020

    ## Invalid Parameters Errors
    # Generic invalid argument or consequence of invalid argument.
    INVALID_PARAMETER = 0x0021
    # Invalid null pointer received as argument.
    NULL_POINTER = 0x0022
    # Invalid configuration provided.
    INVALID_CONFIGURATION = 0x0023
    # Invalid mode.
    INVALID_MODE = 0x0024
    # Invalid handle.
    INVALID_HANDLE = 0x0025
    # Invalid type for operation.
    INVALID_TYPE = 0x0026
    # Invalid index.
    INVALID_INDEX = 0x0027
    # Invalid range.
    INVALID_RANGE = 0x0028
    # Invalid key.
    INVALID_KEY = 0x0029
    # Invalid credentials.
    INVALID_CREDENTIALS = 0x002A
    # Invalid count.
    INVALID_COUNT = 0x002B
    # Invalid signature / verification failed.
    INVALID_SIGNATURE = 0x002C
    # Item could not be found.
    NOT_FOUND = 0x002D
    # Item already exists.
    ALREADY_EXISTS = 0x002E

    ## IO/Communication Errors
    # Generic I/O failure.
    IO = 0x002F
    # I/O failure due to timeout.
    IO_TIMEOUT = 0x0030
    # Generic transmission error.
    TRANSMIT = 0x0031
    # Transmit underflowed.
    TRANSMIT_UNDERFLOW = 0x0032
    # Transmit is incomplete.
    TRANSMIT_INCOMPLETE = 0x0033
    # Transmit is busy.
    TRANSMIT_BUSY = 0x0034
    # Generic reception error.
    RECEIVE = 0x0035
    # Failed to read on/via given object.
    OBJECT_READ = 0x0036
    # Failed to write on/via given object.
    OBJECT_WRITE = 0x0037
    # Message is too long.
    MESSAGE_TOO_LONG = 0x0038

    ## EEPROM/Flash Errors
    # EEPROM MFG version mismatch.
    EEPROM_MFG_VERSION_MISMATCH = 0x0039
    # EEPROM Stack version mismatch.
    EEPROM_STACK_VERSION_MISMATCH = 0x003A
    # Flash write is inhibited.
    FLASH_WRITE_INHIBITED = 0x003B
    # Flash verification failed.
    FLASH_VERIFY_FAILED = 0x003C
    # Flash programming failed.
    FLASH_PROGRAM_FAILED = 0x003D
    # Flash erase failed.
    FLASH_ERASE_FAILED = 0x003E

    ## MAC Errors
    # MAC no data.
    MAC_NO_DATA = 0x003F
    # MAC no ACK received.
    MAC_NO_ACK_RECEIVED = 0x0040
    # MAC indirect timeout.
    MAC_INDIRECT_TIMEOUT = 0x0041
    # MAC unknown header type.
    MAC_UNKNOWN_HEADER_TYPE = 0x0042
    # MAC ACK unknown header type.
    MAC_ACK_HEADER_TYPE = 0x0043
    # MAC command transmit failure.
    MAC_COMMAND_TRANSMIT_FAILURE = 0x0044

    ## CLI_STORAGE Errors
    # Error in open NVM
    CLI_STORAGE_NVM_OPEN_ERROR = 0x0045

    ## Security status codes
    # Image checksum is not valid.
    SECURITY_IMAGE_CHECKSUM_ERROR = 0x0046
    # Decryption failed
    SECURITY_DECRYPT_ERROR = 0x0047

    ## Command status codes
    # Command was not recognized
    COMMAND_IS_INVALID = 0x0048
    # Command or parameter maximum length exceeded
    COMMAND_TOO_LONG = 0x0049
    # Data received does not form a complete command
    COMMAND_INCOMPLETE = 0x004A

    ## Misc Errors
    # Bus error, e.g. invalid DMA address
    BUS_ERROR = 0x004B

    ## Unified MAC Errors
    # CCA failure.
    CCA_FAILURE = 0x004C

    ## Scan errors
    # MAC scanning.
    MAC_SCANNING = 0x004D
    # MAC incorrect scan type.
    MAC_INCORRECT_SCAN_TYPE = 0x004E
    # Invalid channel mask.
    INVALID_CHANNEL_MASK = 0x004F
    # Bad scan duration.
    BAD_SCAN_DURATION = 0x0050

    ## MAC transmit related status
    # The MAC transmit queue is full
    MAC_TRANSMIT_QUEUE_FULL = 0x0053
    # The transmit attempt failed because the radio scheduler could not find a slot to transmit this packet in or a higher priority event interrupted it
    TRANSMIT_SCHEDULER_FAIL = 0x0054
    # An unsupported channel setting was specified
    TRANSMIT_INVALID_CHANNEL = 0x0055
    # An unsupported power setting was specified
    TRANSMIT_INVALID_POWER = 0x0056
    # The expected ACK was received after the last transmission
    TRANSMIT_ACK_RECEIVED = 0x0057
    # The transmit attempt was blocked from going over the air. Typically this is due to the Radio Hold Off (RHO) or Coexistence plugins as they can prevent transmits based on external signals.
    TRANSMIT_BLOCKED = 0x0058

    ## NVM3 specific errors
    # The initialization was aborted as the NVM3 instance is not aligned properly in memory
    NVM3_ALIGNMENT_INVALID = 0x0059
    # The initialization was aborted as the size of the NVM3 instance is too small
    NVM3_SIZE_TOO_SMALL = 0x005A
    # The initialization was aborted as the NVM3 page size is not supported
    NVM3_PAGE_SIZE_NOT_SUPPORTED = 0x005B
    # The application that there was an error initializing some of the tokens
    NVM3_TOKEN_INIT_FAILED = 0x005C
    # The initialization was aborted as the NVM3 instance was already opened with other parameters
    NVM3_OPENED_WITH_OTHER_PARAMETERS = 0x005D

    ## Zigbee status codes
    # Packet is dropped by packet-handoff callbacks
    ZIGBEE_PACKET_HANDOFF_DROPPED = 0x0C01
    # The APS layer attempted to send or deliver a message and failed
    ZIGBEE_DELIVERY_FAILED = 0x0C02
    # The maximum number of in-flight messages ::EMBER_APS_UNICAST_MESSAGE_COUNT has been reached
    ZIGBEE_MAX_MESSAGE_LIMIT_REACHED = 0x0C03
    # The application is trying to delete or overwrite a binding that is in use
    ZIGBEE_BINDING_IS_ACTIVE = 0x0C04
    # The application is trying to overwrite an address table entry that is in use
    ZIGBEE_ADDRESS_TABLE_ENTRY_IS_ACTIVE = 0x0C05
    # After moving, a mobile node's attempt to re-establish contact with the network failed
    ZIGBEE_MOVE_FAILED = 0x0C06
    # The local node ID has changed. The application can get the new node ID by calling ::sl_zigbee_get_node_id()
    ZIGBEE_NODE_ID_CHANGED = 0x0C07
    # The chosen security level is not supported by the stack
    ZIGBEE_INVALID_SECURITY_LEVEL = 0x0C08
    # An error occurred when trying to encrypt at the APS Level
    ZIGBEE_IEEE_ADDRESS_DISCOVERY_IN_PROGRESS = 0x0C09
    # An error occurred when trying to encrypt at the APS Level
    ZIGBEE_APS_ENCRYPTION_ERROR = 0x0C0A
    # There was an attempt to form or join a network with security without calling ::sl_zigbee_set_initial_security_state() first
    ZIGBEE_SECURITY_STATE_NOT_SET = 0x0C0B
    # There was an attempt to broadcast a key switch too quickly after broadcasting the next network key. The Trust Center must wait at least a period equal to the broadcast timeout so that all routers have a chance to receive the broadcast of the new network key
    ZIGBEE_TOO_SOON_FOR_SWITCH_KEY = 0x0C0C
    # The received signature corresponding to the message that was passed to the CBKE Library failed verification and is not valid
    ZIGBEE_SIGNATURE_VERIFY_FAILURE = 0x0C0D
    # The message could not be sent because the link key corresponding to the destination is not authorized for use in APS data messages
    ZIGBEE_KEY_NOT_AUTHORIZED = 0x0C0E
    # The application tried to use a binding that has been remotely modified and the change has not yet been reported to the application
    ZIGBEE_BINDING_HAS_CHANGED = 0x0C0F
    # The EUI of the Trust center has changed due to a successful rejoin after TC Swapout
    ZIGBEE_TRUST_CENTER_SWAP_EUI_HAS_CHANGED = 0x0C10
    # A Trust Center Swapout Rejoin has occurred without the EUI of the TC changing
    ZIGBEE_TRUST_CENTER_SWAP_EUI_HAS_NOT_CHANGED = 0x0C11
    # An attempt to generate random bytes failed because of insufficient random data from the radio
    ZIGBEE_INSUFFICIENT_RANDOM_DATA = 0x0C12
    # A Zigbee route error command frame was received indicating that a source routed message from this node failed en route
    ZIGBEE_SOURCE_ROUTE_FAILURE = 0x0C13
    # A Zigbee route error command frame was received indicating that a message sent to this node along a many-to-one route failed en route
    ZIGBEE_MANY_TO_ONE_ROUTE_FAILURE = 0x0C14
    # A critical and fatal error indicating that the version of the stack trying to run does not match with the chip it's running on
    ZIGBEE_STACK_AND_HARDWARE_MISMATCH = 0x0C15
    # The local PAN ID has changed. The application can get the new PAN ID by calling ::emberGetPanId()
    ZIGBEE_PAN_ID_CHANGED = 0x0C16
    # The channel has changed.
    ZIGBEE_CHANNEL_CHANGED = 0x0C17
    # The network has been opened for joining.
    ZIGBEE_NETWORK_OPENED = 0x0C18
    # The network has been closed for joining.
    ZIGBEE_NETWORK_CLOSED = 0x0C19
    # An attempt was made to join a Secured Network using a pre-configured key, but the Trust Center sent back a Network Key in-the-clear when an encrypted Network Key was required. (::EMBER_REQUIRE_ENCRYPTED_KEY)
    ZIGBEE_RECEIVED_KEY_IN_THE_CLEAR = 0x0C1A
    # An attempt was made to join a Secured Network, but the device did not receive a Network Key.
    ZIGBEE_NO_NETWORK_KEY_RECEIVED = 0x0C1B
    # After a device joined a Secured Network, a Link Key was requested (::EMBER_GET_LINK_KEY_WHEN_JOINING) but no response was ever received.
    ZIGBEE_NO_LINK_KEY_RECEIVED = 0x0C1C
    # An attempt was made to join a Secured Network without a pre-configured key, but the Trust Center sent encrypted data using a pre-configured key.
    ZIGBEE_PRECONFIGURED_KEY_REQUIRED = 0x0C1D
    # A Zigbee EZSP error has occurred. Track the origin and corresponding EzspStatus for more info.
    ZIGBEE_EZSP_ERROR = 0x0C1E

    @classmethod
    def from_ember_status(
        cls: type[sl_Status], status: EmberStatus | EzspStatus
    ) -> sl_Status:
        if isinstance(status, cls):
            return status

        key = type(status), status

        if key not in SL_STATUS_MAP:
            LOGGER.warning(
                "Unknown status %r, converting to generic %r",
                status,
                cls.FAIL,
                stacklevel=2,
            )
            return cls.FAIL

        return SL_STATUS_MAP[key]


# Generic mapping that standardizes status codes
# fmt: off
SL_STATUS_MAP: dict[EzspStatus | EmberStatus, sl_Status] = {
    (type(k), k): v for k, v in [
        # EZSP status
        (EzspStatus.SUCCESS, sl_Status.OK),
        (EzspStatus.ERROR_INVALID_ID, sl_Status.INVALID_PARAMETER),
        (EzspStatus.ERROR_OUT_OF_MEMORY, sl_Status.NO_MORE_RESOURCE),
        (EzspStatus.ERROR_INVALID_CALL, sl_Status.INVALID_PARAMETER),
        (EzspStatus.ERROR_INVALID_VALUE, sl_Status.INVALID_PARAMETER),
        # Ember status
        (EmberStatus.SUCCESS, sl_Status.OK),
        (EmberStatus.ERR_FATAL, sl_Status.FAIL),
        (EmberStatus.NOT_FOUND, sl_Status.NOT_FOUND),
        (EmberStatus.TABLE_ENTRY_ERASED, sl_Status.NOT_FOUND),
        (EmberStatus.INDEX_OUT_OF_RANGE, sl_Status.INVALID_INDEX),
        (EmberStatus.NOT_JOINED, sl_Status.NOT_JOINED),
        (EmberStatus.NETWORK_UP, sl_Status.NETWORK_UP),
        (EmberStatus.NETWORK_DOWN, sl_Status.NETWORK_DOWN),
        (EmberStatus.NETWORK_OPENED, sl_Status.ZIGBEE_NETWORK_OPENED),
        (EmberStatus.NETWORK_CLOSED, sl_Status.ZIGBEE_NETWORK_CLOSED),
        # Network status codes
        (EmberStatus.MAC_INDIRECT_TIMEOUT, sl_Status.MAC_INDIRECT_TIMEOUT),
        (EmberStatus.SOURCE_ROUTE_FAILURE, sl_Status.ZIGBEE_SOURCE_ROUTE_FAILURE),
        (EmberStatus.MANY_TO_ONE_ROUTE_FAILURE, sl_Status.ZIGBEE_MANY_TO_ONE_ROUTE_FAILURE),
        (EmberStatus.MAX_MESSAGE_LIMIT_REACHED, sl_Status.ZIGBEE_MAX_MESSAGE_LIMIT_REACHED),
        (EmberStatus.NETWORK_BUSY, sl_Status.ZIGBEE_MAX_MESSAGE_LIMIT_REACHED),
        (EmberStatus.DELIVERY_FAILED, sl_Status.ZIGBEE_DELIVERY_FAILED),
        (EmberStatus.NO_BUFFERS, sl_Status.ALLOCATION_FAILED),  # TODO: see what the actual mapping is
    ]
}
# fmt: on


class EmberDistinguishedNodeId(basic.enum16):
    """A distinguished network ID that will never be assigned to any node"""

    # This value is used when getting the remote node ID from the address or binding
    # tables. It indicates that the address or binding table entry is currently in use
    # and network address discovery is underway.
    DISCOVERY_ACTIVE = 0xFFFC

    # This value is used when getting the remote node ID from the address or binding
    # tables. It indicates that the address or binding table entry is currently in use
    # but the node ID corresponding to the EUI64 in the table is currently unknown.
    UNKNOWN = 0xFFFD

    # This value is used when setting or getting the remote node ID in the address table
    # or getting the remote node ID from the binding table. It indicates that the
    # address or binding table entry is not in use.
    TABLE_ENTRY_UNUSED = 0xFFFF


class EmberStackError(basic.enum8):
    """Stack error codes."""

    ROUTE_ERROR_NO_ROUTE_AVAILABLE = 0x00
    ROUTE_ERROR_TREE_LINK_FAILURE = 0x01
    ROUTE_ERROR_NON_TREE_LINK_FAILURE = 0x02
    ROUTE_ERROR_LOW_BATTERY_LEVEL = 0x03
    ROUTE_ERROR_NO_ROUTING_CAPACITY = 0x04
    ROUTE_ERROR_NO_INDIRECT_CAPACITY = 0x05
    ROUTE_ERROR_INDIRECT_TRANSACTION_EXPIRY = 0x06
    ROUTE_ERROR_TARGET_DEVICE_UNAVAILABLE = 0x07
    ROUTE_ERROR_TARGET_ADDRESS_UNALLOCATED = 0x08
    ROUTE_ERROR_PARENT_LINK_FAILURE = 0x09
    ROUTE_ERROR_VALIDATE_ROUTE = 0x0A
    ROUTE_ERROR_SOURCE_ROUTE_FAILURE = 0x0B
    ROUTE_ERROR_MANY_TO_ONE_ROUTE_FAILURE = 0x0C
    ROUTE_ERROR_ADDRESS_CONFLICT = 0x0D
    ROUTE_ERROR_VERIFY_ADDRESSES = 0x0E
    ROUTE_ERROR_PAN_IDENTIFIER_UPDATE = 0x0F

    ZIGBEE_NETWORK_STATUS_NETWORK_ADDRESS_UPDATE = 0x10
    ZIGBEE_NETWORK_STATUS_BAD_FRAME_COUNTER = 0x11
    ZIGBEE_NETWORK_STATUS_BAD_KEY_SEQUENCE_NUMBER = 0x12
    ZIGBEE_NETWORK_STATUS_UNKNOWN_COMMAND = 0x13


class NV3KeyId(basic.enum32):
    """NV3 key IDs."""

    # Creator keys
    CREATOR_STACK_NVDATA_VERSION = 0x0000_FF01
    CREATOR_STACK_BOOT_COUNTER = 0x0000_E263
    CREATOR_STACK_NONCE_COUNTER = 0x0000_E563
    CREATOR_STACK_ANALYSIS_REBOOT = 0x0000_E162
    CREATOR_STACK_KEYS = 0x0000_EB79
    CREATOR_STACK_NODE_DATA = 0x0000_EE64
    CREATOR_STACK_CLASSIC_DATA = 0x0000_E364
    CREATOR_STACK_ALTERNATE_KEY = 0x0000_E475
    CREATOR_STACK_APS_FRAME_COUNTER = 0x0000_E123
    CREATOR_STACK_TRUST_CENTER = 0x0000_E124
    CREATOR_STACK_NETWORK_MANAGEMENT = 0x0000_E125
    CREATOR_STACK_PARENT_INFO = 0x0000_E126
    CREATOR_STACK_PARENT_ADDITIONAL_INFO = 0x0000_E127
    CREATOR_STACK_MULTI_PHY_NWK_INFO = 0x0000_E128
    CREATOR_STACK_MIN_RECEIVED_RSSI = 0x0000_E129
    CREATOR_STACK_RESTORED_EUI64 = 0x0000_E12A

    CREATOR_MULTI_NETWORK_STACK_KEYS = 0x0000_E210
    CREATOR_MULTI_NETWORK_STACK_NODE_DATA = 0x0000_E211
    CREATOR_MULTI_NETWORK_STACK_ALTERNATE_KEY = 0x0000_E212
    CREATOR_MULTI_NETWORK_STACK_TRUST_CENTER = 0x0000_E213
    CREATOR_MULTI_NETWORK_STACK_NETWORK_MANAGEMENT = 0x0000_E214
    CREATOR_MULTI_NETWORK_STACK_PARENT_INFO = 0x0000_E215

    # A temporary solution for multi-network nwk counters:
    # This counter will be used on the network with index 1.
    CREATOR_MULTI_NETWORK_STACK_NONCE_COUNTER = 0x0000_E220
    CREATOR_MULTI_NETWORK_STACK_PARENT_ADDITIONAL_INFO = 0x0000_E221

    CREATOR_STACK_GP_DATA = 0x0000_E258
    CREATOR_STACK_GP_PROXY_TABLE = 0x0000_E259
    CREATOR_STACK_GP_SINK_TABLE = 0x0000_E25A
    CREATOR_STACK_GP_INCOMING_FC = 0x0000_E25B
    CREATOR_STACK_GP_INCOMING_FC_IN_SINK = 0x0000_E25C

    CREATOR_STACK_BINDING_TABLE = 0x0000_E274
    CREATOR_STACK_CHILD_TABLE = 0x0000_FF0D
    CREATOR_STACK_KEY_TABLE = 0x0000_E456
    CREATOR_STACK_CERTIFICATE_TABLE = 0x0000_E500
    CREATOR_STACK_ZLL_DATA = 0x0000_E501
    CREATOR_STACK_ZLL_SECURITY = 0x0000_E502
    CREATOR_STACK_ADDITIONAL_CHILD_DATA = 0x0000_E503

    # Stack keys
    NVM3KEY_STACK_NVDATA_VERSION = 0x0001_FF01
    NVM3KEY_STACK_BOOT_COUNTER = 0x0001_E263
    NVM3KEY_STACK_NONCE_COUNTER = 0x0001_E563
    NVM3KEY_STACK_ANALYSIS_REBOOT = 0x0001_E162
    NVM3KEY_STACK_KEYS = 0x0001_EB79
    NVM3KEY_STACK_NODE_DATA = 0x0001_EE64
    NVM3KEY_STACK_CLASSIC_DATA = 0x0001_E364
    NVM3KEY_STACK_ALTERNATE_KEY = 0x0001_E475
    NVM3KEY_STACK_APS_FRAME_COUNTER = 0x0001_E123
    NVM3KEY_STACK_TRUST_CENTER = 0x0001_E124
    NVM3KEY_STACK_NETWORK_MANAGEMENT = 0x0001_E125
    NVM3KEY_STACK_PARENT_INFO = 0x0001_E126
    NVM3KEY_STACK_PARENT_ADDITIONAL_INFO = 0x0001_E127
    NVM3KEY_STACK_MULTI_PHY_NWK_INFO = 0x0001_E128
    NVM3KEY_STACK_MIN_RECEIVED_RSSI = 0x0001_E129
    NVM3KEY_STACK_RESTORED_EUI64 = 0x0001_E12A

    # MULTI-NETWORK STACK KEYS
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_MULTI_NETWORK_STACK_KEYS = 0x0001_0000
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_MULTI_NETWORK_STACK_NODE_DATA = 0x0001_0080
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_MULTI_NETWORK_STACK_ALTERNATE_KEY = 0x0001_0100
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_MULTI_NETWORK_STACK_TRUST_CENTER = 0x0001_0180
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_MULTI_NETWORK_STACK_NETWORK_MANAGEMENT = 0x0001_0200
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_MULTI_NETWORK_STACK_PARENT_INFO = 0x0001_0280

    # Temporary solution for multi-network nwk counters:
    # This counter will be used on the network with index 1.
    NVM3KEY_MULTI_NETWORK_STACK_NONCE_COUNTER = 0x0001_E220
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved
    NVM3KEY_MULTI_NETWORK_STACK_PARENT_ADDITIONAL_INFO = 0x0001_0300

    # GP stack tokens.
    NVM3KEY_STACK_GP_DATA = 0x0001_E258
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_STACK_GP_PROXY_TABLE = 0x0001_0380
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_STACK_GP_SINK_TABLE = 0x0001_0400
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved
    NVM3KEY_STACK_GP_INCOMING_FC = 0x0001_0480

    # APP KEYS
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_STACK_BINDING_TABLE = 0x0001_0500
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_STACK_CHILD_TABLE = 0x0001_0580
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_STACK_KEY_TABLE = 0x0001_0600
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_STACK_CERTIFICATE_TABLE = 0x0001_0680
    NVM3KEY_STACK_ZLL_DATA = 0x0001_E501
    NVM3KEY_STACK_ZLL_SECURITY = 0x0001_E502
    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved.
    NVM3KEY_STACK_ADDITIONAL_CHILD_DATA = 0x0001_0700

    # This key is used for an indexed token and the subsequent 0x7F keys are also reserved
    NVM3KEY_STACK_GP_INCOMING_FC_IN_SINK = 0x0001_0780


class SecurityManagerKeyType(basic.enum8):
    """The list of supported key types used by Zigbee Security Manager."""

    NONE = 0
    # This is the network key, used for encrypting and decrypting network
    # payloads.
    # There is only one of these keys in storage.
    NETWORK = 1
    # This is the Trust Center Link Key. On the joining device, this is the APS
    # key used to communicate with the trust center. On the trust center, this
    # key can be used as a root key for APS encryption and decryption when
    # communicating with joining devices (if the security policy has the
    # EMBER_TRUST_CENTER_USES_HASHED_LINK_KEY bit set).
    # There is only one of these keys in storage.
    TC_LINK = 2
    # This is a Trust Center Link Key, but it times out after either
    # ::EMBER_TRANSIENT_KEY_TIMEOUT_S or
    # ::EMBER_AF_PLUGIN_NETWORK_CREATOR_SECURITY_NETWORK_OPEN_TIME_S (if
    # defined), whichever is longer. This type of key is set on trust centers
    # who wish to open joining with a temporary, or transient, APS key for
    # devices to join with. Joiners who wish to try several keys when joining a
    # network may set several of these types of keys before attempting to join.
    # This is an indexed key, and local storage can fit as many keys as
    # available RAM allows.
    TC_LINK_WITH_TIMEOUT = 3
    # This is an Application link key. On both joining devices and the trust
    # center, this key is used in APS encryption and decryption when
    # communicating to a joining device.
    # This is an indexed key table of size EMBER_KEY_TABLE_SIZE, so long as there
    # is sufficient nonvolatile memory to store keys.
    APP_LINK = 4
    # Key type used to store Secure EZSP keys
    SECURE_EZSP_KEY = 5
    # This is the ZLL encryption key for use by algorithms that require it.
    ZLL_ENCRYPTION_KEY = 6
    # For ZLL, this is the pre-configured link key used during classical ZigBee
    # commissioning.
    ZLL_PRECONFIGURED_KEY = 7
    # This is a Green Power Device (GPD) key used on a Proxy device.
    GREEN_POWER_PROXY_TABLE_KEY = 8
    # This is a Green Power Device (GPD) key used on a Sink device.
    GREEN_POWER_SINK_TABLE_KEY = 9
    # This is a generic key type intended to be loaded for one-time hashing or
    # crypto operations. This key is not persisted.  Intended for use by the Zigbee
    # stack.
    INTERNAL = 10


class SecurityManagerContextFlags(basic.bitmap8):
    """Security Manager context flags."""

    NONE = 0x00
    # For export APIs, this flag indicates the key_index parameter is valid in
    # the ::SecurityManagerContext structure. This bit is set by the caller
    # when intending to search for a key by key_index. This flag has no
    # significance for import APIs.
    KEY_INDEX_IS_VALID = 0x01

    # For export APIs, this flag indicates the eui64 parameter is valid in the
    # ::SecurityManagerContext structure. This bit is set by the caller when
    # intending to search for a key by eui64. It is also set when searching by
    # key_index and an entry is found. This flag has no significance for import
    # APIs.
    EUI_IS_VALID = 0x02

    # Internal use only. This indicates that the transient key being added is an
    # unconfirmed, updated key. This bit is set when we add a transient key and
    # the ::EmberTcLinkKeyRequestPolicy policy
    # is ::EMBER_ALLOW_TC_LINK_KEY_REQUEST_AND_GENERATE_NEW_KEY, whose behavior
    # dictates that we generate a new, unconfirmed key, send it to the requester,
    # and await for a Verify Key Confirm message.
    UNCONFIRMED_TRANSIENT_KEY = 0x04


class EzspConfigId(basic.enum8):
    # Identifies a configuration value.

    # The number of packet buffers available to the stack.  When set to the
    # special value 0xFF, the NCP will allocate all remaining configuration RAM
    # towards packet buffers, such that the resulting count will be the largest
    # whole number of packet buffers that can fit into the available memory.
    CONFIG_PACKET_BUFFER_COUNT = 0x01
    # The maximum number of router neighbors the stack can keep track of. A
    # neighbor is a node within radio range.
    CONFIG_NEIGHBOR_TABLE_SIZE = 0x02
    # The maximum number of APS retried messages the stack can be transmitting
    # at any time.
    CONFIG_APS_UNICAST_MESSAGE_COUNT = 0x03
    # The maximum number of non-volatile bindings supported by the stack.
    CONFIG_BINDING_TABLE_SIZE = 0x04
    # The maximum number of EUI64 to network address associations that the
    # stack can maintain for the application. (Note, the total number of such
    # address associations maintained by the NCP is the sum of the value of
    # this setting and the value of ::CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE).
    CONFIG_ADDRESS_TABLE_SIZE = 0x05
    # The maximum number of multicast groups that the device may be a member
    # of.
    CONFIG_MULTICAST_TABLE_SIZE = 0x06
    # The maximum number of destinations to which a node can route messages.
    # This includes both messages originating at this node and those relayed
    # for others.
    CONFIG_ROUTE_TABLE_SIZE = 0x07
    # The number of simultaneous route discoveries that a node will support.
    CONFIG_DISCOVERY_TABLE_SIZE = 0x08
    # The size of the alarm broadcast buffer.
    CONFIG_BROADCAST_ALARM_DATA_SIZE = 0x09  # Removed in EZSPv5
    # The size of the unicast alarm buffers allocated for end device children.
    CONFIG_UNICAST_ALARM_DATA_SIZE = 0x0A  # Removed in EZSPv5
    # Specifies the stack profile.
    CONFIG_STACK_PROFILE = 0x0C
    # The security level used for security at the MAC and network layers. The
    # supported values are 0 (no security) and 5 (payload is encrypted and a
    # four-byte MIC is used for authentication).
    CONFIG_SECURITY_LEVEL = 0x0D
    # The maximum number of hops for a message.
    CONFIG_MAX_HOPS = 0x10
    # The maximum number of end device children that a router will support.
    CONFIG_MAX_END_DEVICE_CHILDREN = 0x11
    # The maximum amount of time that the MAC will hold a message for indirect
    # transmission to a child.
    CONFIG_INDIRECT_TRANSMISSION_TIMEOUT = 0x12
    # The maximum amount of time that an end device child can wait between
    # polls. If no poll is heard within this timeout, then the parent removes
    # the end device from its tables.
    CONFIG_END_DEVICE_POLL_TIMEOUT = 0x13
    # The maximum amount of time that a mobile node can wait between polls. If
    # no poll is heard within this timeout, then the parent removes the mobile
    # node from its tables.
    CONFIG_MOBILE_NODE_POLL_TIMEOUT = 0x14  # Removed in EZSPv6
    # The number of child table entries reserved for use only by mobile nodes.
    CONFIG_RESERVED_MOBILE_CHILD_ENTRIES = 0x15  # Removed in EZSPv6
    # Enables boost power mode and/or the alternate transmitter output.
    CONFIG_TX_POWER_MODE = 0x17
    # 0: Allow this node to relay messages. 1: Prevent this node from relaying
    # messages.
    CONFIG_DISABLE_RELAY = 0x18
    # The maximum number of EUI64 to network address associations that the
    # Trust Center can maintain.  These address cache entries are reserved for
    # and reused by the Trust Center when processing device join/rejoin
    # authentications. This cache size limits the number of overlapping joins
    # the Trust Center can process within a narrow time window (e.g. two
    # seconds), and thus should be set to the maximum number of near
    # simultaneous joins the Trust Center is expected to accommodate. (Note,
    # the total number of such address associations maintained by the NCP is
    # the sum of the value of this setting and the value of
    # ::CONFIG_ADDRESS_TABLE_SIZE.)
    CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE = 0x19
    # The size of the source route table.
    CONFIG_SOURCE_ROUTE_TABLE_SIZE = 0x1A
    # The units used for timing out end devices on their parents.
    CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT = 0x1B  # Removed in EZSPv7
    # The number of blocks of a fragmented message that can be sent in a single
    # window.
    CONFIG_FRAGMENT_WINDOW_SIZE = 0x1C
    # The time the stack will wait (in milliseconds) between sending blocks of
    # a fragmented message.
    CONFIG_FRAGMENT_DELAY_MS = 0x1D
    # The size of the Key Table used for storing individual link keys (if the
    # device is a Trust Center) or Application Link Keys (if the device is a
    # normal node).
    CONFIG_KEY_TABLE_SIZE = 0x1E
    # The APS ACK timeout value. The stack waits this amount of time between
    # resends of APS retried messages.
    CONFIG_APS_ACK_TIMEOUT = 0x1F
    # The duration of an active scan, in the units used by the 15.4 scan
    # parameter (((1 << duration) + 1) * 15ms). This also controls the jitter
    # used when responding to a beacon request.
    CONFIG_ACTIVE_SCAN_DURATION = 0x20
    # The time the coordinator will wait (in seconds) for a second end device
    # bind request to arrive.
    CONFIG_END_DEVICE_BIND_TIMEOUT = 0x21
    # The number of PAN id conflict reports that must be received by the
    # network manager within one minute to trigger a PAN id change.
    CONFIG_PAN_ID_CONFLICT_REPORT_THRESHOLD = 0x22
    # The timeout value in minutes for how long the Trust Center or a normal
    # node waits for the ZigBee Request Key to complete. On the Trust Center
    # this controls whether or not the device buffers the request, waiting for
    # a matching pair of ZigBee Request Key. If the value is non-zero, the
    # Trust Center buffers and waits for that amount of time. If the value is
    # zero, the Trust Center does not buffer the request and immediately
    # responds to the request.  Zero is the most compliant behavior.
    CONFIG_REQUEST_KEY_TIMEOUT = 0x24
    # This value indicates the size of the runtime modifiable certificate
    # table. Normally certificates are stored in MFG tokens but this table can
    # be used to field upgrade devices with new Smart Energy certificates.
    # This value cannot be set, it can only be queried.
    CONFIG_CERTIFICATE_TABLE_SIZE = 0x29
    # This is a bitmask that controls which incoming ZDO request messages are
    # passed to the application. The bits are defined in the
    # EmberZdoConfigurationFlags enumeration. To see if the application is
    # required to send a ZDO response in reply to an incoming message, the
    # application must check the APS options bitfield within the
    # incomingMessageHandler callback to see if the
    # APS_OPTION_ZDO_RESPONSE_REQUIRED flag is set.
    CONFIG_APPLICATION_ZDO_FLAGS = 0x2A
    # The maximum number of broadcasts during a single broadcast timeout
    # period.
    CONFIG_BROADCAST_TABLE_SIZE = 0x2B
    # The size of the MAC filter list table.
    CONFIG_MAC_FILTER_TABLE_SIZE = 0x2C
    # The number of supported networks.
    CONFIG_SUPPORTED_NETWORKS = 0x2D
    # Whether multicasts are sent to the RxOnWhenIdle=true address (0xFFFD) or
    # the sleepy broadcast address (0xFFFF). The RxOnWhenIdle=true address is
    # the ZigBee compliant destination for multicasts.
    CONFIG_SEND_MULTICASTS_TO_SLEEPY_ADDRESS = 0x2E
    # ZLL group address initial configuration.
    CONFIG_ZLL_GROUP_ADDRESSES = 0x2F
    # ZLL rssi threshold initial configuration.
    CONFIG_ZLL_RSSI_THRESHOLD = 0x30
    # The maximum number of pairings supported by the stack. Controllers
    # must support at least one pairing table entry while targets must
    # support at least five.
    CONFIG_RF4CE_PAIRING_TABLE_SIZE = 0x31  # Removed in EZSPv6
    # The maximum number of outgoing RF4CE packets supported by the stack.
    CONFIG_RF4CE_PENDING_OUTGOING_PACKET_TABLE_SIZE = 0x32  # Removed in EZSPv6
    # Toggles the mtorr flow control in the stack.
    # The maximum number of pairings supported by the stack. Controllers
    # must support at least one pairing table entry while targets must
    # support at least five.
    CONFIG_MTORR_FLOW_CONTROL = 0x33
    # Setting the retry queue size.
    CONFIG_RETRY_QUEUE_SIZE = 0x34
    # Setting the new broadcast entry threshold.
    CONFIG_NEW_BROADCAST_ENTRY_THRESHOLD = 0x35
    # The length of time, in seconds, that a trust center will store a
    # transient link key that a device can use to join its network. A transient
    # key is added with a call to emberAddTransientLinkKey. After the transient
    # key is added, it will be removed once this amount of time has passed. A
    # joining device will not be able to use that key to join until it is added
    # again on the trust center. The default value is 300 seconds, i.e., 5
    # minutes.
    CONFIG_TRANSIENT_KEY_TIMEOUT_S = 0x36
    # The number of passive acknowledgements to record from neighbors before we stop
    # re-transmitting broadcasts
    CONFIG_BROADCAST_MIN_ACKS_NEEDED = 0x37  # Replaces below entry in EZSPv6+
    # Whether the NCP has updated Green Power support. Both host and NCP software must
    # be updated to fully support Green Power Proxy Basic functionality. The 5.10.1 host
    # software calls new EZSP functions for Green Power.  If this configuration value is
    # not present, the host will not call the new functions.
    CONFIG_GREEN_POWER_ACTIVE = 0x37  # Added in EZSPv5 and removed in EZSPv6
    # The length of time, in seconds, that a trust center will allow a Trust Center
    # (insecure) rejoin for a device that is using the well-known link key. This timeout
    # takes effect once rejoins using the well-known key has been allowed. This command
    # updates the emAllowTcRejoinsUsingWellKnownKeyTimeoutSec value.
    CONFIG_TC_REJOINS_USING_WELL_KNOWN_KEY_TIMEOUT_S = 0x38
    # Valid range of a CTUNE value is 0x0000-0x01FF. Higher order bits (0xFE00) of the
    # 16-bit value are ignored.
    CONFIG_CTUNE_VALUE = 0x39
    # To configure non trust center node to assume a concentrator type of the trust
    # center it join to, until it receive many-to-one route request from the trust
    # center. For the trust center node, concentrator type is configured from the
    # concentrator plugin. The stack by default assumes trust center be a low RAM
    # concentrator that make other devices send route record to the trust center even
    # without receiving a many-to-one route request. The default concentrator type can
    # be changed by setting appropriate EmberAssumeTrustCenterConcentratorType config
    # value.
    CONFIG_ASSUME_TC_CONCENTRATOR_TYPE = 0x40
    # This is green power proxy table size. This value is readonly and cannot be set at
    # runtime.
    CONFIG_GP_PROXY_TABLE_SIZE = 0x41
    # This is green power sink table size. This value is readonly and cannot be set at
    # runtime.
    EZSP_CONFIG_GP_SINK_TABLE_SIZE = 0x42


class EzspValueId(basic.enum8):
    # Identifies a value.

    # The contents of the node data stack token.
    VALUE_TOKEN_STACK_NODE_DATA = 0x00
    # The types of MAC passthrough messages that the host wishes to receive.
    VALUE_MAC_PASSTHROUGH_FLAGS = 0x01
    # The source address used to filter legacy EmberNet messages when the
    # MAC_PASSTHROUGH_EMBERNET_SOURCE flag is set in VALUE_MAC_PASSTHROUGH_FLAGS.
    VALUE_EMBERNET_PASSTHROUGH_SOURCE_ADDRESS = 0x02
    # The number of available message buffers.
    VALUE_FREE_BUFFERS = 0x03
    # Selects sending synchronous callbacks in ezsp-uart.
    VALUE_UART_SYNCH_CALLBACKS = 0x04
    # The maximum incoming transfer size for the local node.
    VALUE_MAXIMUM_INCOMING_TRANSFER_SIZE = 0x05
    # The maximum outgoing transfer size for the local node.
    VALUE_MAXIMUM_OUTGOING_TRANSFER_SIZE = 0x06
    # A boolean indicating whether stack tokens are written to persistent
    # storage as they change.
    VALUE_STACK_TOKEN_WRITING = 0x07
    # A read-only value indicating whether the stack is currently performing a rejoin.
    VALUE_STACK_IS_PERFORMING_REJOIN = 0x08
    # A list of EmberMacFilterMatchData values.
    VALUE_MAC_FILTER_LIST = 0x09
    # The Ember Extended Security Bitmask.
    VALUE_EXTENDED_SECURITY_BITMASK = 0x0A
    # The node short ID.
    VALUE_NODE_SHORT_ID = 0x0B
    # The descriptor capability of the local node.
    VALUE_DESCRIPTOR_CAPABILITY = 0x0C
    # The stack device request sequence number of the local node.
    VALUE_STACK_DEVICE_REQUEST_SEQUENCE_NUMBER = 0x0D
    # Enable or disable radio hold-off.
    VALUE_RADIO_HOLD_OFF = 0x0E
    # The flags field associated with the endpoint data.
    VALUE_ENDPOINT_FLAGS = 0x0F
    # Enable/disable the Mfg security config key settings.
    VALUE_MFG_SECURITY_CONFIG = 0x10
    # Retrieves the version information from the stack on the NCP.
    VALUE_VERSION_INFO = 0x11
    # This will get/set the rejoin reason noted by the host for a subsequent call to
    # emberFindAndRejoinNetwork(). After a call to emberFindAndRejoinNetwork() the
    # host's rejoin reason will be set to REJOIN_REASON_NONE. The NCP will store the
    # rejoin reason used by the call to emberFindAndRejoinNetwork()
    VALUE_NEXT_HOST_REJOIN_REASON = 0x12
    # This is the reason that the last rejoin took place. This value may only be
    # retrieved, not set. The rejoin may have been initiated by the stack (NCP) or the
    # application (host). If a host initiated a rejoin the reason will be set by default
    # to REJOIN_DUE_TO_APP_EVENT_1. If the application wishes to denote its own rejoin
    # reasons it can do so by calling ezspSetValue(VALUE_HOST_REJOIN_REASON,
    # REJOIN_DUE_TO_APP_EVENT_X). X is a number corresponding to one of the app events
    # defined. If the NCP initiated a rejoin it will record this value internally for
    # retrieval by ezspGetValue(VALUE_REAL_REJOIN_REASON).
    VALUE_LAST_REJOIN_REASON = 0x13
    # The next ZigBee sequence number.
    VALUE_NEXT_ZIGBEE_SEQUENCE_NUMBER = 0x14
    # CCA energy detect threshold for radio.
    VALUE_CCA_THRESHOLD = 0x15
    # The RF4CE discovery LQI threshold parameter.
    VALUE_RF4CE_DISCOVERY_LQI_THRESHOLD = 0x16
    # The threshold value for a counter
    VALUE_SET_COUNTER_THRESHOLD = 0x17
    # Resets all counters thresholds to 0xFF
    VALUE_RESET_COUNTER_THRESHOLDS = 0x18
    # Clears all the counters
    VALUE_CLEAR_COUNTERS = 0x19
    # The node's new certificate signed by the CA.
    VALUE_CERTIFICATE_283K1 = 0x1A
    # The Certificate Authority's public key.
    VALUE_PUBLIC_KEY_283K1 = 0x1B
    # The node's new static private key.
    VALUE_PRIVATE_KEY_283K1 = 0x1C
    # The GDP binding recipient parameters
    VALUE_RF4CE_GDP_BINDING_RECIPIENT_PARAMETERS = 0x1D
    # The GDP binding push button stimulus received pending flag
    VALUE_RF4CE_GDP_PUSH_BUTTON_STIMULUS_RECEIVED_PENDING_FLAG = 0x1E
    # The GDP originator proxy flag in the advanced binding options
    VALUE_RF4CE_GDP_BINDING_PROXY_FLAG = 0x1F
    # 0x21 The MSO user string
    VALUE_RF4CE_GDP_APPLICATION_SPECIFIC_USER_STRING = 0x20
    # The MSO user string
    VALUE_RF4CE_MSO_USER_STRING = 0x21
    # The MSO binding recipient parameters
    VALUE_RF4CE_MSO_BINDING_RECIPIENT_PARAMETERS = 0x22
    # The NWK layer security frame counter value
    VALUE_NWK_FRAME_COUNTER = 0x23
    # The APS layer security frame counter value
    VALUE_APS_FRAME_COUNTER = 0x24
    # Sets the device type to use on the next rejoin using device type
    VALUE_RETRY_DEVICE_TYPE = 0x25
    # The device RF4CE base channel
    VALUE_RF4CE_BASE_CHANNEL = 0x26
    # The RF4CE device types supported by the node
    VALUE_RF4CE_SUPPORTED_DEVICE_TYPES_LIST = 0x27
    # The RF4CE profiles supported by the node
    VALUE_RF4CE_SUPPORTED_PROFILES_LIST = 0x28
    # Setting this byte enables R21 behavior on the NCP.
    VALUE_ENABLE_R21_BEHAVIOR = 0x29
    # Configure the antenna mode(0-primary,1-secondary,2- toggle on tx ack fail).
    VALUE_ANTENNA_MODE = 0x30
    # Enable or disable packet traffic arbitration.
    VALUE_ENABLE_PTA = 0x31
    # Set packet traffic arbitration configuration options.
    VALUE_PTA_OPTIONS = 0x32
    # Configure manufacturing library options(0-non-CSMA transmits,1-CSMA transmits).
    VALUE_MFGLIB_OPTIONS = 0x33
    # Sets the flag to use either negotiated power by link power delta (LPD) or fixed
    # power value provided by user while forming/joining a network for packet
    # transmissions on subghz interface. This is mainly for testing purposes.
    VALUE_USE_NEGOTIATED_POWER_BY_LPD = 0x34
    # Set packet traffic arbitration configuration PWM options.
    VALUE_PTA_PWM_OPTIONS = 0x35
    # Legacy aliases only for EZSPv6?, these were renumbered!
    # VALUE_END_DEVICE_TIMEOUT_OPTIONS_MASK = 0x36
    # VALUE_END_DEVICE_KEEP_ALIVE_SUPPORT_MODE = 0x37
    VALUE_PTA_DIRECTIONAL_PRIORITY_PULSE_WIDTH = 0x36
    # Set packet traffic arbitration phy select timeout(ms)
    VALUE_PTA_PHY_SELECT_TIMEOUT = 0x37
    # Configure the RX antenna mode: (0-do not switch; 1- primary; 2-secondary;
    # 3-RX antenna diversity).
    VALUE_ANTENNA_RX_MODE = 0x38
    # Configure the timeout to wait for the network key before failing a join.
    VALUE_NWK_KEY_TIMEOUT = 0x39
    # The number of failed CSMA attempts due to failed CCA made by the MAC before
    # continuing transmission with CCA disabled. This is the same as calling the
    # emberForceTxAfterFailedCca(uint8_t csmaAttempts) API. A value of 0 disables the
    # feature
    VALUE_FORCE_TX_AFTER_FAILED_CCA_ATTEMPTS = 0x3A
    # The length of time, in seconds, that a trust center will store a transient link
    # key that a device can use to join its network. A transient key is added with a
    # call to emberAddTransientLinkKey. After the transient key is added, it will be
    # removed once this amount of time has passed. A joining device will not be able to
    # use that key to join until it is added again on the trust center. The default
    # value is 300 seconds (5 minutes).
    VALUE_TRANSIENT_KEY_TIMEOUT_S = 0x3B
    # Cumulative energy usage metric since the last value reset of the coulomb counter
    # plugin. Setting this value will reset the coulomb counter.
    VALUE_COULOMB_COUNTER_USAGE = 0x3C
    # When scanning, configure the maximum number of beacons to store in cache. Each
    # beacon consumes one packet buffer in RAM.
    VALUE_MAX_BEACONS_TO_STORE = 0x3D
    # Set the mask to filter out unacceptable child timeout options on a router.
    VALUE_END_DEVICE_TIMEOUT_OPTIONS_MASK = 0x3E
    # The end device keep alive mode supported by the parent.
    VALUE_END_DEVICE_KEEP_ALIVE_SUPPORT_MODE = 0x3F
    # Sets the mask that controls which pins will have their GPIO configuration and
    # output values set to their power-up and power-down values when the NCP powers
    # the radio up and down.
    VALUE_GPIO_RADIO_POWER_MASK = 0x40
    # Return the active radio config.
    VALUE_ACTIVE_RADIO_CONFIG = 0x41
    # Timeout in milliseconds to store entries in the transient device table.
    # If the devices are not authenticated before the timeout, the entry shall be
    # purged.
    VALUE_TRANSIENT_DEVICE_TIMEOUT = 0x43
    # Return information about the key storage on an NCP.
    # Returns 0 if keys are in classic key storage, and 1 if they
    # are located in PSA key storage. Read only.
    VALUE_KEY_STORAGE_VERSION = 0x44
    # Return activation state about TC Delayed Join on an NCP.  A return value of
    # 0 indicates that the feature is not activated.
    VALUE_DELAYED_JOIN_ACTIVATION = 0x45


class EmberRf4ceTxOption(basic.uint8_t):
    # RF4CE transmission options.
    pass


class EmberRf4ceNodeCapabilities(basic.uint8_t):
    # The RF4CE node capabilities.
    pass


class EmberRf4ceApplicationCapabilities(basic.uint8_t):
    # The RF4CE application capabilities.
    pass


class EmberKeyType(basic.enum8):
    # Describes the type of ZigBee security key.

    # A shared key between the Trust Center and a device.
    TRUST_CENTER_LINK_KEY = 0x01
    # A shared secret used for deriving keys between the Trust Center and a
    # device
    TRUST_CENTER_MASTER_KEY = 0x02
    # The current active Network Key used by all devices in the network.
    CURRENT_NETWORK_KEY = 0x03
    # The alternate Network Key that was previously in use, or the newer key
    # that will be switched to.
    NEXT_NETWORK_KEY = 0x04
    # An Application Link Key shared with another (non-Trust Center) device.
    APPLICATION_LINK_KEY = 0x05
    # An Application Master Key shared secret used to derive an Application
    # Link Key.
    APPLICATION_MASTER_KEY = 0x06


class EzspPolicyId(basic.enum8):
    # Identifies a policy.

    # Controls trust center behavior.
    TRUST_CENTER_POLICY = 0x00
    # Controls how external binding modification requests are handled.
    BINDING_MODIFICATION_POLICY = 0x01
    # Controls whether the Host supplies unicast replies.
    UNICAST_REPLIES_POLICY = 0x02
    # Controls whether pollHandler callbacks are generated.
    POLL_HANDLER_POLICY = 0x03
    # Controls whether the message contents are included in the
    # messageSentHandler callback.
    MESSAGE_CONTENTS_IN_CALLBACK_POLICY = 0x04
    # Controls whether the Trust Center will respond to Trust Center link key
    # requests.
    TC_KEY_REQUEST_POLICY = 0x05
    # Controls whether the Trust Center will respond to application link key
    # requests.
    APP_KEY_REQUEST_POLICY = 0x06
    # Controls whether ZigBee packets that appear invalid are automatically
    # dropped by the stack. A counter will be incremented when this occurs.
    PACKET_VALIDATE_LIBRARY_POLICY = 0x07
    # Controls whether the stack will process ZLL messages.
    ZLL_POLICY = 0x08
    # Controls whether Trust Center (insecure) rejoins for devices using the well-known
    # link key are accepted. If rejoining using the well-known key is allowed, it is
    # disabled again after emAllowTcRejoinsUsingWellKnownKeyTimeoutSec seconds.
    TC_REJOINS_USING_WELL_KNOWN_KEY_POLICY = 0x09
    # Controls whether the ZigBee RF4CE stack will use standard profile-dependent
    # behavior during the discovery and pairing process. The profiles supported at the
    # NCP at the moment are ZRC 1.1 and MSO. If this policy is enabled the stack will
    # use standard behavior for the profiles ZRC 1.1 and MSO while it will fall back to
    # the on/off RF4CE policies for other profiles. If this policy is disabled the
    # on/off RF4CE policies are used for all profiles.
    RF4CE_DISCOVERY_AND_PAIRING_PROFILE_BEHAVIOR_POLICY = 0x09  # Removed in EZSPv6
    # Controls whether the ZigBee RF4CE stack will respond to an incoming discovery
    # request or not.
    RF4CE_DISCOVERY_REQUEST_POLICY = 0x0A  # Removed in EZSPv6
    # Controls the behavior of the ZigBee RF4CE stack discovery process.
    RF4CE_DISCOVERY_POLICY = 0x0B  # Removed in EZSPv6
    # Controls whether the ZigBee RF4CE stack will accept or deny a pair request.
    RF4CE_PAIR_REQUEST_POLICY = 0x0C  # Removed in EZSPv6


class EzspDecisionBitmask(basic.bitmap8):
    """EZSP Decision bitmask."""

    # XXX: this is intentionally an 8-bit bitmap! The SDK source treats it as a 16-bit
    # value but it is always serialized to an 8-bit integer

    # Disallow joins and rejoins.
    DEFAULT_CONFIGURATION = 0x0000
    # Send the network key to all joining devices.
    ALLOW_JOINS = 0x0001
    # Send the network key to all rejoining devices.
    ALLOW_UNSECURED_REJOINS = 0x0002
    # Send the network key in the clear.
    SEND_KEY_IN_CLEAR = 0x0004
    # Do nothing for unsecured rejoins.
    IGNORE_UNSECURED_REJOINS = 0x0008
    # Allow joins if there is an entry in the transient key table.
    JOINS_USE_INSTALL_CODE_KEY = 0x0010
    # Delay sending the network key to a new joining device.
    DEFER_JOINS = 0x0020


class EzspDecisionId(basic.enum8):
    # Identifies a policy decision.

    # Send the network key in the clear to all joining and rejoining devices.
    ALLOW_JOINS = 0x00
    # Send the network key in the clear to all joining devices.  Rejoining
    # devices are sent the network key encrypted with their trust center link
    # key. The trust center and any rejoining device are assumed to share a
    # link key, either preconfigured or obtained under a previous policy.
    ALLOW_JOINS_REJOINS_HAVE_LINK_KEY = 0x04
    # Send the network key encrypted with the joining or rejoining device's
    # trust center link key. The trust center and any joining or rejoining
    # device are assumed to share a link key, either preconfigured or obtained
    # under a previous policy. This is the default value for the
    # TRUST_CENTER_POLICY.
    ALLOW_PRECONFIGURED_KEY_JOINS = 0x01
    # Send the network key encrypted with the rejoining device's trust center
    # link key. The trust center and any rejoining device are assumed to share
    # a link key, either preconfigured or obtained under a previous policy. No
    # new devices are allowed to join.
    ALLOW_REJOINS_ONLY = 0x02
    # Reject all unsecured join and rejoin attempts.
    DISALLOW_ALL_JOINS_AND_REJOINS = 0x03
    # Take no action on trust center rejoin attempts.
    IGNORE_TRUST_CENTER_REJOINS = 0x05
    # Admit joins only if there is an entry in the transient key table. This corresponds
    # to the Base Device Behavior specification where a Trust Center enforces all
    # devices to join with an install code-derived link key.
    BDB_JOIN_USES_INSTALL_CODE_KEY = 0x06
    # Delay sending the network key to a new joining device.
    DEFER_JOINS_REJOINS_HAVE_LINK_KEY = 0x07
    # BINDING_MODIFICATION_POLICY default decision. Do not allow the local
    # binding table to be changed by remote nodes.
    DISALLOW_BINDING_MODIFICATION = 0x10
    # BINDING_MODIFICATION_POLICY decision.  Allow remote nodes to change
    # the local binding table.
    ALLOW_BINDING_MODIFICATION = 0x11
    # BINDING_MODIFICATION_POLICY decision.  Allows remote nodes to set local
    # binding entries only if the entries correspond to endpoints defined on
    # the device, and for output clusters bound to those endpoints.
    CHECK_BINDING_MODIFICATIONS_ARE_VALID_ENDPOINT_CLUSTERS = 0x12
    # UNICAST_REPLIES_POLICY default decision.  The NCP will automatically send
    # an empty reply (containing no payload) for every unicast received.
    HOST_WILL_NOT_SUPPLY_REPLY = 0x20
    # UNICAST_REPLIES_POLICY decision. The NCP will only send a reply if it
    # receives a sendReply command from the Host.
    HOST_WILL_SUPPLY_REPLY = 0x21
    # POLL_HANDLER_POLICY default decision. Do not inform the Host when a child polls.
    POLL_HANDLER_IGNORE = 0x30
    # POLL_HANDLER_POLICY decision. Generate a pollHandler callback when a child polls.
    POLL_HANDLER_CALLBACK = 0x31
    # MESSAGE_CONTENTS_IN_CALLBACK_POLICY default decision. Include only the
    # message tag in the messageSentHandler callback.
    MESSAGE_TAG_ONLY_IN_CALLBACK = 0x40
    # MESSAGE_CONTENTS_IN_CALLBACK_POLICY decision. Include both the message
    # tag and the message contents in the messageSentHandler callback.
    MESSAGE_TAG_AND_CONTENTS_IN_CALLBACK = 0x41
    # TC_KEY_REQUEST_POLICY decision. When the Trust Center receives a request
    # for a Trust Center link key, it will be ignored.
    DENY_TC_KEY_REQUESTS = 0x50
    # TC_KEY_REQUEST_POLICY decision. When the Trust Center receives a request for a
    # Trust Center link key, it will reply to it with the corresponding key.
    ALLOW_TC_KEY_REQUESTS_AND_SEND_CURRENT_KEY = 0x51
    # TC_KEY_REQUEST_POLICY decision. When the Trust Center receives a request
    # for a Trust Center link key, it will generate a key to send to the joiner.
    ALLOW_TC_KEY_REQUEST_AND_GENERATE_NEW_KEY = 0x52
    # APP_KEY_REQUEST_POLICY decision. When the Trust Center receives a request
    # for an application link key, it will be ignored.
    DENY_APP_KEY_REQUESTS = 0x60
    # APP_KEY_REQUEST_POLICY decision. When the Trust Center receives a request
    # for an application link key, it will randomly generate a key and send it
    # to both partners.
    ALLOW_APP_KEY_REQUESTS = 0x61
    # Indicates that packet validate library checks are enabled on the NCP.
    PACKET_VALIDATE_LIBRARY_CHECKS_ENABLED = 0x62
    # Indicates that packet validate library checks are NOT enabled on the NCP.
    PACKET_VALIDATE_LIBRARY_CHECKS_DISABLED = 0x63
    # Indicates that the RF4CE stack during discovery and pairing will use standard
    # profile-dependent behavior for the profiles ZRC 1.1 and MSO, while it will fall
    # back to the on/off policies for any other profile.
    RF4CE_DISCOVERY_AND_PAIRING_PROFILE_BEHAVIOR_ENABLED = 0x70
    # Indicates that the RF4CE stack during discovery and pairing will always use the
    # on/off policies.
    RF4CE_DISCOVERY_AND_PAIRING_PROFILE_BEHAVIOR_DISABLED = 0x71
    # Indicates that the RF4CE stack will respond to incoming discovery requests.
    RF4CE_DISCOVERY_REQUEST_RESPOND = 0x72
    # Indicates that the RF4CE stack will ignore incoming discovery requests.
    RF4CE_DISCOVERY_REQUEST_IGNORE = 0x73
    # Indicates that the RF4CE stack will perform all the discovery trials the
    # application specified in the ezspRf4ceDiscovery() call.
    RF4CE_DISCOVERY_MAX_DISCOVERY_TRIALS = 0x74
    # Indicates that the RF4CE stack will prematurely stop the discovery process if a
    # matching discovery response is received.
    RF4CE_DISCOVERY_STOP_ON_MATCHING_RESPONSE = 0x75
    # Indicates that the RF4CE stack will accept new pairings.
    RF4CE_PAIR_REQUEST_ACCEPT = 0x76
    # Indicates that the RF4CE stack will NOT accept new pairings.
    RF4CE_PAIR_REQUEST_DENY = 0x77


class EmberDeviceUpdate(basic.enum8):
    # The status of the device update.

    STANDARD_SECURITY_SECURED_REJOIN = 0x0
    STANDARD_SECURITY_UNSECURED_JOIN = 0x1
    DEVICE_LEFT = 0x2
    STANDARD_SECURITY_UNSECURED_REJOIN = 0x3

    # Removed in EZSPv5
    HIGH_SECURITY_SECURED_REJOIN = 0x4
    HIGH_SECURITY_UNSECURED_JOIN = 0x5
    HIGH_SECURITY_UNSECURED_REJOIN = 0x7


class EmberCounterType(basic.enum8):
    # Defines the events reported to the application by the
    # readAndClearCounters command.

    # The MAC received a broadcast.
    COUNTER_MAC_RX_BROADCAST = 0
    # The MAC transmitted a broadcast.
    COUNTER_MAC_TX_BROADCAST = 1
    # The MAC received a unicast.
    COUNTER_MAC_RX_UNICAST = 2
    # The MAC successfully transmitted a unicast.
    COUNTER_MAC_TX_UNICAST_SUCCESS = 3
    # The MAC retried a unicast.
    COUNTER_MAC_TX_UNICAST_RETRY = 4
    # The MAC unsuccessfully transmitted a unicast.
    COUNTER_MAC_TX_UNICAST_FAILED = 5
    # The APS layer received a data broadcast.
    COUNTER_APS_DATA_RX_BROADCAST = 6
    # The APS layer transmitted a data broadcast.
    COUNTER_APS_DATA_TX_BROADCAST = 7
    # The APS layer received a data unicast.
    COUNTER_APS_DATA_RX_UNICAST = 8
    # The APS layer successfully transmitted a data unicast.
    COUNTER_APS_DATA_TX_UNICAST_SUCCESS = 9
    # The APS layer retried a data unicast.
    COUNTER_APS_DATA_TX_UNICAST_RETRY = 10
    # The APS layer unsuccessfully transmitted a data unicast.
    COUNTER_APS_DATA_TX_UNICAST_FAILED = 11
    # The network layer successfully submitted a new route discovery to the MAC.
    COUNTER_ROUTE_DISCOVERY_INITIATED = 12
    # An entry was added to the neighbor table.
    COUNTER_NEIGHBOR_ADDED = 13
    # An entry was removed from the neighbor table.
    COUNTER_NEIGHBOR_REMOVED = 14
    # A neighbor table entry became stale because it had not been heard from.
    COUNTER_NEIGHBOR_STALE = 15
    # A node joined or rejoined to the network via this node.
    COUNTER_JOIN_INDICATION = 16
    # An entry was removed from the child table.
    COUNTER_CHILD_REMOVED = 17
    # EZSP-UART only. An overflow error occurred in the UART.
    COUNTER_ASH_OVERFLOW_ERROR = 18
    # EZSP-UART only. A framing error occurred in the UART.
    COUNTER_ASH_FRAMING_ERROR = 19
    # EZSP-UART only. An overrun error occurred in the UART.
    COUNTER_ASH_OVERRUN_ERROR = 20
    # A message was dropped at the network layer because the NWK frame counter
    # was not higher than the last message seen from that source.
    COUNTER_NWK_FRAME_COUNTER_FAILURE = 21
    # A message was dropped at the APS layer because the APS frame counter was
    # not higher than the last message seen from that source.
    COUNTER_APS_FRAME_COUNTER_FAILURE = 22
    # Utility counter for general debugging use.
    COUNTER_UTILITY = 23
    # A message was dropped at the APS layer because it had APS encryption but
    # the key associated with the sender has not been authenticated, and thus
    # the key is not authorized for use in APS data messages.
    COUNTER_APS_LINK_KEY_NOT_AUTHORIZED = 24
    # A NWK encrypted message was received but dropped because decryption
    # failed.
    COUNTER_NWK_DECRYPTION_FAILURE = 25
    # An APS encrypted message was received but dropped because decryption
    # failed.
    COUNTER_APS_DECRYPTION_FAILURE = 26
    # The number of times we failed to allocate a set of linked packet buffers.
    # This doesn't necessarily mean that the packet buffer count was 0 at the
    # time, but that the number requested was greater than the number free.
    COUNTER_ALLOCATE_PACKET_BUFFER_FAILURE = 27
    # The number of relayed unicast packets.
    COUNTER_RELAYED_UNICAST = 28
    # The number of times we dropped a packet due to reaching
    # the preset PHY to MAC queue limit (emMaxPhyToMacQueueLength).
    COUNTER_PHY_TO_MAC_QUEUE_LIMIT_REACHED = 29
    # The number of times we dropped a packet due to the
    # packet-validate library checking a packet and rejecting it
    # due to length or other formatting problems.
    COUNTER_PACKET_VALIDATE_LIBRARY_DROPPED_COUNT = 30
    # The number of times the NWK retry queue is full and a
    # new message failed to be added.
    COUNTER_TYPE_NWK_RETRY_OVERFLOW = 31
    # The number of times the PHY layer was unable to transmit
    # due to a failed CCA.
    COUNTER_PHY_CCA_FAIL_COUNT = 32
    # The number of times a NWK broadcast was dropped because
    # the broadcast table was full.
    COUNTER_BROADCAST_TABLE_FULL = 33
    # The number of low priority packet traffic arbitration requests.
    COUNTER_PTA_LO_PRI_REQUESTED = 34
    # The number of high priority packet traffic arbitration requests.
    COUNTER_PTA_HI_PRI_REQUESTED = 35
    # The number of low priority packet traffic arbitration requests denied.
    COUNTER_PTA_LO_PRI_DENIED = 36
    # The number of high priority packet traffic arbitration requests denied.
    COUNTER_PTA_HI_PRI_DENIED = 37
    # The number of aborted low priority packet traffic arbitration transmissions.
    COUNTER_PTA_LO_PRI_TX_ABORTED = 38
    # The number of aborted high priority packet traffic arbitration transmissions.
    COUNTER_PTA_HI_PRI_TX_ABORTED = 39
    # The number of times an address conflict has caused node_id change, and an address
    # conflict error is sent
    COUNTER_ADDRESS_CONFLICT_SENT = 40


class EmberNetworkInitBitmask(basic.bitmap16):
    # Bitmask options for emberNetworkInit().

    # No options for Network Init
    NETWORK_INIT_NO_OPTIONS = 0x0000
    # Save parent info (node ID and EUI64) in a token during joining/rejoin,
    # and restore on reboot.
    NETWORK_INIT_PARENT_INFO_IN_TOKEN = 0x0001
    # Send a rejoin request as an end device on reboot if parent information is
    # persisted. ZB3 end devices must rejoin on reboot.
    NETWORK_INIT_END_DEVICE_REJOIN_ON_REBOOT = 0x0002


class SecureEzspSecurityType(basic.uint32_t):
    """Security type of the Secure EZSP Protocol."""

    TEMPORARY = 0x00000000
    PERMANENT = 0x12345678


class SecureEzspSecurityLevel(basic.enum8):
    """Security level of the Secure EZSP Protocol."""

    ENC_MIC_32 = 0x05


class EmberMultiPhyNwkConfig(basic.enum8):
    """Network configuration for the desired radio interface for multi phy network."""

    # Enable broadcast support on Routers
    BROADCAST_SUPPORT = 0x01


class EmberDutyCycleState(basic.enum8):
    """Duty cycle states."""

    # No Duty cycle tracking or metrics are taking place
    DUTY_CYCLE_TRACKING_OFF = 0
    # Duty Cycle is tracked and has not exceeded any thresholds.
    DUTY_CYCLE_LBT_NORMAL = 1
    # We have exceeded the limited threshold of our total duty cycle allotment.
    DUTY_CYCLE_LBT_LIMITED_THRESHOLD_REACHED = 2
    # We have exceeded the critical threshold of our total duty cycle allotment.
    DUTY_CYCLE_LBT_CRITICAL_THRESHOLD_REACHED = 3
    # We have reached the suspend limit and are blocking all outbound transmissions.
    DUTY_CYCLE_LBT_SUSPEND_LIMIT_REACHED = 4


class EmberRadioPowerMode(basic.enum8):
    """Radio power mode."""

    # The radio receiver is switched on.
    RADIO_POWER_MODE_RX_ON = 0
    # The radio receiver is switched off.
    RADIO_POWER_MODE_OFF = 1


class EmberGpProxyTableEntryStatus(basic.enum8):
    """The proxy table entry status."""

    # The GP table entry is in use for a Proxy Table Entry.
    ACTIVE = 0x01
    # The proxy table entry is not in use.
    UNUSED = 0xFF


class EmberGpSinkTableEntryStatus(basic.enum8):
    """The sink table entry status."""

    # The GP table entry is in use for a Sink Table Entry.
    ACTIVE = 0x01
    # The proxy table entry is not in use.
    UNUSED = 0xFF


class EmberJoinMethod(basic.enum8):
    # The type of method used for joining.

    # Normally devices use MAC Association to join a network, which respects
    # the "permit joining" flag in the MAC Beacon. For mobile nodes this value
    # causes the device to use an Ember Mobile Node Join, which is functionally
    # equivalent to a MAC association. This value should be used by default.
    USE_MAC_ASSOCIATION = 0x0
    # For those networks where the "permit joining" flag is never turned on,
    # they will need to use a ZigBee NWK Rejoin. This value causes the rejoin
    # to be sent without NWK security and the Trust Center will be asked to
    # send the NWK key to the device. The NWK key sent to the device can be
    # encrypted with the device's corresponding Trust Center link key. That is
    # determined by the ::EmberJoinDecision on the Trust Center returned by the
    # ::emberTrustCenterJoinHandler(). For a mobile node this value will cause
    # it to use an Ember Mobile node rejoin, which is functionally equivalent.
    USE_NWK_REJOIN = 0x1
    # For those networks where the "permit joining" flag is never turned on,
    # they will need to use a NWK Rejoin. If those devices have been
    # preconfigured with the NWK key (including sequence number) they can use a
    # secured rejoin. This is only necessary for end devices since they need a
    # parent. Routers can simply use the ::USE_NWK_COMMISSIONING join method
    # below.
    USE_NWK_REJOIN_HAVE_NWK_KEY = 0x2
    # For those networks where all network and security information is known
    # ahead of time, a router device may be commissioned such that it does not
    # need to send any messages to begin communicating on the network.
    USE_CONFIGURED_NWK_STATE = 0x3


class EmberEntropySource(basic.enum8):
    """Entropy sources."""

    # Entropy source error
    ENTROPY_SOURCE_ERROR = 0
    # Entropy source is the radio.
    ENTROPY_SOURCE_RADIO = 1
    # Entropy source is the TRNG powered by mbed TLS.
    ENTROPY_SOURCE_MBEDTLS_TRNG = 2
    # Entropy source is powered by mbed TLS, the source is not TRNG.
    ENTROPY_SOURCE_MBEDTLS = 3


class SecurityManagerDerivedKeyTypeV12(basic.enum8):
    """Derived keys are calculated when performing Zigbee crypto operations.
    The stack makes use of these derivations.
    """

    # Perform no derivation; use the key as is.
    NONE = 0
    # Perform the Key-Transport-Key hash.
    KEY_TRANSPORT_KEY = 1
    # Perform the Key-Load-Key hash.
    KEY_LOAD_KEY = 2
    # Perform the Verify Key hash.
    VERIFY_KEY = 3
    # Perform a simple AES hash of the key for TC backup.
    TC_SWAP_OUT_KEY = 4
    # For a TC using hashed link keys, hashed the root key against the supplied EUI in
    # context.
    TC_HASHED_LINK_KEY = 5


class SecurityManagerDerivedKeyTypeV13(basic.enum16):
    """Derived keys are calculated when performing Zigbee crypto operations.
    The stack makes use of these derivations.
    """

    # Perform no derivation; use the key as is.
    NONE = 0
    # Perform the Key-Transport-Key hash.
    KEY_TRANSPORT_KEY = 1
    # Perform the Key-Load-Key hash.
    KEY_LOAD_KEY = 2
    # Perform the Verify Key hash.
    VERIFY_KEY = 3
    # Perform a simple AES hash of the key for TC backup.
    TC_SWAP_OUT_KEY = 4
    # For a TC using hashed link keys, hashed the root key against the supplied EUI in
    # context.
    TC_HASHED_LINK_KEY = 5
