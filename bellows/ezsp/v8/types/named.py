"""Protocol version 8 named types."""

import bellows.types.basic as basic
from bellows.types.named import (  # noqa: F401, F403
    Bool,
    Channels,
    EmberApsOption,
    EmberBindingType,
    EmberCertificate283k1Data,
    EmberCertificateData,
    EmberConcentratorType,
    EmberConfigTxPowerMode,
    EmberCurrentSecurityBitmask,
    EmberEUI64,
    EmberEventUnits,
    EmberGpKeyType,
    EmberGpSecurityLevel,
    EmberIncomingMessageType,
    EmberInitialSecurityBitmask,
    EmberJoinDecision,
    EmberKeyData,
    EmberKeyStatus,
    EmberKeyStructBitmask,
    EmberLibraryStatus,
    EmberMacPassthroughType,
    EmberMessageDigest,
    EmberMulticastId,
    EmberNetworkStatus,
    EmberNodeId,
    EmberNodeType,
    EmberOutgoingMessageType,
    EmberPanId,
    EmberPrivateKey283k1Data,
    EmberPrivateKeyData,
    EmberPublicKey283k1Data,
    EmberPublicKeyData,
    EmberSignature283k1Data,
    EmberSignatureData,
    EmberSmacData,
    EmberStatus,
    EmberZdoConfigurationFlags,
    EmberZllKeyIndex,
    EmberZllState,
    ExtendedPanId,
    EzspEndpointFlags,
    EzspExtendedValueId,
    EzspMfgTokenId,
    EzspNetworkScanType,
    EzspSourceRouteOverheadInformation,
    EzspStatus,
    EzspZllNetworkOperation,
)


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
    CONFIG_BROADCAST_MIN_ACKS_NEEDED = 0x37
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
    # Sets the mask that controls which pins will have their GPIO configuration and
    # output values set to their power-up and power-down values when the NCP powers
    # the radio up and down.
    VALUE_GPIO_RADIO_POWER_MASK = 0x40
    # Return the active radio config.
    VALUE_ACTIVE_RADIO_CONFIG = 0x41


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


class EzspDecisionBitmask(basic.bitmap16):
    """EZSP Decision bitmask."""

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


class EmberKeyType(basic.enum8):
    # Describes the type of ZigBee security key.

    # A shared key between the Trust Center and a device.
    TRUST_CENTER_LINK_KEY = 0x01
    # A shared secret used for deriving keys between the Trust Center and a
    # device
    CURRENT_NETWORK_KEY = 0x03
    # The alternate Network Key that was previously in use, or the newer key
    # that will be switched to.
    NEXT_NETWORK_KEY = 0x04
    # An Application Link Key shared with another (non-Trust Center) device.
    APPLICATION_LINK_KEY = 0x05


class EmberDeviceUpdate(basic.enum8):
    # The status of the device update.

    STANDARD_SECURITY_SECURED_REJOIN = 0x0
    STANDARD_SECURITY_UNSECURED_JOIN = 0x1
    DEVICE_LEFT = 0x2
    STANDARD_SECURITY_UNSECURED_REJOIN = 0x3


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


EmberNetworkInitStruct = EmberNetworkInitBitmask


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


class EmberDutyCycleHectoPct(basic.uint16_t):
    """ "The percent of duty cycle for a limit.

    Duty Cycle, Limits, and Thresholds are reported in units of Percent * 100
    (i.e. 10000 = 100.00%, 1 = 0.01%)"""


class EmberGpProxyTableEntryStatus(basic.uint8_t):
    """The proxy table entry status."""


class EmberGpSecurityFrameCounter(basic.uint32_t):
    """The security frame counter"""


class EmberGpSinkTableEntryStatus(basic.uint8_t):
    """The sink table entry status."""


class SecureEzspSecurityType(basic.uint32_t):
    """Security type of the Secure EZSP Protocol."""


class SecureEzspSecurityLevel(basic.uint8_t):
    """Security level of the Secure EZSP Protocol."""


class SecureEzspRandomNumber(basic.fixed_list(16, basic.uint8_t)):
    """Randomly generated 64-bit number.

    Both NCP and Host contribute this number to create the Session ID,
    which is used in the nonce.
    """


class SecureEzspSessionId(basic.fixed_list(8, basic.uint8_t)):
    """Generated 64-bit Session ID, using random numbers from Host and NCP.

    It is generated at each reboot (during negotiation phase). Having both sides
    contribute to the value prevents one side from choosing a number that might have
    been previously used (either because of a bug or by malicious intent).
    """
