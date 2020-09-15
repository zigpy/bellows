import voluptuous as vol

from bellows.config import cv_uint16
import bellows.multicast

from . import types

c = types.EzspConfigId
zdo_flags = types.EmberZdoConfigurationFlags

EZSP_SCHEMA = {
    #
    # The number of packet buffers available to the stack. When set to the special
    # value 0xFF, the NCP will allocate all remaining configuration RAM towards
    # packet buffers, such that the resulting count will be the largest whole number
    # of packet buffers that can fit into the available memory
    vol.Optional(c.CONFIG_PACKET_BUFFER_COUNT.name, default=0xFF): vol.All(
        int, vol.Range(min=1, max=255)
    ),
    # The maximum number of router neighbors the stack can keep track of. A neighbor
    # is a node within radio range
    vol.Optional(c.CONFIG_NEIGHBOR_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=8, max=16)
    ),
    #
    # The maximum number of APS retried messages the stack can be transmitting at
    # any time
    vol.Optional(c.CONFIG_APS_UNICAST_MESSAGE_COUNT.name): vol.All(
        int, vol.Range(min=0, max=255)
    ),
    #
    # The maximum number of non-volatile bindings supported by the stack
    vol.Optional(c.CONFIG_BINDING_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=0, max=32)
    ),
    #
    # The maximum number of EUI64 to network address associations that the stack can
    # maintain for the application. (Note: The total number of such address
    # associations maintained by the NCP is the sum of the value of this setting and
    # the value of EZSP_CONFIG_TRUST_CENTER_ADDRESS_CA CHE_SIZE)
    vol.Optional(c.CONFIG_ADDRESS_TABLE_SIZE.name, default=16): vol.All(
        int, vol.Range(min=0)
    ),
    #
    # The maximum number of multicast groups that the device may be a member of
    vol.Optional(
        c.CONFIG_MULTICAST_TABLE_SIZE.name,
        default=bellows.multicast.Multicast.TABLE_SIZE,
    ): vol.All(int, vol.Range(min=0, max=255)),
    #
    # The maximum number of destinations to which a node can route messages. This
    # includes both messages originating at this node and those relayed for others
    vol.Optional(c.CONFIG_ROUTE_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=0, max=255)
    ),
    #
    # The number of simultaneous route discoveries that a node will support
    vol.Optional(c.CONFIG_DISCOVERY_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=0, max=255)
    ),
    #
    # The size of the alarm broadcast buffer
    vol.Optional(c.CONFIG_BROADCAST_ALARM_DATA_SIZE.name): vol.All(
        int, vol.Range(min=0, max=16)
    ),
    #
    # The size of the unicast alarm buffers allocated for end device children
    vol.Optional(c.CONFIG_UNICAST_ALARM_DATA_SIZE.name): vol.All(
        int, vol.Range(min=0, max=16)
    ),
    #
    # Specifies the stack profile
    vol.Optional(c.CONFIG_STACK_PROFILE.name, default=2): vol.All(
        int, vol.Range(min=0, max=255)
    ),
    #
    # The security level used for security at the MAC and network layers. The
    # supported values are 0 (no security) and 5 (payload is encrypted and a
    # four-byte MIC is used for authentication)
    vol.Optional(c.CONFIG_SECURITY_LEVEL.name, default=5): vol.All(
        int, vol.Range(min=0, max=5)
    ),
    #
    # The maximum number of hops for a message
    vol.Optional(c.CONFIG_MAX_HOPS.name): vol.All(int, vol.Range(min=0, max=30)),
    #
    # The maximum number of end device children that a router will support
    vol.Optional(c.CONFIG_MAX_END_DEVICE_CHILDREN.name, default=32): vol.All(
        int, vol.Range(min=0, max=32)
    ),
    #
    # The maximum amount of time that the MAC will hold a message for indirect
    # transmission to a child
    vol.Optional(c.CONFIG_INDIRECT_TRANSMISSION_TIMEOUT.name, default=7680): vol.All(
        int, vol.Range(min=0, max=30000)
    ),
    #
    # The maximum amount of time that an end device child can wait between polls.
    # If no poll is heard within this timeout, then the parent removes the end
    # device from its tables. The timeout corresponding to a value of zero is 10
    # seconds. The timeout corresponding to a nonzero value N is 2^N minutes,
    # ranging from 2^1 = 2 minutes to 2^14 = 16384 minutes
    vol.Optional(c.CONFIG_END_DEVICE_POLL_TIMEOUT.name, default=60): vol.All(
        int, vol.Range(min=0, max=255)
    ),
    #
    # The maximum amount of time that a mobile node can wait between polls. If no
    # poll is heard within this timeout, then the parent removes the mobile node
    # from its tables
    vol.Optional(c.CONFIG_MOBILE_NODE_POLL_TIMEOUT.name): vol.All(
        int, vol.Range(min=0)
    ),
    #
    # The number of child table entries reserved for use only by mobile nodes
    vol.Optional(c.CONFIG_RESERVED_MOBILE_CHILD_ENTRIES.name): vol.All(
        int, vol.Range(min=0, max=254)
    ),
    #
    # Enables boost power mode and/or the alternate transmitter output
    vol.Optional(c.CONFIG_TX_POWER_MODE.name): vol.All(int, vol.Range(min=0, max=3)),
    #
    # 0: Allow this node to relay messages. 1: Prevent this node from relaying
    # messages
    vol.Optional(c.CONFIG_DISABLE_RELAY.name): vol.All(int, vol.Range(min=0, max=1)),
    #
    # The maximum number of EUI64 to network address associations that the Trust
    # Center can maintain. These address cache entries are reserved for and reused
    # by the Trust Center when processing device join/rejoin authentications. This
    # cache size limits the number of overlapping joins the Trust Center can process
    # within a narrow time window (e.g. two seconds), and thus should be set to the
    # maximum number of near simultaneous joins the Trust Center is expected to
    # accommodate. (Note: The total number of such address associations maintained
    # by the NCP is the sum of the value of this setting and the value of
    # EZSP_CONFIG_ADDRESS_TABLE_SIZE)
    vol.Optional(c.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE.name, default=2): vol.All(
        int, vol.Range(min=0)
    ),
    #
    # The size of the source route table
    vol.Optional(c.CONFIG_SOURCE_ROUTE_TABLE_SIZE.name, default=16): vol.All(
        int, vol.Range(min=0)
    ),
    # The units used for timing out end devices on their parent
    vol.Optional(c.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT.name, default=8): vol.All(
        int, vol.Range(min=0, max=10)
    ),
    #
    # The number of blocks of a fragmented message that can be sent in a single
    # window
    vol.Optional(c.CONFIG_FRAGMENT_WINDOW_SIZE.name): vol.All(
        int, vol.Range(min=0, max=8)
    ),
    #
    # The time (ms) the stack will wait between sending blocks of a fragmented
    # message
    vol.Optional(c.CONFIG_FRAGMENT_DELAY_MS.name): vol.All(int, vol.Range(min=0)),
    #
    # The size of the Key Table used for storing individual link keys (if the device
    # is a Trust Center) or Application Link Keys (if the device is a normal node)
    vol.Optional(c.CONFIG_KEY_TABLE_SIZE.name, default=4): vol.All(
        int, vol.Range(min=0)
    ),
    #
    # The APS ACK timeout value (ms). The stack waits this amount of time between
    # resends of APS retried messages
    vol.Optional(c.CONFIG_APS_ACK_TIMEOUT.name): vol.All(int, vol.Range(min=0)),
    #
    # The duration of an active scan 15/4 scan duration units. This also controls
    # the jitter used when responding to a beacon request
    vol.Optional(c.CONFIG_ACTIVE_SCAN_DURATION.name): vol.All(
        int, vol.Range(min=0, max=6)
    ),
    #
    # The time (seoonds) the coordinator will wait for a second end device bind
    # request to arrive
    vol.Optional(c.CONFIG_END_DEVICE_BIND_TIMEOUT.name): vol.All(int, vol.Range(min=1)),
    #
    # The number of PAN id conflict reports that must be received by the network
    # manager within one minute to trigger a PAN id change
    vol.Optional(c.CONFIG_PAN_ID_CONFLICT_REPORT_THRESHOLD.name, default=2): vol.All(
        int, vol.Range(min=1, max=63)
    ),
    #
    # The timeout value in minutes for how long the Trust Center or a normal node
    # waits for the ZigBee Request Key to complete. On the Trust Center this
    # controls whether or not the device buffers the request, waiting for a matching
    # pair of ZigBee Request Key. If the value is non-zero, the Trust Center buffers
    # and waits for that amount of time. If the value is zero, the Trust Center does
    # not buffer the request and immediately responds to the request. Zero is the
    # most compliant behavior
    vol.Optional(c.CONFIG_REQUEST_KEY_TIMEOUT.name): vol.All(
        int, vol.Range(min=0, max=10)
    ),
    #
    # This value indicates the size of the runtime modifiable certificate table.
    # Normally certificates are stored in MFG tokens but this table can be used to
    # field upgrade devices with new Smart Energy certificates. This value cannot be
    # set, it can only be queried
    vol.Optional(c.CONFIG_CERTIFICATE_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=0, max=1)
    ),
    #
    # This is a bitmask that controls which incoming ZDO request messages are passed
    # to the application. The bits are defined in the EmberZdoConfigurationFlags
    # enumeration. To see if the application is required to send a ZDO response in
    # reply to an incoming message, the application must check the APS options
    # bitfield within the incomingMessageHandler callback to see if the
    # EMBER_APS_OPTION_ZDO_RESPONSE_REQUIRED flag is set
    vol.Optional(
        c.CONFIG_APPLICATION_ZDO_FLAGS.name,
        default=zdo_flags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS
        | zdo_flags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS,
    ): vol.All(int, vol.Range(min=0, max=255)),
    #
    # The maximum number of broadcasts during a single broadcast timeout period
    vol.Optional(c.CONFIG_BROADCAST_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=15, max=254)
    ),
    #
    # The size of the MAC filter list table
    vol.Optional(c.CONFIG_MAC_FILTER_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=0, max=254)
    ),
    #
    # The number of supported networks
    vol.Optional(c.CONFIG_SUPPORTED_NETWORKS.name, default=1): vol.All(
        int, vol.Range(min=1, max=2)
    ),
    #
    # Whether multicasts are sent to the RxOnWhenIdle=true address (0xFFFD) or the
    # sleepy broadcast address (0xFFFF). The RxOnWhenIdle=true address is the ZigBee
    # compliant destination for multicasts. 0=false, 1=true
    vol.Optional(c.CONFIG_SEND_MULTICASTS_TO_SLEEPY_ADDRESS.name): vol.All(
        int, vol.Range(min=0, max=1)
    ),
    #
    # ZLL group address initial configuration
    vol.Optional(c.CONFIG_ZLL_GROUP_ADDRESSES.name): vol.All(
        int, vol.Range(min=0, max=255)
    ),
    #
    # ZLL RSSI threshold initial configuration
    vol.Optional(c.CONFIG_ZLL_RSSI_THRESHOLD.name): vol.All(
        int, vol.Range(min=-128, max=127)
    ),
    #
    # The maximum number of pairings supported by the stack. Controllers must
    # support at least one pairing table entry while targets must support at
    # least five
    vol.Optional(c.CONFIG_RF4CE_PAIRING_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=0, max=126)
    ),
    #
    # The maximum number of outgoing RF4CE packets supported by the stack
    vol.Optional(c.CONFIG_RF4CE_PENDING_OUTGOING_PACKET_TABLE_SIZE.name): vol.All(
        int, vol.Range(min=0, max=16)
    ),
    #
    # Toggles the MTORR flow control in the stack. 0=false, 1=true
    vol.Optional(c.CONFIG_MTORR_FLOW_CONTROL.name): vol.All(
        int, vol.Range(min=0, max=1)
    ),
    #
    # Deprecated
    # The amount of time a trust center will store a transient key
    # with which a device can use to join the network
    vol.Optional(c.CONFIG_TRANSIENT_KEY_TIMEOUT_S.name): vol.All(
        int, vol.Range(min=0, max=65535)
    ),
}

EZSP_POLICIES_SHARED = {
    vol.Optional(
        types.EzspPolicyId.TC_KEY_REQUEST_POLICY.name,
        default=types.EzspDecisionId.ALLOW_TC_KEY_REQUESTS,
    ): cv_uint16,
    vol.Optional(
        types.EzspPolicyId.APP_KEY_REQUEST_POLICY.name,
        default=types.EzspDecisionId.DENY_APP_KEY_REQUESTS,
    ): cv_uint16,
    vol.Optional(
        types.EzspPolicyId.TRUST_CENTER_POLICY.name,
        default=types.EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
    ): cv_uint16,
}

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in types.EzspPolicyId},
}
