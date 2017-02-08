import asyncio
import enum
import logging

import bellows.types as t
from bellows.zigbee import endpoint, zdo


LOGGER = logging.getLogger(__name__)


class Status(enum.IntEnum):
    """The status of a Device"""
    # No initialization done
    NEW = 0
    # ZDO endpoint discovery done
    ZDO_INIT = 1


class Device:
    """A device on the network"""

    def __init__(self, application, ieee, nwk):
        self._application = application
        self._ieee = ieee
        self._nwk = nwk
        self.zdo = zdo.ZDO(self)
        self.endpoints = {0: self.zdo}
        self.lqi = None
        self.rssi = None
        self.status = Status.NEW

    @asyncio.coroutine
    def initialize(self):
        self.info("Discovering endpoints")
        epr = yield from self.zdo.request(0x0005, self._nwk)
        if epr[0] != 0:
            # TODO: Handle
            self.warn("Failed ZDO request during device initialization")
            return

        self.info("Discovered endpoints: %s", epr[2])

        for endpoint_id in epr[2]:
            self.add_endpoint(endpoint_id)

        self.status = Status.ZDO_INIT

        for endpoint_id in epr[2]:
            yield from self.endpoints[endpoint_id].initialize()

    def add_endpoint(self, endpoint_id):
        ep = endpoint.Endpoint(self, endpoint_id)
        self.endpoints[endpoint_id] = ep
        return ep

    def get_aps(self, profile, cluster, endpoint):
        f = t.EmberApsFrame()
        f.profileId = t.uint16_t(profile)
        f.clusterId = t.uint16_t(cluster)
        f.sourceEndpoint = t.uint8_t(endpoint)
        f.destinationEndpoint = t.uint8_t(endpoint)
        f.options = t.EmberApsOption(
            t.EmberApsOption.EMBER_APS_OPTION_RETRY |
            t.EmberApsOption.EMBER_APS_OPTION_ENABLE_ROUTE_DISCOVERY
        )
        f.groupId = t.uint16_t(0)
        f.sequence = t.uint8_t(self._application.get_sequence())
        return f

    def request(self, aps, data):
        return self._application.request(self._nwk, aps, data)

    def handle_request(self, aps_frame, tsn, command_id, args):
        try:
            endpoint = self.endpoints[aps_frame.destinationEndpoint]
        except KeyError:
            self.warn(
                "Request for unknown endpoint %s",
                aps_frame.destinationEndpoint,
            )
            return

        return endpoint.handle_request(aps_frame, tsn, command_id, args)

    def reply(self, aps, data):
        return self._application.reply(self._nwk, aps, data)

    def radio_details(self, lqi, rssi):
        self.lqi = lqi
        self.rssi = rssi

    def log(self, lvl, msg, *args):
        msg = '[0x%04x] ' + msg
        args = (self._nwk, ) + args
        return LOGGER.log(lvl, msg, *args)

    def debug(self, msg, *args):
        return self.log(logging.DEBUG, msg, *args)

    def info(self, msg, *args):
        return self.log(logging.INFO, msg, *args)

    def warn(self, msg, *args):
        return self.log(logging.WARNING, msg, *args)

    def error(self, msg, *args):
        return self.log(logging.ERROR, msg, *args)
