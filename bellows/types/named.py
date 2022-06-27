import zigpy.types as ztypes
import zigpy.zdo.types as zdo_t

from . import basic

Channels = ztypes.Channels
EmberEUI64 = ztypes.EUI64


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


class EmberNodeId(basic.HexRepr, basic.uint16_t):
    # 16-bit ZigBee network address.
    _hex_len = 4


class EmberPanId(basic.HexRepr, basic.uint16_t):
    # 802.15.4 PAN ID.
    _hex_len = 4


class EmberMulticastId(basic.HexRepr, basic.uint16_t):
    # 16-bit ZigBee multicast group identifier.
    _hex_len = 4


class EmberLibraryId(basic.uint8_t):
    # The presence and status of the Ember id.
    pass


class EmberLibraryStatus(basic.uint8_t):
    # The presence and status of the Ember library.
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
    # Received frame is unsecure, when security is established
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
    # The software installed on the hardware doesn't recognize the hardware
    # radio type.
    PHY_OSCILLATOR_CHECK_FAILED = 0x8E
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
    # TRUST_CENTER_MASTER_KEY_NOT_SET 0xA7 There was an attempt to form a
    # network using commercial security without setting the Trust Center master
    # key first.
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
    # The stack accepted the command and is currently processing the request.
    # The results will be returned via an appropriate handler.
    OPERATION_IN_PROGRESS = 0xBA
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

    # TODO: 0x0080 is unknown


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
    USE_NWK_COMMISSIONING = 0x3


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


class EmberKeyData(basic.fixed_list(16, basic.uint8_t)):
    """A 128-bit key."""


class EmberCertificateData(basic.fixed_list(48, basic.uint8_t)):
    """The implicit certificate used in CBKE."""


class EmberPublicKeyData(basic.fixed_list(22, basic.uint8_t)):
    """The public key data used in CBKE."""


class EmberPrivateKeyData(basic.fixed_list(21, basic.uint8_t)):
    """The private key data used in CBKE."""


class EmberSmacData(basic.fixed_list(16, basic.uint8_t)):
    """The Shared Message Authentication Code data used in CBKE."""


class EmberSignatureData(basic.fixed_list(42, basic.uint8_t)):
    """An ECDSA signature."""


class EmberCertificate283k1Data(basic.fixed_list(74, basic.uint8_t)):
    """The implicit certificate used in CBKE."""


class EmberPublicKey283k1Data(basic.fixed_list(37, basic.uint8_t)):
    """The 283k1 public key data used in CBKE."""


class EmberPrivateKey283k1Data(basic.fixed_list(36, basic.uint8_t)):
    """The 283k1 private key data used in CBKE."""


class EmberSignature283k1Data(basic.fixed_list(72, basic.uint8_t)):
    """An 283k1 ECDSA signature data."""


class EmberMessageDigest(basic.fixed_list(16, basic.uint8_t)):
    """The calculated digest of a message"""


class sl_Status(basic.enum32):
    # SL Status Codes.
    #
    # Status Defines
    # Generic Errors
    #  No error.
    SL_STATUS_OK = 0x0000
    #  Generic error.
    SL_STATUS_FAIL = 0x0001
    # State Errors
    #  Generic invalid state error.
    SL_STATUS_INVALID_STATE = 0x0002
    #  Module is not ready for requested operation.
    SL_STATUS_NOT_READY = 0x0003
    #  Module is busy and cannot carry out requested operation.
    SL_STATUS_BUSY = 0x0004
    #  Operation is in progress and not yet complete (pass or fail).
    SL_STATUS_IN_PROGRESS = 0x0005
    #  Operation aborted.
    SL_STATUS_ABORT = 0x0006
    #  Operation timed out.
    SL_STATUS_TIMEOUT = 0x0007
    #  Operation not allowed per permissions.
    SL_STATUS_PERMISSION = 0x0008
    #  Non-blocking operation would block.
    SL_STATUS_WOULD_BLOCK = 0x0009
    #  Operation/module is Idle, cannot carry requested operation.
    SL_STATUS_IDLE = 0x000A
    #  Operation cannot be done while construct is waiting.
    SL_STATUS_IS_WAITING = 0x000B
    #  No task/construct waiting/pending for that action/event.
    SL_STATUS_NONE_WAITING = 0x000C
    #  Operation cannot be done while construct is suspended.
    SL_STATUS_SUSPENDED = 0x000D
    #  Feature not available due to software configuration.
    SL_STATUS_NOT_AVAILABLE = 0x000E
    #  Feature not supported.
    SL_STATUS_NOT_SUPPORTED = 0x000F
    #  Initialization failed.
    SL_STATUS_INITIALIZATION = 0x0010
    #  Module has not been initialized.
    SL_STATUS_NOT_INITIALIZED = 0x0011
    #  Module has already been initialized.
    SL_STATUS_ALREADY_INITIALIZED = 0x0012
    #  Object/construct has been deleted.
    SL_STATUS_DELETED = 0x0013
    #  Illegal call from ISR.
    SL_STATUS_ISR = 0x0014
    #  Illegal call because network is up.
    SL_STATUS_NETWORK_UP = 0x0015
    #  Illegal call because network is down.
    SL_STATUS_NETWORK_DOWN = 0x0016
    #  Failure due to not being joined in a network.
    SL_STATUS_NOT_JOINED = 0x0017
    #  Invalid operation as there are no beacons.
    SL_STATUS_NO_BEACONS = 0x0018
    # Allocation/ownership Errors
    #  Generic allocation error.
    SL_STATUS_ALLOCATION_FAILED = 0x0019
    #  No more resource available to perform the operation.
    SL_STATUS_NO_MORE_RESOURCE = 0x001A
    #  Item/list/queue is empty.
    SL_STATUS_EMPTY = 0x001B
    #  Item/list/queue is full.
    SL_STATUS_FULL = 0x001C
    #  Item would overflow.
    SL_STATUS_WOULD_OVERFLOW = 0x001D
    #  Item/list/queue has been overflowed.
    SL_STATUS_HAS_OVERFLOWED = 0x001E
    #  Generic ownership error.
    SL_STATUS_OWNERSHIP = 0x001F
    #  Already/still owning resource.
    SL_STATUS_IS_OWNER = 0x0020
    # Invalid Parameters Errors
    #  Generic invalid argument or consequence of invalid argument.
    SL_STATUS_INVALID_PARAMETER = 0x0021
    #  Invalid null pointer received as argument.
    SL_STATUS_NULL_POINTER = 0x0022
    #  Invalid configuration provided.
    SL_STATUS_INVALID_CONFIGURATION = 0x0023
    #  Invalid mode.
    SL_STATUS_INVALID_MODE = 0x0024
    #  Invalid handle.
    SL_STATUS_INVALID_HANDLE = 0x0025
    #  Invalid type for operation.
    SL_STATUS_INVALID_TYPE = 0x0026
    #  Invalid index.
    SL_STATUS_INVALID_INDEX = 0x0027
    #  Invalid range.
    SL_STATUS_INVALID_RANGE = 0x0028
    #  Invalid key.
    SL_STATUS_INVALID_KEY = 0x0029
    #  Invalid credentials.
    SL_STATUS_INVALID_CREDENTIALS = 0x002A
    #  Invalid count.
    SL_STATUS_INVALID_COUNT = 0x002B
    #  Invalid signature / verification failed.
    SL_STATUS_INVALID_SIGNATURE = 0x002C
    #  Item could not be found.
    SL_STATUS_NOT_FOUND = 0x002D
    #  Item already exists.
    SL_STATUS_ALREADY_EXISTS = 0x002E
    # IO/Communication Errors
    #  Generic I/O failure.
    SL_STATUS_IO = 0x002F
    #  I/O failure due to timeout.
    SL_STATUS_IO_TIMEOUT = 0x0030
    #  Generic transmission error.
    SL_STATUS_TRANSMIT = 0x0031
    #  Transmit underflowed.
    SL_STATUS_TRANSMIT_UNDERFLOW = 0x0032
    #  Transmit is incomplete.
    SL_STATUS_TRANSMIT_INCOMPLETE = 0x0033
    #  Transmit is busy.
    SL_STATUS_TRANSMIT_BUSY = 0x0034
    #  Generic reception error.
    SL_STATUS_RECEIVE = 0x0035
    #  Failed to read on/via given object.
    SL_STATUS_OBJECT_READ = 0x0036
    #  Failed to write on/via given object.
    SL_STATUS_OBJECT_WRITE = 0x0037
    #  Message is too long.
    SL_STATUS_MESSAGE_TOO_LONG = 0x0038
    # EEPROM/Flash Errors
    SL_STATUS_EEPROM_MFG_VERSION_MISMATCH = 0x0039
    SL_STATUS_EEPROM_STACK_VERSION_MISMATCH = 0x003A
    #  Flash write is inhibited.
    SL_STATUS_FLASH_WRITE_INHIBITED = 0x003B
    #  Flash verification failed.
    SL_STATUS_FLASH_VERIFY_FAILED = 0x003C
    #  Flash programming failed.
    SL_STATUS_FLASH_PROGRAM_FAILED = 0x003D
    #  Flash erase failed.
    SL_STATUS_FLASH_ERASE_FAILED = 0x003E
    # MAC Errors
    SL_STATUS_MAC_NO_DATA = 0x003F
    SL_STATUS_MAC_NO_ACK_RECEIVED = 0x0040
    SL_STATUS_MAC_INDIRECT_TIMEOUT = 0x0041
    SL_STATUS_MAC_UNKNOWN_HEADER_TYPE = 0x0042
    SL_STATUS_MAC_ACK_HEADER_TYPE = 0x0043
    SL_STATUS_MAC_COMMAND_TRANSMIT_FAILURE = 0x0044
    # CLI_STORAGE Errors
    #  Error in open NVM
    SL_STATUS_CLI_STORAGE_NVM_OPEN_ERROR = 0x0045
    # Security status codes
    #  Image checksum is not valid.
    SL_STATUS_SECURITY_IMAGE_CHECKSUM_ERROR = 0x0046
    #  Decryption failed
    SL_STATUS_SECURITY_DECRYPT_ERROR = 0x0047
    # Command status codes
    #  Command was not recognized
    SL_STATUS_COMMAND_IS_INVALID = 0x0048
    #  Command or parameter maximum length exceeded
    SL_STATUS_COMMAND_TOO_LONG = 0x0049
    #  Data received does not form a complete command
    SL_STATUS_COMMAND_INCOMPLETE = 0x004A
    # Misc Errors
    #  Bus error, e.g. invalid DMA address
    SL_STATUS_BUS_ERROR = 0x004B
    # Unified MAC Errors
    SL_STATUS_CCA_FAILURE = 0x004C  #
    # Scan errors
    SL_STATUS_MAC_SCANNING = 0x004D
    SL_STATUS_MAC_INCORRECT_SCAN_TYPE = 0x004E
    SL_STATUS_INVALID_CHANNEL_MASK = 0x004F
    SL_STATUS_BAD_SCAN_DURATION = 0x0050
    # Bluetooth status codes
    #  Bonding procedure can't be started because device has no space
    #  left for bond.
    SL_STATUS_BT_OUT_OF_BONDS = 0x0402
    #  Unspecified error
    SL_STATUS_BT_UNSPECIFIED = 0x0403
    #  Hardware failure
    SL_STATUS_BT_HARDWARE = 0x0404
    #  The bonding does not exist.
    SL_STATUS_BT_NO_BONDING = 0x0406
    #  Error using crypto functions
    SL_STATUS_BT_CRYPTO = 0x0407
    #  Data was corrupted.
    SL_STATUS_BT_DATA_CORRUPTED = 0x0408
    #  Invalid periodic advertising sync handle
    SL_STATUS_BT_INVALID_SYNC_HANDLE = 0x040A
    #  Bluetooth cannot be used on this hardware
    SL_STATUS_BT_INVALID_MODULE_ACTION = 0x040B
    #  Error received from radio
    SL_STATUS_BT_RADIO = 0x040C
    #  Returned when remote disconnects the connection-oriented channel by sending
    #  disconnection request.
    SL_STATUS_BT_L2CAP_REMOTE_DISCONNECTED = 0x040D
    #  Returned when local host disconnect the connection-oriented channel by sending
    #  disconnection request.
    SL_STATUS_BT_L2CAP_LOCAL_DISCONNECTED = 0x040E
    #  Returned when local host did not find a connection-oriented channel with given
    #  destination CID.
    SL_STATUS_BT_L2CAP_CID_NOT_EXIST = 0x040F
    #  Returned when connection-oriented channel disconnected due to LE connection is dropped.
    SL_STATUS_BT_L2CAP_LE_DISCONNECTED = 0x0410
    #  Returned when connection-oriented channel disconnected due to remote end send data
    #  even without credit.
    SL_STATUS_BT_L2CAP_FLOW_CONTROL_VIOLATED = 0x0412
    #  Returned when connection-oriented channel disconnected due to remote end send flow
    #  control credits exceed 65535.
    SL_STATUS_BT_L2CAP_FLOW_CONTROL_CREDIT_OVERFLOWED = 0x0413
    #  Returned when connection-oriented channel has run out of flow control credit and
    #  local application still trying to send data.
    SL_STATUS_BT_L2CAP_NO_FLOW_CONTROL_CREDIT = 0x0414
    #  Returned when connection-oriented channel has not received connection response message
    #  within maximum timeout.
    SL_STATUS_BT_L2CAP_CONNECTION_REQUEST_TIMEOUT = 0x0415
    #  Returned when local host received a connection-oriented channel connection response
    #  with an invalid destination CID.
    SL_STATUS_BT_L2CAP_INVALID_CID = 0x0416
    #  Returned when local host application tries to send a command which is not suitable
    #  for L2CAP channel's current state.
    SL_STATUS_BT_L2CAP_WRONG_STATE = 0x0417
    #  Flash reserved for PS store is full
    SL_STATUS_BT_PS_STORE_FULL = 0x041B
    #  PS key not found
    SL_STATUS_BT_PS_KEY_NOT_FOUND = 0x041C
    #  Mismatched or insufficient security level
    SL_STATUS_BT_APPLICATION_MISMATCHED_OR_INSUFFICIENT_SECURITY = 0x041D
    #  Encrypion/decryption operation failed.
    SL_STATUS_BT_APPLICATION_ENCRYPTION_DECRYPTION_ERROR = 0x041E
    # Bluetooth controller status codes
    #  Connection does not exist, or connection open request was cancelled.
    SL_STATUS_BT_CTRL_UNKNOWN_CONNECTION_IDENTIFIER = 0x1002
    #  Pairing or authentication failed due to incorrect results in the pairing or
    #  authentication procedure. This could be due to an incorrect PIN or Link Key
    SL_STATUS_BT_CTRL_AUTHENTICATION_FAILURE = 0x1005
    #  Pairing failed because of missing PIN, or authentication failed because of missing Key
    SL_STATUS_BT_CTRL_PIN_OR_KEY_MISSING = 0x1006
    #  Controller is out of memory.
    SL_STATUS_BT_CTRL_MEMORY_CAPACITY_EXCEEDED = 0x1007
    #  Link supervision timeout has expired.
    SL_STATUS_BT_CTRL_CONNECTION_TIMEOUT = 0x1008
    #  Controller is at limit of connections it can support.
    SL_STATUS_BT_CTRL_CONNECTION_LIMIT_EXCEEDED = 0x1009
    #  The Synchronous Connection Limit to a Device Exceeded error code indicates that
    #  the Controller has reached the limit to the number of synchronous connections that
    #  can be achieved to a device.
    SL_STATUS_BT_CTRL_SYNCHRONOUS_CONNECTION_LIMIT_EXCEEDED = 0x100A
    #  The ACL Connection Already Exists error code indicates that an attempt to create
    #  a new ACL Connection to a device when there is already a connection to this device.
    SL_STATUS_BT_CTRL_ACL_CONNECTION_ALREADY_EXISTS = 0x100B
    #  Command requested cannot be executed because the Controller is in a state where
    #  it cannot process this command at this time.
    SL_STATUS_BT_CTRL_COMMAND_DISALLOWED = 0x100C
    #  The Connection Rejected Due To Limited Resources error code indicates that an
    #  incoming connection was rejected due to limited resources.
    SL_STATUS_BT_CTRL_CONNECTION_REJECTED_DUE_TO_LIMITED_RESOURCES = 0x100D
    #  The Connection Rejected Due To Security Reasons error code indicates that a
    #  connection was rejected due to security requirements not being fulfilled, like
    #  authentication or pairing.
    SL_STATUS_BT_CTRL_CONNECTION_REJECTED_DUE_TO_SECURITY_REASONS = 0x100E
    #  The Connection was rejected because this device does not accept the BD_ADDR.
    #  This may be because the device will only accept connections from specific BD_ADDRs.
    SL_STATUS_BT_CTRL_CONNECTION_REJECTED_DUE_TO_UNACCEPTABLE_BD_ADDR = 0x100F
    #  The Connection Accept Timeout has been exceeded for this connection attempt.
    SL_STATUS_BT_CTRL_CONNECTION_ACCEPT_TIMEOUT_EXCEEDED = 0x1010
    #  A feature or parameter value in the HCI command is not supported.
    SL_STATUS_BT_CTRL_UNSUPPORTED_FEATURE_OR_PARAMETER_VALUE = 0x1011
    #  Command contained invalid parameters.
    SL_STATUS_BT_CTRL_INVALID_COMMAND_PARAMETERS = 0x1012
    #  User on the remote device terminated the connection.
    SL_STATUS_BT_CTRL_REMOTE_USER_TERMINATED = 0x1013
    #  The remote device terminated the connection because of low resources
    SL_STATUS_BT_CTRL_REMOTE_DEVICE_TERMINATED_CONNECTION_DUE_TO_LOW_RESOURCES = 0x1014
    #  Remote Device Terminated Connection due to Power Off
    SL_STATUS_BT_CTRL_REMOTE_POWERING_OFF = 0x1015
    #  Local device terminated the connection.
    SL_STATUS_BT_CTRL_CONNECTION_TERMINATED_BY_LOCAL_HOST = 0x1016
    #  The Controller is disallowing an authentication or pairing procedure because
    #  too little time has elapsed since the last authentication or pairing attempt failed.
    SL_STATUS_BT_CTRL_REPEATED_ATTEMPTS = 0x1017
    #  The device does not allow pairing. This can be for example, when a device only
    #  allows pairing during a certain time window after some user input allows pairing
    SL_STATUS_BT_CTRL_PAIRING_NOT_ALLOWED = 0x1018
    #  The remote device does not support the feature associated with the issued command.
    SL_STATUS_BT_CTRL_UNSUPPORTED_REMOTE_FEATURE = 0x101A
    #  No other error code specified is appropriate to use.
    SL_STATUS_BT_CTRL_UNSPECIFIED_ERROR = 0x101F
    #  Connection terminated due to link-layer procedure timeout.
    SL_STATUS_BT_CTRL_LL_RESPONSE_TIMEOUT = 0x1022
    #  LL procedure has collided with the same transaction or procedure that is already
    #  in progress.
    SL_STATUS_BT_CTRL_LL_PROCEDURE_COLLISION = 0x1023
    #  The requested encryption mode is not acceptable at this time.
    SL_STATUS_BT_CTRL_ENCRYPTION_MODE_NOT_ACCEPTABLE = 0x1025
    #  Link key cannot be changed because a fixed unit key is being used.
    SL_STATUS_BT_CTRL_LINK_KEY_CANNOT_BE_CHANGED = 0x1026
    #  LMP PDU or LL PDU that includes an instant cannot be performed because the instan
    #  when this would have occurred has passed.
    SL_STATUS_BT_CTRL_INSTANT_PASSED = 0x1028
    #  It was not possible to pair as a unit key was requested and it is not supported.
    SL_STATUS_BT_CTRL_PAIRING_WITH_UNIT_KEY_NOT_SUPPORTED = 0x1029
    #  LMP transaction was started that collides with an ongoing transaction.
    SL_STATUS_BT_CTRL_DIFFERENT_TRANSACTION_COLLISION = 0x102A
    #  The Controller cannot perform channel assessment because it is not supported.
    SL_STATUS_BT_CTRL_CHANNEL_ASSESSMENT_NOT_SUPPORTED = 0x102E
    #  The HCI command or LMP PDU sent is only possible on an encrypted link.
    SL_STATUS_BT_CTRL_INSUFFICIENT_SECURITY = 0x102F
    #  A parameter value requested is outside the mandatory range of parameters for the
    #  given HCI command or LMP PDU.
    SL_STATUS_BT_CTRL_PARAMETER_OUT_OF_MANDATORY_RANGE = 0x1030
    #  The IO capabilities request or response was rejected because the sending Host does
    #  not support Secure Simple Pairing even though the receiving Link Manager does.
    SL_STATUS_BT_CTRL_SIMPLE_PAIRING_NOT_SUPPORTED_BY_HOST = 0x1037
    #  The Host is busy with another pairing operation and unable to support the requested
    #  pairing. The receiving device should retry pairing again later.
    SL_STATUS_BT_CTRL_HOST_BUSY_PAIRING = 0x1038
    #  The Controller could not calculate an appropriate value for the Channel selection operation.
    SL_STATUS_BT_CTRL_CONNECTION_REJECTED_DUE_TO_NO_SUITABLE_CHANNEL_FOUND = 0x1039
    #  Operation was rejected because the controller is busy and unable to process the request.
    SL_STATUS_BT_CTRL_CONTROLLER_BUSY = 0x103A
    #  Remote device terminated the connection because of an unacceptable connection interval.
    SL_STATUS_BT_CTRL_UNACCEPTABLE_CONNECTION_INTERVAL = 0x103B
    #  Ddvertising for a fixed duration completed or, for directed advertising, that advertising
    #  completed without a connection being created.
    SL_STATUS_BT_CTRL_ADVERTISING_TIMEOUT = 0x103C
    #  Connection was terminated because the Message Integrity Check (MIC) failed on a
    #  received packet.
    SL_STATUS_BT_CTRL_CONNECTION_TERMINATED_DUE_TO_MIC_FAILURE = 0x103D
    #  LL initiated a connection but the connection has failed to be established. Controller did not receive
    #  any packets from remote end.
    SL_STATUS_BT_CTRL_CONNECTION_FAILED_TO_BE_ESTABLISHED = 0x103E
    #  The MAC of the 802.11 AMP was requested to connect to a peer, but the connection failed.
    SL_STATUS_BT_CTRL_MAC_CONNECTION_FAILED = 0x103F
    #  The master, at this time, is unable to make a coarse adjustment to the piconet clock,
    #  using the supplied parameters. Instead the master will attempt to move the clock using clock dragging.
    SL_STATUS_BT_CTRL_COARSE_CLOCK_ADJUSTMENT_REJECTED_BUT_WILL_TRY_TO_ADJUST_USING_CLOCK_DRAGGING = (
        0x1040
    )
    #  A command was sent from the Host that should identify an Advertising or Sync handle, but the
    #  Advertising or Sync handle does not exist.
    SL_STATUS_BT_CTRL_UNKNOWN_ADVERTISING_IDENTIFIER = 0x1042
    #  Number of operations requested has been reached and has indicated the completion of the activity
    #  (e.g., advertising or scanning).
    SL_STATUS_BT_CTRL_LIMIT_REACHED = 0x1043
    #  A request to the Controller issued by the Host and still pending was successfully canceled.
    SL_STATUS_BT_CTRL_OPERATION_CANCELLED_BY_HOST = 0x1044
    #  An attempt was made to send or receive a packet that exceeds the maximum allowed packet l
    SL_STATUS_BT_CTRL_PACKET_TOO_LONG = 0x1045
    # Bluetooth attribute status codes
    #  The attribute handle given was not valid on this server
    SL_STATUS_BT_ATT_INVALID_HANDLE = 0x1101
    #  The attribute cannot be read
    SL_STATUS_BT_ATT_READ_NOT_PERMITTED = 0x1102
    #  The attribute cannot be written
    SL_STATUS_BT_ATT_WRITE_NOT_PERMITTED = 0x1103
    #  The attribute PDU was invalid
    SL_STATUS_BT_ATT_INVALID_PDU = 0x1104
    #  The attribute requires authentication before it can be read or written.
    SL_STATUS_BT_ATT_INSUFFICIENT_AUTHENTICATION = 0x1105
    #  Attribute Server does not support the request received from the client.
    SL_STATUS_BT_ATT_REQUEST_NOT_SUPPORTED = 0x1106
    #  Offset specified was past the end of the attribute
    SL_STATUS_BT_ATT_INVALID_OFFSET = 0x1107
    #  The attribute requires authorization before it can be read or written.
    SL_STATUS_BT_ATT_INSUFFICIENT_AUTHORIZATION = 0x1108
    #  Too many prepare writes have been queued
    SL_STATUS_BT_ATT_PREPARE_QUEUE_FULL = 0x1109
    #  No attribute found within the given attribute handle range.
    SL_STATUS_BT_ATT_ATT_NOT_FOUND = 0x110A
    #  The attribute cannot be read or written using the Read Blob Request
    SL_STATUS_BT_ATT_ATT_NOT_LONG = 0x110B
    #  The Encryption Key Size used for encrypting this link is insufficient.
    SL_STATUS_BT_ATT_INSUFFICIENT_ENC_KEY_SIZE = 0x110C
    #  The attribute value length is invalid for the operation
    SL_STATUS_BT_ATT_INVALID_ATT_LENGTH = 0x110D
    #  The attribute request that was requested has encountered an error that was unlikely, and
    #  therefore could not be completed as requested.
    SL_STATUS_BT_ATT_UNLIKELY_ERROR = 0x110E
    #  The attribute requires encryption before it can be read or written.
    SL_STATUS_BT_ATT_INSUFFICIENT_ENCRYPTION = 0x110F
    #  The attribute type is not a supported grouping attribute as defined by a higher layer
    #  specification.
    SL_STATUS_BT_ATT_UNSUPPORTED_GROUP_TYPE = 0x1110
    #  Insufficient Resources to complete the request
    SL_STATUS_BT_ATT_INSUFFICIENT_RESOURCES = 0x1111
    #  The server requests the client to rediscover the database.
    SL_STATUS_BT_ATT_OUT_OF_SYNC = 0x1112
    #  The attribute parameter value was not allowed.
    SL_STATUS_BT_ATT_VALUE_NOT_ALLOWED = 0x1113
    #  When this is returned in a BGAPI response, the application tried to read or write the
    #  value of a user attribute from the GATT databa
    SL_STATUS_BT_ATT_APPLICATION = 0x1180
    #  The requested write operation cannot be fulfilled for reasons other than permissions.
    SL_STATUS_BT_ATT_WRITE_REQUEST_REJECTED = 0x11FC
    #  The Client Characteristic Configuration descriptor is not configured according to the
    #  requirements of the profile or service.
    SL_STATUS_BT_ATT_CLIENT_CHARACTERISTIC_CONFIGURATION_DESCRIPTOR_IMPROPERLY_CONFIGURED = (
        0x11FD
    )
    #  The profile or service request cannot be serviced because an operation that has been
    #  previously triggered is still in progress.
    SL_STATUS_BT_ATT_PROCEDURE_ALREADY_IN_PROGRESS = 0x11FE
    #  The attribute value is out of range as defined by a profile or service specification.
    SL_STATUS_BT_ATT_OUT_OF_RANGE = 0x11FF
    # Bluetooth Security Manager Protocol status codes
    #  The user input of passkey failed, for example, the user cancelled the operation
    SL_STATUS_BT_SMP_PASSKEY_ENTRY_FAILED = 0x1201
    #  Out of Band data is not available for authentication
    SL_STATUS_BT_SMP_OOB_NOT_AVAILABLE = 0x1202
    #  The pairing procedure cannot be performed as authentication requirements cannot be
    #  met due to IO capabilities of one or both devices
    SL_STATUS_BT_SMP_AUTHENTICATION_REQUIREMENTS = 0x1203
    #  The confirm value does not match the calculated compare value
    SL_STATUS_BT_SMP_CONFIRM_VALUE_FAILED = 0x1204
    #  Pairing is not supported by the device
    SL_STATUS_BT_SMP_PAIRING_NOT_SUPPORTED = 0x1205
    #  The resultant encryption key size is insufficient for the security requirements of this device
    SL_STATUS_BT_SMP_ENCRYPTION_KEY_SIZE = 0x1206
    #  The SMP command received is not supported on this device
    SL_STATUS_BT_SMP_COMMAND_NOT_SUPPORTED = 0x1207
    #  Pairing failed due to an unspecified reason
    SL_STATUS_BT_SMP_UNSPECIFIED_REASON = 0x1208
    #  Pairing or authentication procedure is disallowed because too little time has elapsed
    #  since last pairing request or security request
    SL_STATUS_BT_SMP_REPEATED_ATTEMPTS = 0x1209
    #  The Invalid Parameters error code indicates: the command length is invalid or a parameter
    #  is outside of the specified range.
    SL_STATUS_BT_SMP_INVALID_PARAMETERS = 0x120A
    #  Indicates to the remote device that the DHKey Check value received doesn't match the one
    #  calculated by the local device.
    SL_STATUS_BT_SMP_DHKEY_CHECK_FAILED = 0x120B
    #  Indicates that the confirm values in the numeric comparison protocol do not match.
    SL_STATUS_BT_SMP_NUMERIC_COMPARISON_FAILED = 0x120C
    #  Indicates that the pairing over the LE transport failed due to a Pairing Request
    #  sent over the BR/EDR transport in process.
    SL_STATUS_BT_SMP_BREDR_PAIRING_IN_PROGRESS = 0x120D
    #  Indicates that the BR/EDR Link Key generated on the BR/EDR transport cannot be used
    #  to derive and distribute keys for the LE transport.
    SL_STATUS_BT_SMP_CROSS_TRANSPORT_KEY_DERIVATION_GENERATION_NOT_ALLOWED = 0x120E
    #  Indicates that the device chose not to accept a distributed key.
    SL_STATUS_BT_SMP_KEY_REJECTED = 0x120F
    # Bluetooth Mesh status codes
    #  Returned when trying to add a key or some other unique resource with an ID which already exists
    SL_STATUS_BT_MESH_ALREADY_EXISTS = 0x0501
    #  Returned when trying to manipulate a key or some other resource with an ID which does not exist
    SL_STATUS_BT_MESH_DOES_NOT_EXIST = 0x0502
    #  Returned when an operation cannot be executed because a pre-configured limit for keys,
    #  key bindings, elements, models, virtual addresses, provisioned devices, or provisioning sessions is reached
    SL_STATUS_BT_MESH_LIMIT_REACHED = 0x0503
    #  Returned when trying to use a reserved address or add a "pre-provisioned" device
    #  using an address already used by some other device
    SL_STATUS_BT_MESH_INVALID_ADDRESS = 0x0504
    #  In a BGAPI response, the user supplied malformed data; in a BGAPI event, the remote
    #  end responded with malformed or unrecognized data
    SL_STATUS_BT_MESH_MALFORMED_DATA = 0x0505
    #  An attempt was made to initialize a subsystem that was already initialized.
    SL_STATUS_BT_MESH_ALREADY_INITIALIZED = 0x0506
    #  An attempt was made to use a subsystem that wasn't initialized yet. Call the
    #  subsystem's init function first.
    SL_STATUS_BT_MESH_NOT_INITIALIZED = 0x0507
    #  Returned when trying to establish a friendship as a Low Power Node, but no acceptable
    #  friend offer message was received.
    SL_STATUS_BT_MESH_NO_FRIEND_OFFER = 0x0508
    #  Provisioning link was unexpectedly closed before provisioning was complete.
    SL_STATUS_BT_MESH_PROV_LINK_CLOSED = 0x0509
    #  An unrecognized provisioning PDU was received.
    SL_STATUS_BT_MESH_PROV_INVALID_PDU = 0x050A
    #  A provisioning PDU with wrong length or containing field values that are out of
    #  bounds was received.
    SL_STATUS_BT_MESH_PROV_INVALID_PDU_FORMAT = 0x050B
    #  An unexpected (out of sequence) provisioning PDU was received.
    SL_STATUS_BT_MESH_PROV_UNEXPECTED_PDU = 0x050C
    #  The computed confirmation value did not match the expected value.
    SL_STATUS_BT_MESH_PROV_CONFIRMATION_FAILED = 0x050D
    #  Provisioning could not be continued due to insufficient resources.
    SL_STATUS_BT_MESH_PROV_OUT_OF_RESOURCES = 0x050E
    #  The provisioning data block could not be decrypted.
    SL_STATUS_BT_MESH_PROV_DECRYPTION_FAILED = 0x050F
    #  An unexpected error happened during provisioning.
    SL_STATUS_BT_MESH_PROV_UNEXPECTED_ERROR = 0x0510
    #  Device could not assign unicast addresses to all of its elements.
    SL_STATUS_BT_MESH_PROV_CANNOT_ASSIGN_ADDR = 0x0511
    #  Returned when trying to reuse an address of a previously deleted device before an
    #  IV Index Update has been executed.
    SL_STATUS_BT_MESH_ADDRESS_TEMPORARILY_UNAVAILABLE = 0x0512
    #  Returned when trying to assign an address that is used by one of the devices in the
    #  Device Database, or by the Provisioner itself.
    SL_STATUS_BT_MESH_ADDRESS_ALREADY_USED = 0x0513
    #  Application key or publish address are not set
    SL_STATUS_BT_MESH_PUBLISH_NOT_CONFIGURED = 0x0514
    #  Application key is not bound to a model
    SL_STATUS_BT_MESH_APP_KEY_NOT_BOUND = 0x0515
    # Bluetooth Mesh foundation status codes
    #  Returned when address in request was not valid
    SL_STATUS_BT_MESH_FOUNDATION_INVALID_ADDRESS = 0x1301
    #  Returned when model identified is not found for a given element
    SL_STATUS_BT_MESH_FOUNDATION_INVALID_MODEL = 0x1302
    #  Returned when the key identified by AppKeyIndex is not stored in the node
    SL_STATUS_BT_MESH_FOUNDATION_INVALID_APP_KEY = 0x1303
    #  Returned when the key identified by NetKeyIndex is not stored in the node
    SL_STATUS_BT_MESH_FOUNDATION_INVALID_NET_KEY = 0x1304
    #  Returned when The node cannot serve the request due to insufficient resources
    SL_STATUS_BT_MESH_FOUNDATION_INSUFFICIENT_RESOURCES = 0x1305
    #  Returned when the key identified is already stored in the node and the new
    #  NetKey value is different
    SL_STATUS_BT_MESH_FOUNDATION_KEY_INDEX_EXISTS = 0x1306
    #  Returned when the model does not support the publish mechanism
    SL_STATUS_BT_MESH_FOUNDATION_INVALID_PUBLISH_PARAMS = 0x1307
    #  Returned when  the model does not support the subscribe mechanism
    SL_STATUS_BT_MESH_FOUNDATION_NOT_SUBSCRIBE_MODEL = 0x1308
    #  Returned when storing of the requested parameters failed
    SL_STATUS_BT_MESH_FOUNDATION_STORAGE_FAILURE = 0x1309
    #  Returned when requested setting is not supported
    SL_STATUS_BT_MESH_FOUNDATION_NOT_SUPPORTED = 0x130A
    #  Returned when the requested update operation cannot be performed due to general constraints
    SL_STATUS_BT_MESH_FOUNDATION_CANNOT_UPDATE = 0x130B
    #  Returned when the requested delete operation cannot be performed due to general constraints
    SL_STATUS_BT_MESH_FOUNDATION_CANNOT_REMOVE = 0x130C
    #  Returned when the requested bind operation cannot be performed due to general constraints
    SL_STATUS_BT_MESH_FOUNDATION_CANNOT_BIND = 0x130D
    #  Returned when The node cannot start advertising with Node Identity or Proxy since the
    #  maximum number of parallel advertising is reached
    SL_STATUS_BT_MESH_FOUNDATION_TEMPORARILY_UNABLE = 0x130E
    #  Returned when the requested state cannot be set
    SL_STATUS_BT_MESH_FOUNDATION_CANNOT_SET = 0x130F
    #  Returned when an unspecified error took place
    SL_STATUS_BT_MESH_FOUNDATION_UNSPECIFIED = 0x1310
    #  Returned when the NetKeyIndex and AppKeyIndex combination is not valid for a Config AppKey Update
    SL_STATUS_BT_MESH_FOUNDATION_INVALID_BINDING = 0x1311
    # Wi-Fi Errors
    #  Invalid firmware keyset
    SL_STATUS_WIFI_INVALID_KEY = 0x0B01
    #  The firmware download took too long
    SL_STATUS_WIFI_FIRMWARE_DOWNLOAD_TIMEOUT = 0x0B02
    #  Unknown request ID or wrong interface ID used
    SL_STATUS_WIFI_UNSUPPORTED_MESSAGE_ID = 0x0B03
    #  The request is successful but some parameters have been ignored
    SL_STATUS_WIFI_WARNING = 0x0B04
    #  No Packets waiting to be received
    SL_STATUS_WIFI_NO_PACKET_TO_RECEIVE = 0x0B05
    #  The sleep mode is granted
    SL_STATUS_WIFI_SLEEP_GRANTED = 0x0B08
    #  The WFx does not go back to sleep
    SL_STATUS_WIFI_SLEEP_NOT_GRANTED = 0x0B09
    #  The SecureLink MAC key was not found
    SL_STATUS_WIFI_SECURE_LINK_MAC_KEY_ERROR = 0x0B10
    #  The SecureLink MAC key is already installed in OTP
    SL_STATUS_WIFI_SECURE_LINK_MAC_KEY_ALREADY_BURNED = 0x0B11
    #  The SecureLink MAC key cannot be installed in RAM
    SL_STATUS_WIFI_SECURE_LINK_RAM_MODE_NOT_ALLOWED = 0x0B12
    #  The SecureLink MAC key installation failed
    SL_STATUS_WIFI_SECURE_LINK_FAILED_UNKNOWN_MODE = 0x0B13
    #  SecureLink key (re)negotiation failed
    SL_STATUS_WIFI_SECURE_LINK_EXCHANGE_FAILED = 0x0B14
    #  The device is in an inappropriate state to perform the request
    SL_STATUS_WIFI_WRONG_STATE = 0x0B18
    #  The request failed due to regulatory limitations
    SL_STATUS_WIFI_CHANNEL_NOT_ALLOWED = 0x0B19
    #  The connection request failed because no suitable AP was found
    SL_STATUS_WIFI_NO_MATCHING_AP = 0x0B1A
    #  The connection request was aborted by host
    SL_STATUS_WIFI_CONNECTION_ABORTED = 0x0B1B
    #  The connection request failed because of a timeout
    SL_STATUS_WIFI_CONNECTION_TIMEOUT = 0x0B1C
    #  The connection request failed because the AP rejected the device
    SL_STATUS_WIFI_CONNECTION_REJECTED_BY_AP = 0x0B1D
    #  The connection request failed because the WPA handshake did not complete successfully
    SL_STATUS_WIFI_CONNECTION_AUTH_FAILURE = 0x0B1E
    #  The request failed because the retry limit was exceeded
    SL_STATUS_WIFI_RETRY_EXCEEDED = 0x0B1F
    #  The request failed because the MSDU life time was exceeded
    SL_STATUS_WIFI_TX_LIFETIME_EXCEEDED = 0x0B20


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
