import voluptuous as vol

from bellows.config import cv_optional_int, cv_uint16
from bellows.types import EzspConfigId, EzspDecisionId, EzspPolicyId

EZSP_SCHEMA = {
    #
    # The number of packet buffers available to the stack. When set to the special
    # value 0xFF, the NCP will allocate all remaining configuration RAM towards
    # packet buffers, such that the resulting count will be the largest whole number
    # of packet buffers that can fit into the available memory
    vol.Optional(EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name): cv_optional_int(
        min=1, max=255
    ),
    # The maximum number of router neighbors the stack can keep track of. A neighbor
    # is a node within radio range
    vol.Optional(EzspConfigId.CONFIG_NEIGHBOR_TABLE_SIZE.name): cv_optional_int(
        min=8, max=16
    ),
    #
    # The maximum number of APS retried messages the stack can be transmitting at
    # any time
    vol.Optional(EzspConfigId.CONFIG_APS_UNICAST_MESSAGE_COUNT.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # The maximum number of non-volatile bindings supported by the stack
    vol.Optional(EzspConfigId.CONFIG_BINDING_TABLE_SIZE.name): cv_optional_int(
        min=0, max=32
    ),
    #
    # The maximum number of EUI64 to network address associations that the stack can
    # maintain for the application. (Note: The total number of such address
    # associations maintained by the NCP is the sum of the value of this setting and
    # the value of EZSP_CONFIG_TRUST_CENTER_ADDRESS_CA CHE_SIZE)
    vol.Optional(EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE.name): cv_optional_int(min=0),
    #
    # The maximum number of multicast groups that the device may be a member of
    vol.Optional(EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # The maximum number of destinations to which a node can route messages. This
    # includes both messages originating at this node and those relayed for others
    vol.Optional(EzspConfigId.CONFIG_ROUTE_TABLE_SIZE.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # The number of simultaneous route discoveries that a node will support
    vol.Optional(EzspConfigId.CONFIG_DISCOVERY_TABLE_SIZE.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # The size of the alarm broadcast buffer
    vol.Optional(EzspConfigId.CONFIG_BROADCAST_ALARM_DATA_SIZE.name): cv_optional_int(
        min=0, max=16
    ),
    #
    # The size of the unicast alarm buffers allocated for end device children
    vol.Optional(EzspConfigId.CONFIG_UNICAST_ALARM_DATA_SIZE.name): cv_optional_int(
        min=0, max=16
    ),
    #
    # Specifies the stack profile
    vol.Optional(EzspConfigId.CONFIG_STACK_PROFILE.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # The security level used for security at the MAC and network layers. The
    # supported values are 0 (no security) and 5 (payload is encrypted and a
    # four-byte MIC is used for authentication)
    vol.Optional(EzspConfigId.CONFIG_SECURITY_LEVEL.name): cv_optional_int(
        min=0, max=5
    ),
    #
    # The maximum number of hops for a message
    vol.Optional(EzspConfigId.CONFIG_MAX_HOPS.name): cv_optional_int(min=0, max=30),
    #
    # The maximum number of end device children that a router will support
    vol.Optional(EzspConfigId.CONFIG_MAX_END_DEVICE_CHILDREN.name): cv_optional_int(
        min=0, max=32
    ),
    #
    # The maximum amount of time that the MAC will hold a message for indirect
    # transmission to a child
    vol.Optional(
        EzspConfigId.CONFIG_INDIRECT_TRANSMISSION_TIMEOUT.name
    ): cv_optional_int(min=0, max=30000),
    #
    # The maximum amount of time that an end device child can wait between polls.
    # If no poll is heard within this timeout, then the parent removes the end
    # device from its tables. The timeout corresponding to a value of zero is 10
    # seconds. The timeout corresponding to a nonzero value N is 2^N minutes,
    # ranging from 2^1 = 2 minutes to 2^14 = 16384 minutes
    vol.Optional(EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # The maximum amount of time that a mobile node can wait between polls. If no
    # poll is heard within this timeout, then the parent removes the mobile node
    # from its tables
    vol.Optional(EzspConfigId.CONFIG_MOBILE_NODE_POLL_TIMEOUT.name): cv_optional_int(
        min=0
    ),
    #
    # The number of child table entries reserved for use only by mobile nodes
    vol.Optional(
        EzspConfigId.CONFIG_RESERVED_MOBILE_CHILD_ENTRIES.name
    ): cv_optional_int(min=0, max=254),
    #
    # Enables boost power mode and/or the alternate transmitter output
    vol.Optional(EzspConfigId.CONFIG_TX_POWER_MODE.name): cv_optional_int(min=0, max=3),
    #
    # 0: Allow this node to relay messages. 1: Prevent this node from relaying
    # messages
    vol.Optional(EzspConfigId.CONFIG_DISABLE_RELAY.name): cv_optional_int(min=0, max=1),
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
    vol.Optional(
        EzspConfigId.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE.name
    ): cv_optional_int(min=0),
    #
    # The size of the source route table
    vol.Optional(EzspConfigId.CONFIG_SOURCE_ROUTE_TABLE_SIZE.name): cv_optional_int(
        min=0
    ),
    # The units used for timing out end devices on their parent
    vol.Optional(
        EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT.name
    ): cv_optional_int(min=0, max=10),
    #
    # The number of blocks of a fragmented message that can be sent in a single
    # window
    vol.Optional(EzspConfigId.CONFIG_FRAGMENT_WINDOW_SIZE.name): cv_optional_int(
        min=0, max=8
    ),
    #
    # The time (ms) the stack will wait between sending blocks of a fragmented
    # message
    vol.Optional(EzspConfigId.CONFIG_FRAGMENT_DELAY_MS.name): cv_optional_int(min=0),
    #
    # The size of the Key Table used for storing individual link keys (if the device
    # is a Trust Center) or Application Link Keys (if the device is a normal node)
    vol.Optional(EzspConfigId.CONFIG_KEY_TABLE_SIZE.name): cv_optional_int(min=0),
    #
    # The APS ACK timeout value (ms). The stack waits this amount of time between
    # resends of APS retried messages
    vol.Optional(EzspConfigId.CONFIG_APS_ACK_TIMEOUT.name): cv_optional_int(min=0),
    #
    # The duration of an active scan 15/4 scan duration units. This also controls
    # the jitter used when responding to a beacon request
    vol.Optional(EzspConfigId.CONFIG_ACTIVE_SCAN_DURATION.name): cv_optional_int(
        min=0, max=6
    ),
    #
    # The time (seoonds) the coordinator will wait for a second end device bind
    # request to arrive
    vol.Optional(EzspConfigId.CONFIG_END_DEVICE_BIND_TIMEOUT.name): cv_optional_int(
        min=1
    ),
    #
    # The number of PAN id conflict reports that must be received by the network
    # manager within one minute to trigger a PAN id change
    vol.Optional(
        EzspConfigId.CONFIG_PAN_ID_CONFLICT_REPORT_THRESHOLD.name
    ): cv_optional_int(min=1, max=63),
    #
    # The timeout value in minutes for how long the Trust Center or a normal node
    # waits for the ZigBee Request Key to complete. On the Trust Center this
    # controls whether or not the device buffers the request, waiting for a matching
    # pair of ZigBee Request Key. If the value is non-zero, the Trust Center buffers
    # and waits for that amount of time. If the value is zero, the Trust Center does
    # not buffer the request and immediately responds to the request. Zero is the
    # most compliant behavior
    vol.Optional(EzspConfigId.CONFIG_REQUEST_KEY_TIMEOUT.name): cv_optional_int(
        min=0, max=10
    ),
    #
    # This value indicates the size of the runtime modifiable certificate table.
    # Normally certificates are stored in MFG tokens but this table can be used to
    # field upgrade devices with new Smart Energy certificates. This value cannot be
    # set, it can only be queried
    vol.Optional(EzspConfigId.CONFIG_CERTIFICATE_TABLE_SIZE.name): cv_optional_int(
        min=0, max=1
    ),
    #
    # This is a bitmask that controls which incoming ZDO request messages are passed
    # to the application. The bits are defined in the EmberZdoConfigurationFlags
    # enumeration. To see if the application is required to send a ZDO response in
    # reply to an incoming message, the application must check the APS options
    # bitfield within the incomingMessageHandler callback to see if the
    # EMBER_APS_OPTION_ZDO_RESPONSE_REQUIRED flag is set
    vol.Optional(EzspConfigId.CONFIG_APPLICATION_ZDO_FLAGS.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # The maximum number of broadcasts during a single broadcast timeout period
    vol.Optional(EzspConfigId.CONFIG_BROADCAST_TABLE_SIZE.name): cv_optional_int(
        min=15, max=254
    ),
    #
    # The size of the MAC filter list table
    vol.Optional(EzspConfigId.CONFIG_MAC_FILTER_TABLE_SIZE.name): cv_optional_int(
        min=0, max=254
    ),
    #
    # The number of supported networks
    vol.Optional(EzspConfigId.CONFIG_SUPPORTED_NETWORKS.name): cv_optional_int(
        min=1, max=2
    ),
    #
    # Whether multicasts are sent to the RxOnWhenIdle=true address (0xFFFD) or the
    # sleepy broadcast address (0xFFFF). The RxOnWhenIdle=true address is the ZigBee
    # compliant destination for multicasts. 0=false, 1=true
    vol.Optional(
        EzspConfigId.CONFIG_SEND_MULTICASTS_TO_SLEEPY_ADDRESS.name
    ): cv_optional_int(min=0, max=1),
    #
    # ZLL group address initial configuration
    vol.Optional(EzspConfigId.CONFIG_ZLL_GROUP_ADDRESSES.name): cv_optional_int(
        min=0, max=255
    ),
    #
    # ZLL RSSI threshold initial configuration
    vol.Optional(EzspConfigId.CONFIG_ZLL_RSSI_THRESHOLD.name): cv_optional_int(
        min=-128, max=127
    ),
    #
    # The maximum number of pairings supported by the stack. Controllers must
    # support at least one pairing table entry while targets must support at
    # least five
    vol.Optional(EzspConfigId.CONFIG_RF4CE_PAIRING_TABLE_SIZE.name): cv_optional_int(
        min=0, max=126
    ),
    #
    # The maximum number of outgoing RF4CE packets supported by the stack
    vol.Optional(
        EzspConfigId.CONFIG_RF4CE_PENDING_OUTGOING_PACKET_TABLE_SIZE.name
    ): cv_optional_int(min=0, max=16),
    #
    # Toggles the MTORR flow control in the stack. 0=false, 1=true
    vol.Optional(EzspConfigId.CONFIG_MTORR_FLOW_CONTROL.name): cv_optional_int(
        min=0, max=1
    ),
    #
    # Deprecated
    # The amount of time a trust center will store a transient key
    # with which a device can use to join the network
    vol.Optional(EzspConfigId.CONFIG_TRANSIENT_KEY_TIMEOUT_S.name): cv_optional_int(
        min=0, max=65535
    ),
}

EZSP_POLICIES_SHARED = {
    vol.Optional(
        EzspPolicyId.TC_KEY_REQUEST_POLICY.name,
        default=EzspDecisionId.ALLOW_TC_KEY_REQUESTS_AND_SEND_CURRENT_KEY,
    ): cv_uint16,
    vol.Optional(
        EzspPolicyId.APP_KEY_REQUEST_POLICY.name,
        default=EzspDecisionId.DENY_APP_KEY_REQUESTS,
    ): cv_uint16,
    vol.Optional(
        EzspPolicyId.TRUST_CENTER_POLICY.name,
        default=EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
    ): cv_uint16,
}

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
