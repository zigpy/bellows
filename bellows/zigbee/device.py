import asyncio
import enum
import logging

import bellows.types as t
import bellows.zigbee.endpoint
import bellows.zigbee.util as zutil
import bellows.zigbee.zdo as zdo
from bellows.zigbee.zdo.types import CLUSTER_ID


LOGGER = logging.getLogger(__name__)


class Status(enum.IntEnum):
    """The status of a Device"""
    # No initialization done
    NEW = 0
    # ZDO endpoint discovery done
    ZDO_INIT = 1
    # Endpoints initialized
    ENDPOINTS_INIT = 2
    # Initialization finished
    INITIALIZED = 100


class Device(zutil.LocalLogMixin):
    """A device on the network"""

    def __init__(self, application, ieee, nwk, manufacturer=None):
        self._application = application
        self._ieee = ieee
        self.nwk = nwk
        self.zdo = zdo.ZDO(self)
        self.endpoints = {0: self.zdo}
        self.lqi = None
        self.rssi = None
        self.status = Status.NEW
        self.initializing = False
        self._manufacturer_code = manufacturer

    def schedule_initialize(self):
        self.initializing = True
        loop = asyncio.get_event_loop()
        loop.call_soon(asyncio.async, self._initialize())

    @asyncio.coroutine
    def _discover_endpoints(self):
        self.info("Discovering endpoints")
        try:
            epr = yield from self.zdo.request(CLUSTER_ID.Active_EP_req, self.nwk, tries=3, delay=2)
            if epr[0] != 0:
                raise Exception("Endpoint request failed: %s", epr)
        except Exception as exc:
            self.initializing = False
            self.warn("Failed ZDO request during device initialization: %s", exc)
            return

        self.info("Discovered endpoints: %s", epr[2])

        for endpoint_id in epr[2]:
            self.add_endpoint(endpoint_id)

        for endpoint_id in self.endpoints.keys():
            if endpoint_id == 0:  # ZDO
                continue
            yield from self.endpoints[endpoint_id].initialize()

    @asyncio.coroutine
    def get_manufacturer_code(self):
        if self._manufacturer_code is None:
            try:
                ndr = yield from self.zdo.request(
                    CLUSTER_ID.Node_Desc_req,
                    self.nwk,
                    tries=3,
                    delay=2,
                )

                if ndr[0] != 0:
                    raise Exception("Failed to retrieve node descriptor: %s", ndr)

                self.info("Discovered node information: %s", ndr[2])
                self._manufacturer_code = ndr[2].manufacturer_code
            except Exception as exc:
                self.warn("Failed ZDO request: %s", exc)
                return
        return self._manufacturer_code

    @property
    def manufacturer_code(self):
        return self._manufacturer_code

    @asyncio.coroutine
    def _initialize(self):
        if self.status == Status.NEW:
            yield from self._discover_endpoints()
            self.status = Status.ZDO_INIT

        self.status = Status.ENDPOINTS_INIT
        yield from self.get_manufacturer_code()
        self.status = Status.INITIALIZED
        self.initializing = False
        self._application.listener_event('device_initialized', self)

    def add_endpoint(self, endpoint_id):
        if endpoint_id not in self.endpoints:
            ep = bellows.zigbee.endpoint.Endpoint(self, endpoint_id)
            self.endpoints[endpoint_id] = ep
            return ep

    def get_aps(self, profile, cluster, endpoint):
        f = t.EmberApsFrame()
        f.profileId = t.uint16_t(profile)
        f.clusterId = t.uint16_t(cluster)
        f.sourceEndpoint = t.uint8_t(endpoint)
        f.destinationEndpoint = t.uint8_t(endpoint)
        f.options = t.EmberApsOption(
            t.EmberApsOption.APS_OPTION_RETRY |
            t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        )
        f.groupId = t.uint16_t(0)
        f.sequence = t.uint8_t(self._application.get_sequence())
        return f

    def request(self, aps, data):
        return self._application.request(self.nwk, aps, data)

    def handle_message(self, is_reply, aps_frame, tsn, command_id, args):
        try:
            endpoint = self.endpoints[aps_frame.destinationEndpoint]
        except KeyError:
            self.warn(
                "Message on unknown endpoint %s",
                aps_frame.destinationEndpoint,
            )
            return

        return endpoint.handle_message(is_reply, aps_frame, tsn, command_id, args)

    def reply(self, aps, data):
        return self._application.reply(self.nwk, aps, data)

    def radio_details(self, lqi, rssi):
        self.lqi = lqi
        self.rssi = rssi

    def log(self, lvl, msg, *args):
        msg = '[0x%04x] ' + msg
        args = (self.nwk, ) + args
        return LOGGER.log(lvl, msg, *args)

    @property
    def application(self):
        return self._application

    @property
    def ieee(self):
        return self._ieee

    def __getitem__(self, key):
        return self.endpoints[key]
