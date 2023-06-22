import bellows.types as t


class sl_zb_sec_man_key_type_t(t.enum8):
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


class sl_zb_sec_man_derived_key_type_t(t.enum8):
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


class sl_zb_sec_man_flags_t(t.bitmap8):
    """Security Manager context flags."""

    NONE = 0x00
    # For export APIs, this flag indicates the key_index parameter is valid in
    # the ::sl_zb_sec_man_context_t structure. This bit is set by the caller
    # when intending to search for a key by key_index. This flag has no
    # significance for import APIs.
    KEY_INDEX_IS_VALID = 0x01

    # For export APIs, this flag indicates the eui64 parameter is valid in the
    # ::sl_zb_sec_man_context_t structure. This bit is set by the caller when
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


class EzspValueId(t.enum8):
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
    # The threshold value for a counter
    VALUE_SET_COUNTER_THRESHOLD = 0x17
    # Resets all counters thresholds to 0xFF
    VALUE_RESET_COUNTER_THRESHOLDS = 0x18
    # Clears all the counters
    VALUE_CLEAR_COUNTERS = 0x19
    # The node's new certificate signed by the CA.
    EZSP_VALUE_CERTIFICATE_283K1 = 0x1A
    # The Certificate Authority's public key.
    EZSP_VALUE_PUBLIC_KEY_283K1 = 0x1B
    # The node's new static private key.
    EZSP_VALUE_PRIVATE_KEY_283K1 = 0x1C
    # The NWK layer security frame counter value
    VALUE_NWK_FRAME_COUNTER = 0x23
    # The APS layer security frame counter value
    VALUE_APS_FRAME_COUNTER = 0x24
    # Sets the device type to use on the next rejoin using device type
    VALUE_RETRY_DEVICE_TYPE = 0x25
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
    # Set packet traffic arbitration directional priority pulse width in microseconds.
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
