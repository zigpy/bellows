import asyncio
import enum
import logging

import bellows.zigbee.appdb
import bellows.zigbee.profiles
import bellows.zigbee.util as zutil
import bellows.zigbee.zcl

LOGGER = logging.getLogger(__name__)


class Status(enum.IntEnum):
    """The status of an Endpoint"""
    # No initialization is done
    NEW = 0
    # Endpoint information (device type, clusters, etc) init done
    ZDO_INIT = 1


class Endpoint(zutil.LocalLogMixin, zutil.ListenableMixin):
    """An endpoint on a device on the network"""
    def __init__(self, device, endpoint_id):
        self._device = device
        self._endpoint_id = endpoint_id
        self.in_clusters = {}
        self.out_clusters = {}
        self._cluster_attr = {}
        self.status = Status.NEW
        self._listeners = {}

    @asyncio.coroutine
    def initialize(self):
        if self.status == Status.ZDO_INIT:
            return

        self.info("Discovering endpoint information")
        try:
            sdr = yield from self._device.zdo.request(
                0x0004,
                self._device.nwk,
                self._endpoint_id,
                tries=3,
                delay=2,
            )
            if sdr[0] != 0:
                raise Exception("Failed to retrieve service descriptor: %s", sdr)
        except Exception as exc:
            self.warn("Failed ZDO request during device initialization: %s", exc)
            return

        self.info("Discovered endpoint information: %s", sdr[2])
        sd = sdr[2]
        self.profile_id = sd.profile
        self.device_type = sd.device_type
        try:
            if self.profile_id == 260:
                self.device_type = bellows.zigbee.profiles.zha.DeviceType(self.device_type)
            elif self.profile_id == 49246:
                self.device_type = bellows.zigbee.profiles.zll.DeviceType(self.device_type)
        except:
            pass

        for cluster in sd.input_clusters:
            self.add_input_cluster(cluster)
        for cluster in sd.output_clusters:
            self.add_output_cluster(cluster)

        self.status = Status.ZDO_INIT

    def add_input_cluster(self, cluster_id):
        """Adds an endpoint's input cluster

        (a server cluster supported by the device)
        """
        if cluster_id in self.in_clusters:
            return self.in_clusters[cluster_id]

        cluster = bellows.zigbee.zcl.Cluster.from_id(self, cluster_id)
        self.in_clusters[cluster_id] = cluster
        if hasattr(cluster, 'ep_attribute'):
            self._cluster_attr[cluster.ep_attribute] = cluster

        listener = bellows.zigbee.appdb.ClusterPersistingListener(
            self._device.application._dblistener,
            cluster,
        )
        cluster.add_listener(listener)

        return cluster

    def add_output_cluster(self, cluster_id):
        """Adds an endpoint's output cluster

        (a client cluster supported by the device)
        """
        if cluster_id in self.out_clusters:
            return self.out_clusters[cluster_id]

        cluster = bellows.zigbee.zcl.Cluster.from_id(self, cluster_id)
        self.out_clusters[cluster_id] = cluster
        return cluster

    def get_aps(self, cluster):
        assert self.status != Status.NEW
        return self._device.get_aps(
            profile=self.profile_id,
            cluster=cluster,
            endpoint=self._endpoint_id,
        )

    def handle_message(self, is_reply, aps_frame, tsn, command_id, args):
        handler = None
        if aps_frame.clusterId in self.in_clusters:
            handler = self.in_clusters[aps_frame.clusterId].handle_message
        elif aps_frame.clusterId in self.out_clusters:
            handler = self.out_clusters[aps_frame.clusterId].handle_message
        else:
            self.warn("Message on unknown cluster 0x%04x", aps_frame.clusterId)
            self.listener_event("unknown_cluster_message", is_reply,
                                command_id, args)
            return

        handler(is_reply, aps_frame, tsn, command_id, args)

    def log(self, lvl, msg, *args):
        msg = '[0x%04x:%s] ' + msg
        args = (self._device.nwk, self._endpoint_id) + args
        return LOGGER.log(lvl, msg, *args)

    @property
    def device(self):
        return self._device

    @property
    def endpoint_id(self):
        return self._endpoint_id

    def __getattr__(self, name):
        try:
            return self._cluster_attr[name]
        except KeyError:
            raise AttributeError
