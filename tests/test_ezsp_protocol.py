import asyncio
import logging

from asynctest import CoroutineMock, mock
import bellows.ezsp.v4
import bellows.ezsp.v4.types as t
import pytest


class _DummyProtocolHandler(bellows.ezsp.v4.EZSPv4):
    """Protocol handler mock."""

    @property
    def gw_mock(self):
        return self._gw

    @property
    def cb_mock(self):
        return self._handle_callback


@pytest.fixture
def prot_hndl():
    """Protocol handler mock."""
    return _DummyProtocolHandler(mock.MagicMock(), mock.MagicMock())


@pytest.mark.asyncio
async def test_command(prot_hndl):
    coro = prot_hndl.command("nop")
    prot_hndl._awaiting[prot_hndl._seq - 1][2].set_result(True)
    await coro
    assert prot_hndl._gw.data.call_count == 1


def test_receive_reply(prot_hndl):
    callback_mock = mock.MagicMock(spec_set=asyncio.Future)
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["version"][2], callback_mock)
    prot_hndl(b"\x00\xff\x00\x04\x05\x06")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert prot_hndl.cb_mock.call_count == 0


def test_receive_reply_after_timeout(prot_hndl):
    callback_mock = mock.MagicMock(spec_set=asyncio.Future)
    callback_mock.set_result.side_effect = asyncio.InvalidStateError()
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["version"][2], callback_mock)
    prot_hndl(b"\x00\xff\x00\x04\x05\x06")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert prot_hndl.cb_mock.call_count == 0


@pytest.mark.asyncio
async def test_cfg_initialize(prot_hndl, caplog):
    """Test initialization."""

    p1 = mock.patch.object(prot_hndl, "setConfigurationValue", new=CoroutineMock())
    p2 = mock.patch.object(prot_hndl, "set_source_routing", new=CoroutineMock())
    with p1 as cfg_mock, p2 as src_mock:
        cfg_mock.return_value = (t.EzspStatus.SUCCESS,)
        await prot_hndl.initialize({"ezsp_config": {}, "source_routing": True})
        assert src_mock.call_count == 1

        cfg_mock.return_value = (t.EzspStatus.ERROR_OUT_OF_MEMORY,)
        with caplog.at_level(logging.WARNING):
            await prot_hndl.initialize({"ezsp_config": {}, "source_routing": False})
            assert "Couldn't set" in caplog.text


@pytest.mark.asyncio
async def test_update_policies(prot_hndl):
    """Test update_policies."""

    with mock.patch.object(prot_hndl, "setPolicy", new=CoroutineMock()) as pol_mock:
        pol_mock.return_value = (t.EzspStatus.SUCCESS,)
        await prot_hndl.update_policies({"ezsp_policies": {}})

        pol_mock.return_value = (t.EzspStatus.ERROR_OUT_OF_MEMORY,)
        with pytest.raises(AssertionError):
            await prot_hndl.update_policies({"ezsp_policies": {}})
