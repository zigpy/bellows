import asyncio
import binascii
import logging
import os

from zigpy.exceptions import DeliveryError
import zigpy.application
import zigpy.device
import zigpy.util

import bellows.types as t
import bellows.zigbee.util

LOGGER = logging.getLogger(__name__)


class ControllerApplication(zigpy.application.ControllerApplication):
    direct = t.EmberOutgoingMessageType.OUTGOING_DIRECT

    def __init__(self, ezsp, database_file=None):
        super().__init__(database_file=database_file)
        self._ezsp = ezsp
        self._pending = {}

    @asyncio.coroutine
    def initialize(self):
        """Perform basic NCP initialization steps"""
        e = self._ezsp

        yield from e.reset()
        yield from e.version()

        c = t.EzspConfigId
        yield from self._cfg(c.CONFIG_STACK_PROFILE, 2)
        yield from self._cfg(c.CONFIG_SECURITY_LEVEL, 5)
        yield from self._cfg(c.CONFIG_SUPPORTED_NETWORKS, 1)
        zdo = (
            t.EmberZdoConfigurationFlags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS |
            t.EmberZdoConfigurationFlags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
        )
        yield from self._cfg(c.CONFIG_APPLICATION_ZDO_FLAGS, zdo)
        yield from self._cfg(c.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE, 2)
        yield from self._cfg(c.CONFIG_PACKET_BUFFER_COUNT, 0xff)
        yield from self._cfg(c.CONFIG_KEY_TABLE_SIZE, 1)
        yield from self._cfg(c.CONFIG_TRANSIENT_KEY_TIMEOUT_S, 180, True)
        yield from self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT, 60)
        yield from self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT, 6)

    @asyncio.coroutine
    def startup(self, auto_form=False):
        """Perform a complete application startup"""
        yield from self.initialize()
        e = self._ezsp

        v = yield from e.networkInit()
        if v[0] != t.EmberStatus.SUCCESS:
            if not auto_form:
                raise Exception("Could not initialize network")
            yield from self.form_network()

        v = yield from e.getNetworkParameters()
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check
        if v[1] != t.EmberNodeType.COORDINATOR:
            if not auto_form:
                raise Exception("Network not configured as coordinator")

            LOGGER.info("Forming network")
            yield from self._ezsp.leaveNetwork()
            yield from asyncio.sleep(1)  # TODO
            yield from self.form_network()

        yield from self._policy()
        nwk = yield from e.getNodeId()
        self._nwk = nwk[0]
        ieee = yield from e.getEui64()
        self._ieee = ieee[0]

        e.add_callback(self.ezsp_callback_handler)

    @asyncio.coroutine
    def form_network(self, channel=15, pan_id=None, extended_pan_id=None):
        channel = t.uint8_t(channel)

        if pan_id is None:
            pan_id = t.uint16_t.from_bytes(os.urandom(2), 'little')
        pan_id = t.uint16_t(pan_id)

        if extended_pan_id is None:
            extended_pan_id = t.fixed_list(8, t.uint8_t)([t.uint8_t(0)] * 8)

        initial_security_state = bellows.zigbee.util.zha_security(controller=True)
        v = yield from self._ezsp.setInitialSecurityState(initial_security_state)
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check

        parameters = t.EmberNetworkParameters()
        parameters.panId = pan_id
        parameters.extendedPanId = extended_pan_id
        parameters.radioTxPower = t.uint8_t(8)
        parameters.radioChannel = channel
        parameters.joinMethod = t.EmberJoinMethod.USE_MAC_ASSOCIATION
        parameters.nwkManagerId = t.EmberNodeId(0)
        parameters.nwkUpdateId = t.uint8_t(0)
        parameters.channels = t.uint32_t(0)

        yield from self._ezsp.formNetwork(parameters)
        yield from self._ezsp.setValue(t.EzspValueId.VALUE_STACK_TOKEN_WRITING, 1)

    @asyncio.coroutine
    def _cfg(self, config_id, value, optional=False):
        v = yield from self._ezsp.setConfigurationValue(config_id, value)
        if not optional:
            assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check

    @asyncio.coroutine
    def _policy(self):
        """Set up the policies for what the NCP should do"""
        e = self._ezsp
        v = yield from e.setPolicy(
            t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            t.EzspDecisionId.DENY_TC_KEY_REQUESTS,
        )
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check
        v = yield from e.setPolicy(
            t.EzspPolicyId.APP_KEY_REQUEST_POLICY,
            t.EzspDecisionId.ALLOW_APP_KEY_REQUESTS,
        )
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check
        v = yield from e.setPolicy(
            t.EzspPolicyId.TRUST_CENTER_POLICY,
            t.EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
        )
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check

    @asyncio.coroutine
    def force_remove(self, dev):
        # This should probably be delivered to the parent device instead
        # of the device itself.
        yield from self._ezsp.removeDevice(dev.nwk, dev.ieee, dev.ieee)

    def ezsp_callback_handler(self, frame_name, args):
        if frame_name == 'incomingMessageHandler':
            self._handle_frame(*args)
        elif frame_name == 'messageSentHandler':
            if args[4] != t.EmberStatus.SUCCESS:
                self._handle_frame_failure(*args)
            else:
                self._handle_frame_sent(*args)
        elif frame_name == 'trustCenterJoinHandler':
            if args[2] == t.EmberDeviceUpdate.DEVICE_LEFT:
                self.handle_leave(args[0], args[1])
            else:
                self.handle_join(args[0], args[1], args[4])

    def _handle_frame(self, message_type, aps_frame, lqi, rssi, sender, binding_index, address_index, message):
        try:
            self.get_device(nwk=sender).radio_details(lqi, rssi)
        except KeyError:
            LOGGER.debug("No such device %s", sender)

        if aps_frame.destinationEndpoint == 0:
            deserialize = zigpy.zdo.deserialize
        else:
            deserialize = zigpy.zcl.deserialize

        try:
            tsn, command_id, is_reply, args = deserialize(aps_frame.clusterId, message)
        except ValueError as e:
            LOGGER.error("Failed to parse message (%s) on cluster %d, because %s", binascii.hexlify(message), aps_frame.clusterId, e)
            return

        if is_reply:
            self._handle_reply(sender, aps_frame, tsn, command_id, args)
        else:
            self.handle_message(False, sender, aps_frame.profileId, aps_frame.clusterId, aps_frame.sourceEndpoint, aps_frame.destinationEndpoint, tsn, command_id, args)

    def _handle_reply(self, sender, aps_frame, tsn, command_id, args):
        try:
            send_fut, reply_fut = self._pending[tsn]
            if send_fut.done():
                self._pending.pop(tsn)
            if reply_fut:
                reply_fut.set_result(args)
            return
        except KeyError:
            LOGGER.warning("Unexpected response TSN=%s command=%s args=%s", tsn, command_id, args)
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug("Invalid state on future - probably duplicate response: %s", exc)
            # We've already handled, don't drop through to device handler
            return

        self.handle_message(True, sender, aps_frame.profileId, aps_frame.clusterId, aps_frame.sourceEndpoint, aps_frame.destinationEndpoint, tsn, command_id, args)

    def _handle_frame_failure(self, message_type, destination, aps_frame, message_tag, status, message):
        try:
            send_fut, reply_fut = self._pending.pop(message_tag)
            send_fut.set_exception(DeliveryError("Message send failure: %s" % (status, )))
            if reply_fut:
                reply_fut.cancel()
        except KeyError:
            LOGGER.warning("Unexpected message send failure")
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug("Invalid state on future - probably duplicate response: %s", exc)

    def _handle_frame_sent(self, message_type, destination, aps_frame, message_tag, status, message):
        try:
            send_fut, reply_fut = self._pending[message_tag]
            # Sometimes messageSendResult and a reply come out of order
            # If we've already handled the reply, delete pending
            if reply_fut is None or reply_fut.done():
                self._pending.pop(message_tag)
            send_fut.set_result(True)
        except KeyError:
            LOGGER.warning("Unexpected message send notification")
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug("Invalid state on future - probably duplicate response: %s", exc)

    @zigpy.util.retryable_request
    @asyncio.coroutine
    def request(self, nwk, profile, cluster, src_ep, dst_ep, sequence, data, expect_reply=True, timeout=10):
        assert sequence not in self._pending
        send_fut = asyncio.Future()
        reply_fut = None
        if expect_reply:
            reply_fut = asyncio.Future()
        self._pending[sequence] = (send_fut, reply_fut)

        aps_frame = t.EmberApsFrame()
        aps_frame.profileId = t.uint16_t(profile)
        aps_frame.clusterId = t.uint16_t(cluster)
        aps_frame.sourceEndpoint = t.uint8_t(src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(dst_ep)
        aps_frame.options = t.EmberApsOption(
            t.EmberApsOption.APS_OPTION_RETRY |
            t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        )
        aps_frame.groupId = t.uint16_t(0)
        aps_frame.sequence = t.uint8_t(sequence)

        v = yield from self._ezsp.sendUnicast(self.direct, nwk, aps_frame, sequence, data)
        if v[0] != t.EmberStatus.SUCCESS:
            self._pending.pop(sequence)
            send_fut.cancel()
            if expect_reply:
                reply_fut.cancel()
            raise DeliveryError("Message send failure %s" % (v[0], ))

        # Wait for messageSentHandler message
        v = yield from send_fut
        if expect_reply:
            # Wait for reply
            v = yield from asyncio.wait_for(reply_fut, timeout)
        return v

    def permit(self, time_s=60):
        assert 0 <= time_s <= 254
        return self._ezsp.permitJoining(time_s)

    def permit_with_key(self, node, code, time_s=60):
        if type(node) is not t.EmberEUI64:
            node = t.EmberEUI64([t.uint8_t(p) for p in node])

        key = zigpy.util.convert_install_code(code)
        if key is None:
            raise Exception("Invalid install code")

        v = yield from self._ezsp.addTransientLinkKey(node, key)
        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception("Failed to set link key")

        v = yield from self._ezsp.setPolicy(
            t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            t.EzspDecisionId.GENERATE_NEW_TC_LINK_KEY,
        )
        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception("Failed to change policy to allow generation of new trust center keys")

        return self._ezsp.permitJoining(time_s, True)
