import logging

import bellows.types as t

from . import types


LOGGER = logging.getLogger(__name__)


def deserialize(aps_frame, data):
    tsn, data = data[0], data[1:]

    try:
        cluster_details = types.CLUSTERS[aps_frame.clusterId]
    except KeyError:
        LOGGER.warning("Unknown ZDO cluster 0x%02x", aps_frame.clusterId)
        is_reply = bool(aps_frame.clusterId & 0x8000)
        return tsn, aps_frame.clusterId, is_reply, data

    args, data = t.deserialize(data, cluster_details[2])
    if data != b'':
        # TODO: Seems sane to check, but what should we do?
        LOGGER.warning("Data remains after deserializing ZDO frame")
    return tsn, aps_frame.clusterId, bool(aps_frame.clusterId & 0x8000), args


class ZDO:
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

    def handle_request(self, aps_frame, tsn, command_id, args):
        app = self._device._application
        if command_id == 0x0000:  # NWK_addr_req
            if app._ieee == args[0]:
                self.reply(0x8000, 0, app._ieee, app._nwk, 0, 0, [])
        if command_id == 0x0001:  # IEEE_addr_req
            if app._nwk == args[0]:
                self.reply(0x8001, 0, app._ieee, app._nwk, 0, 0, [])
        elif command_id == 0x0006:  # Match_Desc_req
            self.handle_match_desc(*args)
        elif command_id == 0x0013:  # Device_annce
            app.add_device(args[1], args[2])
        else:
            LOGGER.warning("Unsupported ZDO request 0x%04x", command_id)

    def handle_match_desc(self, addr, profile, in_clusters, out_clusters):
        if profile == 260:
            response = (0x8006, 0, addr, [t.uint8_t(1)])
        else:
            response = (0x8006, 0, addr, [])

        self.reply(*response)

    def handle_device_announce(self, addr, ieee, capability):
        pass

    def bind(self, endpoint, cluster):
        dstaddr = types.MultiAddress()
        dstaddr.addrmode = 3
        dstaddr.ieee = self._device._application._ieee
        dstaddr.endpoint = 1
        return self.request(0x0021, self._device._ieee, endpoint, cluster, dstaddr)

    def unbind(self, endpoint, cluster):
        dstaddr = types.MultiAddress()
        dstaddr.addrmode = 3
        dstaddr.ieee = self._device._application._ieee
        dstaddr.endpoint = 1
        return self.request(0x0022, self._device._ieee, endpoint, cluster, dstaddr)
