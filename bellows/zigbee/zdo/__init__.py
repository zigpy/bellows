import functools
import logging

import bellows.types as t
from bellows.zigbee import util

from . import types
from .types import CLUSTER_ID


LOGGER = logging.getLogger(__name__)


def deserialize(cluster_id, data):
    tsn, data = data[0], data[1:]

    is_reply = bool(cluster_id & 0x8000)
    try:
        cluster_details = types.CLUSTERS[cluster_id]
    except KeyError:
        LOGGER.warning("Unknown ZDO cluster 0x%02x", cluster_id)
        return tsn, cluster_id, is_reply, data

    args, data = t.deserialize(data, cluster_details[2])
    if data != b'':
        # TODO: Seems sane to check, but what should we do?
        LOGGER.warning("Data remains after deserializing ZDO frame")

    return tsn, cluster_id, is_reply, args


class ZDO(util.LocalLogMixin, util.ListenableMixin):
    """The ZDO endpoint of a device"""
    def __init__(self, device):
        self._device = device
        self._listeners = {}

    def _serialize(self, command, *args):
        aps = self._device.get_aps(profile=0, cluster=command, endpoint=0)
        data = aps.sequence.to_bytes(1, 'little')
        schema = types.CLUSTERS[command][2]
        data += t.serialize(args, schema)
        return aps, data

    @util.retryable_request
    def request(self, command, *args):
        if isinstance(command, str):
            command = CLUSTER_ID[command]
        aps, data = self._serialize(command, *args)
        return self._device.request(aps, data)

    def reply(self, command, *args):
        aps, data = self._serialize(command, *args)
        return self._device.reply(aps, data)

    def handle_message(self, is_reply, aps_frame, tsn, command_id, args):
        if is_reply:
            self.debug("Unexpected ZDO reply 0x%04x: %s", command_id, args)
            return

        self.debug("ZDO request 0x%04x: %s", command_id, args)
        app = self._device.application
        if command_id == CLUSTER_ID.NWK_addr_req:
            if app.ieee == args[0]:
                self.reply(CLUSTER_ID.NWK_addr_rsp, 0, app.ieee, app.nwk, 0, 0, [])
        elif command_id == CLUSTER_ID.IEEE_addr_req:  # IEEE_addr_req
            broadcast = (0xffff, 0xfffd, 0xfffc)
            if args[0] in broadcast or app.nwk == args[0]:
                self.reply(CLUSTER_ID.IEEE_addr_rsp, 0, app.ieee, app.nwk, 0, 0, [])
        elif command_id == CLUSTER_ID.Match_Desc_req:  # Match_Desc_req
            self.handle_match_desc(*args)
        elif command_id == CLUSTER_ID.Device_annce:
            self.listener_event('device_announce', self._device)
        else:
            self.warn("Unsupported ZDO request 0x%04x", command_id)

    def handle_match_desc(self, addr, profile, in_clusters, out_clusters):
        local_addr = self._device.application.nwk
        if profile == 260:
            response = (CLUSTER_ID.Match_Desc_rsp, 0, local_addr, [t.uint8_t(1)])
        else:
            response = (CLUSTER_ID.Match_Desc_rsp, 0, local_addr, [])

        self.reply(*response)

    def bind(self, endpoint, cluster):
        dstaddr = types.MultiAddress()
        dstaddr.addrmode = 3
        dstaddr.ieee = self._device.application.ieee
        dstaddr.endpoint = 1
        return self.request(CLUSTER_ID.Bind_req, self._device.ieee, endpoint, cluster, dstaddr)

    def unbind(self, endpoint, cluster):
        dstaddr = types.MultiAddress()
        dstaddr.addrmode = 3
        dstaddr.ieee = self._device.application.ieee
        dstaddr.endpoint = 1
        return self.request(CLUSTER_ID.Unbind_req, self._device.ieee, endpoint, cluster, dstaddr)

    def leave(self):
        dstaddr = types.MultiAddress()
        dstaddr.addrmode = 3
        dstaddr.ieee = self._device.application.ieee
        dstaddr.endpoint = 1
        return self.request(CLUSTER_ID.Mgmt_Leave_req, self._device.ieee, 0x02, dstaddr)

    def log(self, lvl, msg, *args):
        msg = '[0x%04x:zdo] ' + msg
        args = (
            self._device.nwk,
        ) + args
        return LOGGER.log(lvl, msg, *args)

    @property
    def device(self):
        return self._device

    def __getattr__(self, name):
        try:
            return functools.partial(
                self.request,
                CLUSTER_ID[name],
            )
        except KeyError:
            raise AttributeError("No such zdo command name: %s" % (name, ))
