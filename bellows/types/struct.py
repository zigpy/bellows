import dataclasses
import inspect
import typing

from . import basic, named

NoneType = type(None)


class ListSubclass(list):
    # So we can call `setattr()` on it
    pass


class DotDict(dict):
    __getattr__ = dict.__getitem__


class EzspStruct:
    """Struct class."""

    @classmethod
    def _annotations(cls) -> typing.Dict[str, type]:
        # First get our proper subclasses
        subclasses = []

        for subcls in cls.__mro__:
            if subcls is EzspStruct:
                break

            subclasses.append(subcls)

        annotations = {}

        # Iterate over the annotations *backwards*.
        # We want subclasses' annotations to override their parent classes'.
        for subcls in subclasses[::-1]:
            annotations.update(getattr(subcls, "__annotations__", {}))

        return annotations

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()

        # Explicitly check for old-style structs and fail very early
        if hasattr(cls, "_fields"):
            raise TypeError(
                "Struct subclasses do not use `_fields` anymore."
                " Use class attributes with type annotations."
            )

        # We generate fields up here to fail early (and cache it)
        fields = cls.fields()

        # We dynamically create our subclass's `__new__` method
        def _new(cls, *args, **kwargs) -> EzspStruct:
            # Like a copy constructor
            if len(args) == 1 and isinstance(args[0], cls):
                if kwargs:
                    raise ValueError(
                        f"Cannot use copy constructor with kwargs: " f"{kwargs!r}"
                    )

                kwargs = args[0].as_dict()
                args = ()

            # Pretend our signature is `__new__(cls, p1: t1, p2: t2, ...)`
            signature = inspect.Signature(
                parameters=[
                    inspect.Parameter(
                        name=f.name,
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=None,
                        annotation=f.type,
                    )
                    for f in cls.fields()
                ]
            )

            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()

            instance = super().__new__(cls)

            # Set and convert the attributes to their respective types
            for name, value in bound.arguments.items():
                field = getattr(fields, name)

                if value is not None:
                    try:
                        value = field.concrete_type(value)
                    except Exception as e:
                        raise ValueError(
                            f"Failed to convert {name}={value!r} from type"
                            f" {type(value)} to {field.concrete_type}"
                        ) from e

                setattr(instance, name, value)

            return instance

        # Finally, attach the above __new__ classmethod to our subclass
        cls.__new__ = _new

    @classmethod
    def fields(cls) -> typing.List["StructField"]:
        fields = ListSubclass()
        seen_optional = False

        # We need both to throw type errors in case a field is not annotated
        annotations = cls._annotations()
        variables = vars(cls)

        # `set(annotations) | set(variables)` doesn't preserve order, which we need
        for name in list(annotations) + [v for v in variables if v not in annotations]:
            # _foo and FOO are considered constants and ignored
            if name.startswith("_") or name.upper() == name:
                continue

            field = getattr(cls, name, StructField())

            # Ignore methods and properties
            if callable(field) or isinstance(field, property):
                continue

            # It's a lot easier to debug when things break immediately instead of
            # fields being silently skipped
            if name not in annotations:
                raise TypeError(f"Field {name!r} is not annotated")

            annotation = annotations[name]

            if not isinstance(field, StructField):
                raise TypeError(
                    f"Field {name!r} must be a StructField or undefined, not {field!r}"
                )

            if field.type is not None and field.type != annotation:
                raise TypeError(
                    f"Field {name!r} type annotation conflicts with provided type:"
                    f" {annotation} != {field.type}"
                )

            field = field.replace(name=name, type=annotation)

            if field.optional:
                seen_optional = True

            if seen_optional and not field.optional:
                raise TypeError(
                    f"No required fields can come after optional fields: " f"{field!r}"
                )

            fields.append(field)
            setattr(fields, field.name, field)

        return fields

    def assigned_fields(self, *, strict=False) -> ListSubclass:
        assigned_fields = ListSubclass()

        for field in self.fields():
            value = getattr(self, field.name)

            # Ignore fields that aren't required
            if field.requires is not None and not field.requires(self):
                continue

            # Missing non-optional required fields cause an error if strict
            if value is None:
                if not strict or field.optional:
                    continue

                raise ValueError(f"Value for field {field.name} is required")

            assigned_fields.append((field, value))
            setattr(assigned_fields, field.name, (field, value))

        return assigned_fields

    def as_dict(self) -> typing.Dict[str, typing.Any]:
        return {f.name: v for f, v in self.assigned_fields()}

    def serialize(self) -> bytes:
        return b"".join(
            f.concrete_type(v).serialize() for f, v in self.assigned_fields(strict=True)
        )

    @classmethod
    def deserialize(cls, data: bytes) -> typing.Tuple["EzspStruct", bytes]:
        kwargs = DotDict()

        for field in cls.fields():
            # XXX: DotDict looks like our struct because it has attributes
            if field.requires is not None and not field.requires(kwargs):
                continue

            kwargs[field.name], data = field.concrete_type.deserialize(data)

        return cls(**kwargs), data

    def replace(self, **kwargs) -> "EzspStruct":
        d = self.as_dict().copy()
        d.update(kwargs)

        return type(self)(**d)

    def __eq__(self, other: "EzspStruct") -> bool:
        if not isinstance(self, type(other)) and not isinstance(other, type(self)):
            return False

        return self.as_dict() == other.as_dict()

    def __repr__(self) -> str:
        kwargs = ", ".join([f"{k}={v!r}" for k, v in self.as_dict().items()])
        return f"{type(self).__name__}({kwargs})"


@dataclasses.dataclass(frozen=True)
class StructField:
    name: typing.Optional[str] = None
    type: typing.Optional[type] = None

    requires: typing.Optional[typing.Callable[[EzspStruct], bool]] = None

    def __post_init__(self):
        # Fail to initialize if the concrete type is invalid
        self.concrete_type

    @property
    def optional(self) -> bool:
        # typing.Optional[Foo] is really typing.Union[Foo, None]
        if getattr(self.type, "__origin__", None) is not typing.Union:
            return False

        # I can't think of a case where this is ever False but it's best to be explicit
        return NoneType in self.type.__args__

    @property
    def concrete_type(self) -> type:
        if getattr(self.type, "__origin__", None) is not typing.Union:
            return self.type

        types = set(self.type.__args__) - {NoneType}

        if len(types) > 1:
            raise TypeError("Struct field cannot have more than one concrete type")

        return tuple(types)[0]

    def replace(self, **kwargs) -> "StructField":
        return dataclasses.replace(self, **kwargs)


class EmberNetworkParameters(EzspStruct):
    # Network parameters.
    # The network's extended PAN identifier.
    extendedPanId: named.ExtendedPanId
    # The network's PAN identifier.
    panId: named.EmberPanId
    # A power setting, in dBm.
    radioTxPower: basic.uint8_t
    # A radio channel.
    radioChannel: basic.uint8_t
    # The method used to initially join the network.
    joinMethod: named.EmberJoinMethod
    # NWK Manager ID. The ID of the network manager in the current network.
    # This may only be set at joining when using USE_NWK_COMMISSIONING as
    # the join method.
    nwkManagerId: named.EmberNodeId
    # NWK Update ID. The value of the ZigBee nwkUpdateId known by the
    # stack. This is used to determine the newest instance of the network
    # after a PAN ID or channel change. This may only be set at joining
    # when using USE_NWK_COMMISSIONING as the join method.
    nwkUpdateId: basic.uint8_t
    # NWK channel mask. The list of preferred channels that the NWK manager
    # has told this device to use when searching for the network. This may
    # only be set at joining when using USE_NWK_COMMISSIONING as the join
    # method.
    channels: named.Channels


class EmberZigbeeNetwork(EzspStruct):
    # The parameters of a ZigBee network.
    # The 802.15.4 channel associated with the network.
    channel: basic.uint8_t
    # The network's PAN identifier.
    panId: named.EmberPanId
    # The network's extended PAN identifier.
    extendedPanId: named.ExtendedPanId
    # Whether the network is allowing MAC associations.
    allowingJoin: named.Bool
    # The Stack Profile associated with the network.
    stackProfile: basic.uint8_t
    # The instance of the Network.
    nwkUpdateId: basic.uint8_t


class EmberApsFrame(EzspStruct):
    # ZigBee APS frame parameters.
    # The application profile ID that describes the format of the message.
    profileId: basic.uint16_t
    # The cluster ID for this message.
    clusterId: basic.uint16_t
    # The source endpoint.
    sourceEndpoint: basic.uint8_t
    # The destination endpoint.
    destinationEndpoint: basic.uint8_t
    # A bitmask of options.
    options: named.EmberApsOption
    # The group ID for this message, if it is multicast mode.
    groupId: basic.uint16_t
    # The sequence number.
    sequence: basic.uint8_t


class EmberBindingTableEntry(EzspStruct):
    # An entry in the binding table.
    # The type of binding.
    type: named.EmberBindingType
    # The endpoint on the local node.
    local: basic.uint8_t
    # A cluster ID that matches one from the local endpoint's simple
    # descriptor. This cluster ID is set by the provisioning application to
    # indicate which part an endpoint's functionality is bound to this
    # particular remote node and is used to distinguish between unicast and
    # multicast bindings. Note that a binding can be used to send messages
    # with any cluster ID, not just that listed in the binding.
    clusterId: basic.uint16_t
    # The endpoint on the remote node (specified by identifier).
    remote: basic.uint8_t
    # A 64-bit identifier. This is either the destination EUI64 (for
    # unicasts) or the 64-bit group address (for multicasts).
    identifier: named.EmberEUI64
    # The index of the network the binding belongs to.
    networkIndex: basic.uint8_t


class EmberMulticastTableEntry(EzspStruct):
    # A multicast table entry indicates that a particular endpoint is a member
    # of a particular multicast group.  Only devices with an endpoint in a
    # multicast group will receive messages sent to that multicast group.
    # The multicast group ID.
    multicastId: named.EmberMulticastId
    # The endpoint that is a member, or 0 if this entry is not in use (the
    # ZDO is not a member of any multicast groups.)
    endpoint: basic.uint8_t
    # The network index of the network the entry is related to.
    networkIndex: basic.uint8_t


class EmberTransientKeyData(EzspStruct):
    # The transient key data structure. Added in ver. 5
    # The IEEE address paired with the transient link key.
    eui64: named.EmberEUI64
    # The key data structure matching the transient key.
    keyData: named.EmberKeyData
    # The incoming frame counter associated with this key.
    incomingFrameCounter: basic.uint32_t
    # The number of milliseconds remaining before the key
    # is automatically timed out of the transient key table.
    countdownTimerMs: basic.uint32_t


class EmberAesMmoHashContext(EzspStruct):
    # The hash context for an ongoing hash operation.
    # The result of ongoing the hash operation.
    result: basic.fixed_list(16, basic.uint8_t)
    # The total length of the data that has been hashed so far.
    length: basic.uint32_t


class EmberNeighborTableEntry(EzspStruct):
    # A neighbor table entry stores information about the reliability of RF
    # links to and from neighboring nodes.
    # The neighbor's two byte network id
    shortId: named.EmberNodeId
    # An exponentially weighted moving average of the link quality values
    # of incoming packets from this neighbor as reported by the PHY.
    averageLqi: basic.uint8_t
    # The incoming cost for this neighbor, computed from the average LQI.
    # Values range from 1 for a good link to 7 for a bad link.
    inCost: basic.uint8_t
    # The outgoing cost for this neighbor, obtained from the most recently
    # received neighbor exchange message from the neighbor. A value of zero
    # means that a neighbor exchange message from the neighbor has not been
    # received recently enough, or that our id was not present in the most
    # recently received one.
    outCost: basic.uint8_t
    # The number of aging periods elapsed since a link status message was
    # last received from this neighbor. The aging period is 16 seconds.
    age: basic.uint8_t
    # The 8 byte EUI64 of the neighbor.
    longId: named.EmberEUI64


class EmberRouteTableEntry(EzspStruct):
    # A route table entry stores information about the next hop along the route
    # to the destination.
    # The short id of the destination. A value of 0xFFFF indicates the
    # entry is unused.
    destination: named.EmberNodeId
    # The short id of the next hop to this destination.
    nextHop: basic.uint16_t
    # Indicates whether this entry is active (0), being discovered (1)),
    # unused (3), or validating (4).
    status: basic.uint8_t
    # The number of seconds since this route entry was last used to send a
    # packet.
    age: basic.uint8_t
    # Indicates whether this destination is a High RAM Concentrator (2), a
    # Low RAM Concentrator (1), or not a concentrator (0).
    concentratorType: basic.uint8_t
    # For a High RAM Concentrator, indicates whether a route record is
    # needed (2), has been sent (1), or is no long needed (0) because a
    # source routed message from the concentrator has been received.
    routeRecordState: basic.uint8_t


class EmberInitialSecurityState(EzspStruct):
    # The security data used to set the configuration for the stack, or the
    # retrieved configuration currently in use.
    # A bitmask indicating the security state used to indicate what the
    # security configuration will be when the device forms or joins the
    # network.
    bitmask: named.EmberInitialSecurityBitmask
    # The pre-configured Key data that should be used when forming or
    # joining the network. The security bitmask must be set with the
    # HAVE_PRECONFIGURED_KEY bit to indicate that the key contains valid
    # data.
    preconfiguredKey: named.EmberKeyData
    # The Network Key that should be used by the Trust Center when it forms
    # the network, or the Network Key currently in use by a joined device.
    # The security bitmask must be set with HAVE_NETWORK_KEY to indicate
    # that the key contains valid data.
    networkKey: named.EmberKeyData
    # The sequence number associated with the network key. This is only
    # valid if the HAVE_NETWORK_KEY has been set in the security bitmask.
    networkKeySequenceNumber: basic.uint8_t
    # This is the long address of the trust center on the network that will
    # be joined. It is usually NOT set prior to joining the network and
    # instead it is learned during the joining message exchange. This field
    # is only examined if HAVE_TRUST_CENTER_EUI64 is set in the
    # EmberInitialSecurityState::bitmask. Most devices should clear that
    # bit and leave this field alone. This field must be set when using
    # commissioning mode.
    preconfiguredTrustCenterEui64: named.EmberEUI64


class EmberCurrentSecurityState(EzspStruct):
    # The security options and information currently used by the stack.
    # A bitmask indicating the security options currently in use by a
    # device joined in the network.
    bitmask: named.EmberCurrentSecurityBitmask
    # The IEEE Address of the Trust Center device.
    trustCenterLongAddress: named.EmberEUI64


class EmberZllSecurityAlgorithmData(EzspStruct):
    # Data associated with the ZLL security algorithm.
    # Transaction identifier.
    transactionId: basic.uint32_t
    # Response identifier.
    responseId: basic.uint32_t
    # Bitmask.
    bitmask: basic.uint16_t


class EmberZllNetwork(EzspStruct):
    # The parameters of a ZLL network.
    # The parameters of a ZigBee network.
    zigbeeNetwork: EmberZigbeeNetwork
    # Data associated with the ZLL security algorithm.
    securityAlgorithm: EmberZllSecurityAlgorithmData
    # Associated EUI64.
    eui64: named.EmberEUI64
    # The node id.
    nodeId: named.EmberNodeId
    # The ZLL state.
    state: named.EmberZllState
    # The node type.
    nodeType: named.EmberNodeType
    # The number of sub devices.
    numberSubDevices: basic.uint8_t
    # The total number of group identifiers.
    totalGroupIdentifiers: basic.uint8_t
    # RSSI correction value.
    rssiCorrection: basic.uint8_t


class EmberZllInitialSecurityState(EzspStruct):
    # Describes the initial security features and requirements that will be
    # used when forming or joining ZLL networks.
    # Unused bitmask; reserved for future use.
    bitmask: basic.uint32_t
    # The key encryption algorithm advertised by the application.
    keyIndex: named.EmberZllKeyIndex
    # The encryption key for use by algorithms that require it.
    encryptionKey: named.EmberKeyData
    # The pre-configured link key used during classical ZigBee
    # commissioning.
    preconfiguredKey: named.EmberKeyData


class EmberZllDeviceInfoRecord(EzspStruct):
    # Information about a specific ZLL Device.
    # EUI64 associated with the device.
    ieeeAddress: named.EmberEUI64
    # Endpoint id.
    endpointId: basic.uint8_t
    # Profile id.
    profileId: basic.uint16_t
    # Device id.
    deviceId: basic.uint16_t
    # Associated version.
    version: basic.uint8_t
    # Number of relevant group ids.
    groupIdCount: basic.uint8_t


class EmberZllAddressAssignment(EzspStruct):
    # ZLL address assignment data.
    # Relevant node id.
    nodeId: named.EmberNodeId
    # Minimum free node id.
    freeNodeIdMin: named.EmberNodeId
    # Maximum free node id.
    freeNodeIdMax: named.EmberNodeId
    # Minimum group id.
    groupIdMin: named.EmberMulticastId
    # Maximum group id.
    groupIdMax: named.EmberMulticastId
    # Minimum free group id.
    freeGroupIdMin: named.EmberMulticastId
    # Maximum free group id.
    freeGroupIdMax: named.EmberMulticastId


class EmberTokenData(EzspStruct):
    # Token Data
    # Token data size in bytes
    size: basic.uint32_t
    # Token data pointer
    data: basic.uint8_t


class EmberTokenInfo(EzspStruct):
    # Information of a token in the token table
    # NVM3 key of the token
    nvm3Key: basic.uint32_t
    # Token is a counter type
    isCnt: named.Bool
    # Token is an indexed token
    isIdx: named.Bool
    # Size of the token
    size: basic.uint8_t
    # Array size of the token
    arraSize: basic.uint8_t


class EmberTokTypeStackZllData(EzspStruct):
    # Public API for ZLL stack data token.
    # Token bitmask.
    bitmask: basic.uint32_t
    # Minimum free node id.
    freeNodeIdMin: basic.uint16_t
    # Maximum free node id.
    freeNodeIdMax: basic.uint16_t
    # Local minimum group id.
    myGroupIdMin: basic.uint16_t
    # Minimum free group id.
    freeGroupIdMin: basic.uint16_t
    # Maximum free group id.
    freeGroupIdMax: basic.uint16_t
    # RSSI correction value.
    rssiCorrection: basic.uint8_t


class EmberTokTypeStackZllSecurity(EzspStruct):
    # Public API for ZLL stack security token.
    # Token bitmask.
    bitmask: basic.uint32_t
    # Key index.
    keyIndex: basic.uint8_t
    # Encryption key.
    encryptionKey: named.EmberKeyData
    # Preconfigured key.
    preconfiguredKey: named.EmberKeyData


class EmberGpAddress(EzspStruct):
    # A GP address structure.
    # The GPD's EUI64.
    gpdIeeeAddress: named.EmberEUI64
    # The GPD's source ID.
    sourceId: basic.uint32_t
    # The GPD Application ID.
    applicationId: basic.uint8_t
    # The GPD endpoint.
    endpoint: basic.uint8_t
