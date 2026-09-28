from unittest.mock import MagicMock, call, patch

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


@pytest.mark.parametrize(
    "version",
    [v for v in bellows.ezsp.EZSP._BY_VERSION if v >= 14],
)
@pytest.mark.parametrize(
    ("command", "data", "expected"),
    [
        # Captured from EmberZNet 8.0.2.0
        ("getExtendedTimeout", b"\x01\x00\x00\x00", [t.sl_Status.FAIL]),
        (
            "lookupNodeIdByEui64",
            b"\x00\x00\x00\x00\xf5\xac",
            [t.sl_Status.OK, 0xACF5],
        ),
        (
            "lookupNodeIdByEui64",
            b"\x2d\x00\x00\x00\xff\xff",
            [t.sl_Status.NOT_FOUND, 0xFFFF],
        ),
    ],
)
def test_extended_timeout_rx_schemas(
    version: int, command: str, data: bytes, expected: list
) -> None:
    """The status-prefixed responses are parsed by v14 and newer."""
    _, _, rx_schema = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS[command]
    result, rest = t.deserialize_dict(data, rx_schema)

    assert list(result.values()) == expected
    assert rest == b""


@pytest.mark.parametrize(
    ("curr_status", "extended_timeout"),
    [(t.sl_Status.OK, True), (t.sl_Status.FAIL, False)],
)
async def test_set_extended_timeout_already_set(
    ezsp_f, curr_status: t.sl_Status, extended_timeout: bool
) -> None:
    ezsp_f.getExtendedTimeout.return_value = (curr_status,)

    await ezsp_f.set_extended_timeout(
        nwk=0x1234,
        ieee=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
        extended_timeout=extended_timeout,
    )

    assert ezsp_f.getExtendedTimeout.mock_calls == [
        call(remoteEui64=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"))
    ]
    assert ezsp_f.lookupNodeIdByEui64.mock_calls == []
    assert ezsp_f.setExtendedTimeout.mock_calls == []


@pytest.mark.parametrize(
    ("curr_status", "extended_timeout"),
    [(t.sl_Status.FAIL, True), (t.sl_Status.OK, False)],
)
async def test_set_extended_timeout_already_have_entry(
    ezsp_f, curr_status: t.sl_Status, extended_timeout: bool
) -> None:
    ezsp_f.getExtendedTimeout.return_value = (curr_status,)
    ezsp_f.lookupNodeIdByEui64.return_value = (t.sl_Status.OK, 0x1234)
    ezsp_f.setExtendedTimeout.return_value = (t.sl_Status.OK,)

    await ezsp_f.set_extended_timeout(
        nwk=0x1234,
        ieee=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
        extended_timeout=extended_timeout,
    )

    assert ezsp_f.lookupNodeIdByEui64.mock_calls == [
        call(eui64=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"))
    ]
    assert ezsp_f.setExtendedTimeout.mock_calls == [
        call(
            remoteEui64=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
            extendedTimeout=extended_timeout,
        )
    ]
    assert ezsp_f.replaceAddressTableEntry.mock_calls == []


@pytest.mark.parametrize(
    "lookup_rsp",
    [(t.sl_Status.NOT_FOUND, 0xFFFF), (t.sl_Status.OK, 0xFFFF)],
)
async def test_set_extended_timeout_no_entry(ezsp_f, lookup_rsp: tuple) -> None:
    ezsp_f.getExtendedTimeout.return_value = (t.sl_Status.FAIL,)
    ezsp_f.lookupNodeIdByEui64.return_value = lookup_rsp
    ezsp_f.getConfigurationValue.return_value = (t.sl_Status.OK, 8)
    ezsp_f.replaceAddressTableEntry.return_value = (
        t.sl_Status.OK,
        t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
        0xFFFF,
        t.Bool.false,
    )

    with patch("bellows.ezsp.v4.random.randint") as mock_random:
        mock_random.return_value = 3
        await ezsp_f.set_extended_timeout(
            nwk=0x1234,
            ieee=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
            extended_timeout=True,
        )

    assert ezsp_f.setExtendedTimeout.mock_calls == []
    assert ezsp_f.getConfigurationValue.mock_calls == [
        call(t.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE)
    ]
    assert mock_random.mock_calls == [call(0, 8 - 1)]
    assert ezsp_f.replaceAddressTableEntry.mock_calls == [
        call(
            addressTableIndex=3,
            newEui64=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
            newId=0x1234,
            newExtendedTimeout=True,
        )
    ]


@pytest.mark.parametrize(
    ("config_rsp", "config_calls"),
    [
        ((t.sl_Status.FAIL, 0xFF), 2),  # Not cached, queried again
        ((t.sl_Status.OK, 0), 1),  # No address table
    ],
)
async def test_set_extended_timeout_no_address_table(
    ezsp_f, config_rsp: tuple, config_calls: int
) -> None:
    ezsp_f.getExtendedTimeout.return_value = (t.sl_Status.FAIL,)
    ezsp_f.lookupNodeIdByEui64.return_value = (t.sl_Status.NOT_FOUND, 0xFFFF)
    ezsp_f.getConfigurationValue.return_value = config_rsp
    ezsp_f.setExtendedTimeout.return_value = (t.sl_Status.OK,)

    for _ in range(2):
        await ezsp_f.set_extended_timeout(
            nwk=0x1234,
            ieee=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
            extended_timeout=True,
        )

    assert len(ezsp_f.getConfigurationValue.mock_calls) == config_calls
    assert ezsp_f.setExtendedTimeout.mock_calls == 2 * [
        call(
            remoteEui64=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"), extendedTimeout=True
        )
    ]
    assert ezsp_f.replaceAddressTableEntry.mock_calls == []
