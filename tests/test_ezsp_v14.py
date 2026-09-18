from unittest.mock import MagicMock, call

import pytest
import zigpy.exceptions
import zigpy.state

import bellows.ezsp
import bellows.ezsp.v14
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v14 protocol handler."""
    ezsp = bellows.ezsp.v14.EZSPv14(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 14)
    assert data == b"\x22\x00\x01\x00\x00\x0e"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


@pytest.mark.parametrize(
    "version",
    [v for v in bellows.ezsp.EZSP._BY_VERSION if v >= 14],
)
def test_leave_network_tx_schema(version: int) -> None:
    """`leaveNetwork` sends its one-byte `options` argument on v14 and newer."""
    ezsp = bellows.ezsp.EZSP._BY_VERSION[version](MagicMock(), MagicMock())
    ezsp._seq = 0x22

    data = ezsp._ezsp_frame(
        "leaveNetwork", options=t.SlZigbeeLeaveNetworkOption.WITH_NO_OPTION
    )
    assert data == b"\x22\x00\x01\x20\x00" + b"\x00"


@pytest.mark.parametrize(
    "version",
    [v for v in bellows.ezsp.EZSP._BY_VERSION if v >= 14],
)
@pytest.mark.parametrize(
    ("command", "data", "expected"),
    [
        ("leaveNetwork", b"\x00\x00\x00\x00", [t.sl_Status.OK]),
        ("setManufacturerCode", b"\x00\x00\x00\x00", [t.sl_Status.OK]),
    ],
)
def test_status_rx_schemas(
    version: int, command: str, data: bytes, expected: list
) -> None:
    """The `sl_status_t` responses are fully parsed by v14 and newer."""
    _, _, rx_schema = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS[command]
    result, rest = t.deserialize_dict(data, rx_schema)

    assert list(result.values()) == expected
    assert rest == b""


async def test_leave_network(ezsp_f) -> None:
    ezsp_f.leaveNetwork.return_value = (t.sl_Status.OK,)
    assert await ezsp_f.leave_network() == t.sl_Status.OK
    assert ezsp_f.leaveNetwork.mock_calls == [
        call(options=t.SlZigbeeLeaveNetworkOption.WITH_NO_OPTION)
    ]


async def test_leave_network_options(ezsp_f) -> None:
    ezsp_f.leaveNetwork.return_value = (t.sl_Status.OK,)
    assert (
        await ezsp_f.leave_network(
            options=t.SlZigbeeLeaveNetworkOption.WITH_OPTION_REJOIN
        )
        == t.sl_Status.OK
    )
    assert ezsp_f.leaveNetwork.mock_calls == [
        call(options=t.SlZigbeeLeaveNetworkOption.WITH_OPTION_REJOIN)
    ]


async def test_read_address_table(ezsp_f):
    def get_addr_table_info(index):
        default = (
            t.sl_Status.OK,
            t.EmberNodeId(0xFFFF),
            t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
        )
        return {
            16: (
                t.sl_Status.OK,
                t.EmberNodeId(0x44CB),
                t.EUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca"),
            ),
            17: (
                t.sl_Status.OK,
                t.EmberNodeId(0x0702),
                t.EUI64.convert("ec:1b:bd:ff:fe:2f:41:a4"),
            ),
            # Not actually seen with a real adapter
            18: (
                t.sl_Status.FAIL,
                t.EmberNodeId(0x1234),
                t.EUI64.convert("ab:cd:ab:cd:ab:cd:ab:cd"),
            ),
        }.get(index, default)

    ezsp_f.getAddressTableInfo.side_effect = get_addr_table_info
    ezsp_f.getConfigurationValue.return_value = (t.sl_Status.OK, 20)

    address_table = [key async for key in ezsp_f.read_address_table()]
    assert address_table == [
        (0x44CB, t.EUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca")),
        (0x0702, t.EUI64.convert("ec:1b:bd:ff:fe:2f:41:a4")),
    ]


async def test_get_network_key_and_tc_link_key(ezsp_f):
    def export_key(context):
        if context.core_key_type == t.SecurityManagerKeyType.NETWORK:
            return (
                t.sl_Status.OK,
                t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
                t.SecurityManagerContextV13(
                    core_key_type=t.SecurityManagerKeyType.NETWORK,
                    key_index=0,
                    derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                    eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                    multi_network_index=0,
                    flags=t.SecurityManagerContextFlags.NONE,
                    psa_key_alg_permission=0,
                ),
            )
        elif context.core_key_type == t.SecurityManagerKeyType.TC_LINK:
            return (
                t.sl_Status.OK,
                t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
                t.SecurityManagerContextV13(
                    core_key_type=t.SecurityManagerKeyType.NETWORK,
                    key_index=0,
                    derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                    eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                    multi_network_index=0,
                    flags=t.SecurityManagerContextFlags.NONE,
                    psa_key_alg_permission=0,
                ),
            )
        else:
            pytest.fail("Invalid core_key_type")

    ezsp_f.exportKey.side_effect = export_key
    ezsp_f.getNetworkKeyInfo.return_value = [
        t.sl_Status.OK,
        t.SecurityManagerNetworkKeyInfo(
            network_key_set=True,
            alternate_network_key_set=False,
            network_key_sequence_number=108,
            alt_network_key_sequence_number=0,
            network_key_frame_counter=118785,
        ),
    ]

    assert (await ezsp_f.get_network_key()) == zigpy.state.Key(
        key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
        seq=108,
        tx_counter=118785,
    )

    assert (await ezsp_f.get_tc_link_key()) == zigpy.state.Key(
        key=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
    )


async def test_get_network_key_without_network(ezsp_f):
    ezsp_f.getNetworkKeyInfo.return_value = [
        t.sl_Status.OK,
        t.SecurityManagerNetworkKeyInfo(
            network_key_set=False,  # Not set
            alternate_network_key_set=False,
            network_key_sequence_number=108,
            alt_network_key_sequence_number=0,
            network_key_frame_counter=118785,
        ),
    ]

    ezsp_f.exportKey.return_value = [
        t.sl_Status.OK,
        t.KeyData.convert("00000000000000000000000000000000"),
        t.SecurityManagerContextV13(
            core_key_type=t.SecurityManagerKeyType.NETWORK,
            key_index=0,
            derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
            eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
            multi_network_index=0,
            flags=t.SecurityManagerContextFlags.NONE,
            psa_key_alg_permission=0,
        ),
    ]

    with pytest.raises(zigpy.exceptions.NetworkNotFormed):
        await ezsp_f.get_network_key()


V14_AND_LATER = [v for v in bellows.ezsp.EZSP._BY_VERSION if v >= 14]

EUI64 = t.EUI64.convert("01:02:03:04:05:06:07:08")
EUI64_BYTES = bytes.fromhex("0807060504030201")

# `sl_zigbee_rx_packet_info_t`
PACKET_INFO_BYTES = bytes.fromhex(
    "3412" "0807060504030201" "ff" "03" "aa" "c4" "04030201"
)
PACKET_INFO = t.SlRxPacketInfo(
    sender_short_id=0x1234,
    sender_long_id=EUI64,
    binding_index=0xFF,
    address_index=0x03,
    last_hop_lqi=0xAA,
    last_hop_rssi=-60,
    last_hop_timestamp=0x01020304,
)

# `sl_zigbee_sec_man_context_t`
CONTEXT_BYTES = bytes.fromhex("04" "00" "0000" "0807060504030201" "00" "02" "00000000")
CONTEXT = t.SecurityManagerContextV13(
    core_key_type=t.SecurityManagerKeyType.APP_LINK,
    key_index=0,
    derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
    eui64=EUI64,
    multi_network_index=0,
    flags=t.SecurityManagerContextFlags.EUI_IS_VALID,
    psa_key_alg_permission=0,
)

KEY_BYTES = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
KEY = t.KeyData.convert("000102030405060708090a0b0c0d0e0f")

# `sl_zigbee_sec_man_aps_key_metadata_t`
KEY_METADATA_BYTES = bytes.fromhex("1200" "01000000" "02000000" "b400")
KEY_METADATA = t.SecurityManagerAPSKeyMetadata(
    bitmask=(
        t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
        | t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
    ),
    outgoing_frame_counter=1,
    incoming_frame_counter=2,
    ttl_in_seconds=180,
)

STATUS_OK_BYTES = bytes.fromhex("00000000")


def zll_network_found_handler_data() -> tuple[bytes, dict]:
    data = (
        # `sl_zigbee_zll_network_t`
        bytes.fromhex("0b" "3412" "0807060504030201" "01" "02" "00")
        + bytes.fromhex("78563412" "21436587" "0100")
        + bytes.fromhex("0807060504030201" "cdab" "0000" "02" "01" "00" "00")
        # `isDeviceInfoNull`
        + bytes.fromhex("00")
        # `sl_zigbee_zll_device_info_record_t`
        + bytes.fromhex("0807060504030201" "01" "5ec0" "0001" "02" "00")
        + PACKET_INFO_BYTES
    )

    expected = {
        "networkInfo": t.EmberZllNetwork(
            zigbeeNetwork=t.EmberZigbeeNetwork(
                channel=11,
                panId=0x1234,
                extendedPanId=t.ExtendedPanId.convert("01:02:03:04:05:06:07:08"),
                allowingJoin=t.Bool.true,
                stackProfile=2,
                nwkUpdateId=0,
            ),
            securityAlgorithm=t.EmberZllSecurityAlgorithmData(
                transactionId=0x12345678,
                responseId=0x87654321,
                bitmask=0x0001,
            ),
            eui64=EUI64,
            nodeId=0xABCD,
            state=t.EmberZllState(0x0000),
            nodeType=t.EmberNodeType.ROUTER,
            numberSubDevices=1,
            totalGroupIdentifiers=0,
            rssiCorrection=0,
        ),
        "isDeviceInfoNull": t.Bool.false,
        "deviceInfo": t.EmberZllDeviceInfoRecord(
            ieeeAddress=EUI64,
            endpointId=1,
            profileId=0xC05E,
            deviceId=0x0100,
            version=2,
            groupIdCount=0,
        ),
        "packetInfo": PACKET_INFO,
    }

    return data, expected


RESPONSE_LAYOUTS = [
    (
        "exportLinkKeyByEui",
        STATUS_OK_BYTES + CONTEXT_BYTES + KEY_BYTES + KEY_METADATA_BYTES,
        {
            "status": t.sl_Status.OK,
            "context": CONTEXT,
            "plaintext_key": KEY,
            "key_data": KEY_METADATA,
        },
    ),
    (
        "exportTransientKeyByIndex",
        STATUS_OK_BYTES + CONTEXT_BYTES + KEY_BYTES + KEY_METADATA_BYTES,
        {
            "status": t.sl_Status.OK,
            "context": CONTEXT,
            "plaintext_key": KEY,
            "key_data": KEY_METADATA,
        },
    ),
    (
        "exportTransientKeyByEui",
        STATUS_OK_BYTES + CONTEXT_BYTES + KEY_BYTES + KEY_METADATA_BYTES,
        {
            "status": t.sl_Status.OK,
            "context": CONTEXT,
            "plaintext_key": KEY,
            "key_data": KEY_METADATA,
        },
    ),
    (
        "getApsKeyInfo",
        STATUS_OK_BYTES + KEY_METADATA_BYTES + CONTEXT_BYTES,
        {
            "status": t.sl_Status.OK,
            "key_data": KEY_METADATA,
            "context": CONTEXT,
        },
    ),
    (
        "importKey",
        STATUS_OK_BYTES + CONTEXT_BYTES,
        {"status": t.sl_Status.OK, "context": CONTEXT},
    ),
    ("checkKeyContext", STATUS_OK_BYTES, {"status": t.sl_Status.OK}),
    ("findAndRejoinNetwork", STATUS_OK_BYTES, {"status": t.sl_Status.OK}),
    ("setAddressTableInfo", STATUS_OK_BYTES, {"status": t.sl_Status.OK}),
    ("setPowerDescriptor", STATUS_OK_BYTES, {"status": t.sl_Status.OK}),
    ("clearStoredBeacons", STATUS_OK_BYTES, {"status": t.sl_Status.OK}),
    ("sendPanIdUpdate", b"\x01", {"status": t.Bool.true}),
    (
        "readAttribute",
        b"\x00" + b"\x21" + b"\x02\x34\x12",
        {"status": t.EmberStatus.SUCCESS, "dataType": 0x21, "data": b"\x34\x12"},
    ),
    ("writeAttribute", b"\x00", {"status": t.EmberStatus.SUCCESS}),
    (
        "macPassthroughMessageHandler",
        b"\x01" + PACKET_INFO_BYTES + b"\x03abc",
        {
            "messageType": t.EmberMacPassthroughType.MAC_PASSTHROUGH_SE_INTERPAN,
            "packetInfo": PACKET_INFO,
            "messageContents": b"abc",
        },
    ),
    (
        "incomingBootloadMessageHandler",
        EUI64_BYTES + PACKET_INFO_BYTES + b"\x03abc",
        {"longId": EUI64, "packetInfo": PACKET_INFO, "messageContents": b"abc"},
    ),
    (
        "zllNetworkFoundHandler",
        *zll_network_found_handler_data(),
    ),
    (
        "zllAddressAssignmentHandler",
        bytes.fromhex("0100" "0200" "fff7" "0100" "ff00" "0001" "fffe")
        + PACKET_INFO_BYTES,
        {
            "addressInfo": t.EmberZllAddressAssignment(
                nodeId=0x0001,
                freeNodeIdMin=0x0002,
                freeNodeIdMax=0xF7FF,
                groupIdMin=0x0001,
                groupIdMax=0x00FF,
                freeGroupIdMin=0x0100,
                freeGroupIdMax=0xFEFF,
            ),
            "packetInfo": PACKET_INFO,
        },
    ),
    (
        "rawTransmitCompleteHandler",
        b"\x03abc" + bytes.fromhex("01000000"),
        {"messageContents": b"abc", "status": t.sl_Status.FAIL},
    ),
]


@pytest.mark.parametrize("version", V14_AND_LATER)
@pytest.mark.parametrize(
    ("name", "data", "expected"),
    RESPONSE_LAYOUTS,
    ids=[name for name, _, _ in RESPONSE_LAYOUTS],
)
def test_v14_response_layouts(
    version: int, name: str, data: bytes, expected: dict
) -> None:
    """Responses and callbacks whose layout changed in v14 parse SDK-layout bytes."""
    _, _, rx_schema = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS[name]
    result, rest = t.deserialize_dict(data, rx_schema)

    assert rest == b""
    assert result == expected


@pytest.mark.parametrize("version", [v for v in V14_AND_LATER if v < 18])
def test_v14_mac_filter_match_message_handler(version: int) -> None:
    _, _, rx_schema = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS[
        "macFilterMatchMessageHandler"
    ]
    result, rest = t.deserialize_dict(
        b"\x02" + b"\x01" + PACKET_INFO_BYTES + b"\x03abc", rx_schema
    )

    assert rest == b""
    assert result == {
        "filterIndexMatch": 2,
        "legacyPassthroughType": t.EmberMacPassthroughType.MAC_PASSTHROUGH_SE_INTERPAN,
        "packetInfo": PACKET_INFO,
        "messageContents": b"abc",
    }


REQUEST_LAYOUTS = [
    (
        "findAndRejoinNetwork",
        {
            "haveCurrentNetworkKey": True,
            "channelMask": 0x07FFF800,
            "reason": 0x03,
            "nodeType": t.EmberNodeType.ROUTER,
        },
        bytes.fromhex("01" "00f8ff07" "03" "02"),
    ),
    (
        "setAddressTableInfo",
        {"index": 5, "eui64": EUI64, "nwk": 0xABCD},
        b"\x05" + EUI64_BYTES + b"\xcd\xab",
    ),
    ("checkKeyContext", {"context": CONTEXT}, CONTEXT_BYTES),
    ("getApsKeyInfo", {"context_in": CONTEXT}, CONTEXT_BYTES),
    ("importKey", {"context": CONTEXT, "key": KEY}, CONTEXT_BYTES + KEY_BYTES),
    ("setPowerDescriptor", {"descriptor": 0x0010}, b"\x10\x00"),
]


@pytest.mark.parametrize("version", V14_AND_LATER)
@pytest.mark.parametrize(
    ("name", "kwargs", "data"),
    REQUEST_LAYOUTS,
    ids=[name for name, _, _ in REQUEST_LAYOUTS],
)
def test_v14_request_layouts(
    version: int, name: str, kwargs: dict, data: bytes
) -> None:
    """Requests whose layout changed in v14 serialize to the SDK layout."""
    _, tx_schema, _ = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS[name]

    assert t.serialize_dict((), kwargs, tx_schema) == data


@pytest.mark.parametrize("version", V14_AND_LATER)
@pytest.mark.parametrize(
    "name",
    [
        "setAddressTableRemoteEui64",
        "setAddressTableRemoteNodeId",
        "getAddressTableRemoteNodeId",
        "incomingSenderEui64Handler",
        "getFirstBeacon",
        "getNextBeacon",
        "proxyBroadcast",
        "sendMulticastWithAlias",
        "sendRawMessage",
        "setLongUpTime",
        "setHubConnectivity",
        "isUpTimeLong",
        "isHubConnected",
        "setParentClassificationEnabled",
        "getParentClassificationEnabled",
    ],
)
def test_v14_removed_commands(version: int, name: str) -> None:
    """Commands removed from the SDK in v14 are not defined."""
    assert name not in bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS


@pytest.mark.parametrize("version", V14_AND_LATER)
def test_no_duplicate_frame_ids(version: int) -> None:
    """Every frame ID maps to a single command."""
    names_by_id: dict[int, list[str]] = {}

    for name, (cmd_id, _, _) in bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS.items():
        names_by_id.setdefault(cmd_id, []).append(name)

    assert {k: v for k, v in names_by_id.items() if len(v) > 1} == {}


async def test_send_unicast(ezsp_f) -> None:
    ezsp_f.sendUnicast.return_value = (t.sl_Status.OK, 0x0042)
    status, message_tag = await ezsp_f.send_unicast(
        nwk=0x1234,
        aps_frame=t.EmberApsFrame(),
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendUnicast.mock_calls == [
        call(
            message_type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            nwk=0x1234,
            aps_frame=t.EmberApsFrame(),
            message_tag=0x42,
            message=b"hello",
        )
    ]


async def test_send_multicast(ezsp_f) -> None:
    ezsp_f.sendMulticast.return_value = (t.sl_Status.OK, 0x0042)
    status, message_tag = await ezsp_f.send_multicast(
        aps_frame=t.EmberApsFrame(sequence=0x34),
        radius=12,
        non_member_radius=34,
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendMulticast.mock_calls == [
        call(
            aps_frame=t.EmberApsFrame(sequence=0x34),
            hops=12,
            broadcast_addr=t.BroadcastAddress.RX_ON_WHEN_IDLE,
            alias=0x0000,
            sequence=0x34,
            message_tag=0x0042,
            message=b"hello",
        )
    ]


async def test_send_broadcast(ezsp_f) -> None:
    ezsp_f.sendBroadcast.return_value = (t.sl_Status.OK, 0x0042)
    status, message_tag = await ezsp_f.send_broadcast(
        address=t.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
        aps_frame=t.EmberApsFrame(),
        radius=12,
        message_tag=0x42,
        aps_sequence=34,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendBroadcast.mock_calls == [
        call(
            alias=0x0000,
            destination=t.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
            sequence=34,
            aps_frame=t.EmberApsFrame(),
            radius=12,
            message_tag=0x42,
            message=b"hello",
        )
    ]
