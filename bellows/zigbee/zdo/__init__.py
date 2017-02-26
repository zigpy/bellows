import logging

import bellows.types as t
from bellows.zigbee import util

from . import types


LOGGER = logging.getLogger(__name__)


def deserialize(aps_frame, data):
    tsn, data = data[0], data[1:]

    is_reply = bool(aps_frame.clusterId & 0x8000)
    try:
        cluster_details = types.CLUSTERS[aps_frame.clusterId]
    except KeyError:
        LOGGER.warning("Unknown ZDO cluster 0x%02x", aps_frame.clusterId)
        return tsn, aps_frame.clusterId, is_reply, data

    args, data = t.deserialize(data, cluster_details[2])
    if data != b'':
        # TODO: Seems sane to check, but what should we do?
        LOGGER.warning("Data remains after deserializing ZDO frame")

    return tsn, aps_frame.clusterId, is_reply, args


class ZDO(util.LocalLogMixin):
    """The ZDO endpoint of a device"""
    def __init__(self, device):
        self._device = device

    def _serialize(self, command, *args):
        aps = self._device.get_aps(profile=0, cluster=command, endpoint=0)
        data = aps.sequence.to_bytes(1, 'little')
        schema = types.CLUSTERS[command][2]
        data += t.serialize(args, schema)
        return aps, data

    def request(self, command, *args):
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
        if command_id == 0x0000:  # NWK_addr_req
            if app.ieee == args[0]:
                self.reply(0x8000, 0, app.ieee, app.nwk, 0, 0, [])
        elif command_id == 0x0001:  # IEEE_addr_req
            broadcast = (0xffff, 0xfffd, 0xfffc)
            if args[0] in broadcast or app.nwk == args[0]:
                self.reply(0x8001, 0, app.ieee, app.nwk, 0, 0, [])
        elif command_id == 0x0006:  # Match_Desc_req
            self.handle_match_desc(*args)
        elif command_id == 0x0013:  # Device_annce
            pass
        else:
            self.warn("Unsupported ZDO request 0x%04x", command_id)

    def handle_match_desc(self, addr, profile, in_clusters, out_clusters):
        local_addr = self._device.application.nwk
        if profile == 260:
            response = (0x8006, 0, local_addr, [t.uint8_t(1)])
        else:
            response = (0x8006, 0, local_addr, [])

        self.reply(*response)

    def bind(self, endpoint, cluster):
        dstaddr = types.MultiAddress()
        dstaddr.addrmode = 3
        dstaddr.ieee = self._device.application.ieee
        dstaddr.endpoint = 1
        return self.request(0x0021, self._device.ieee, endpoint, cluster, dstaddr)

    def unbind(self, endpoint, cluster):
        dstaddr = types.MultiAddress()
        dstaddr.addrmode = 3
        dstaddr.ieee = self._device.application.ieee
        dstaddr.endpoint = 1
        return self.request(0x0022, self._device.ieee, endpoint, cluster, dstaddr)

    def log(self, lvl, msg, *args):
        msg = '[0x%04x:zdo] ' + msg
        args = (
            self._device.nwk,
        ) + args
        return LOGGER.log(lvl, msg, *args)

    @property
    def device(self):
        return self._device
