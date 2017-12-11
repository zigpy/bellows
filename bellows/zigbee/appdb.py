import logging
import sqlite3

import bellows.types as t
import bellows.zigbee.device
import bellows.zigbee.endpoint
import bellows.zigbee.profiles


LOGGER = logging.getLogger(__name__)


def _sqlite_adapters():
    def adapt_ieee(eui64):
        return repr(eui64)
    sqlite3.register_adapter(t.EmberEUI64, adapt_ieee)

    def convert_ieee(s):
        l = [t.uint8_t(p, base=16) for p in s.split(b':')]
        return t.EmberEUI64(l)
    sqlite3.register_converter("ieee", convert_ieee)


class PersistingListener:
    def __init__(self, database_file, application):
        self._database_file = database_file
        _sqlite_adapters()
        self._db = sqlite3.connect(database_file,
                                   detect_types=sqlite3.PARSE_DECLTYPES)
        self._cursor = self._db.cursor()

        self._create_table_devices()
        self._create_table_endpoints()
        self._create_table_input_clusters()
        self._create_table_output_clusters()
        self._create_table_cluster_attributes()

        self._application = application

    def execute(self, *args, **kwargs):
        return self._cursor.execute(*args, **kwargs)

    def device_joined(self, device):
        self._save_device(device)

    def device_initialized(self, device):
        self._save_device(device)

    def device_updated(self, device):
        self._save_device(device)

    def device_left(self, device):
        pass

    def device_removed(self, device):
        self._remove_device(device)

    def attribute_updated(self, cluster, attrid, value):
        self._save_attribute(
            cluster.endpoint.device.ieee,
            cluster.endpoint.endpoint_id,
            cluster.cluster_id,
            attrid,
            value,
        )

    def _create_table(self, table_name, spec):
        self.execute("CREATE TABLE IF NOT EXISTS %s %s" % (table_name, spec))

    def _create_index(self, index_name, table, columns):
        self.execute("CREATE UNIQUE INDEX IF NOT EXISTS %s ON %s(%s)" % (
            index_name, table, columns
        ))

    def _create_table_devices(self):
        self._create_table("devices", "(ieee ieee, nwk INTEGER, manufacturer INTEGER)")
        self._create_index("ieee_idx", "devices", "ieee")

    def _create_table_endpoints(self):
        self._create_table(
            "endpoints",
            "(ieee ieee, endpoint_id INTEGER, profile_id INTEGER, device_type INTEGER)",
        )
        self._create_index("endpoint_idx", "endpoints", "ieee, endpoint_id")

    def _create_table_input_clusters(self):
        self._create_table("input_clusters", "(ieee ieee, endpoint_id INTEGER, cluster INTEGER)")
        self._create_index(
            "cluster_idx",
            "input_clusters",
            "ieee, endpoint_id, cluster",
        )

    def _create_table_output_clusters(self):
        self._create_table("output_clusters", "(ieee ieee, endpoint_id INTEGER, cluster INTEGER)")
        self._create_index(
            "output_cluster_idx",
            "output_clusters",
            "ieee, endpoint_id, cluster",
        )

    def _create_table_cluster_attributes(self):
        self._create_table(
            "cluster_attributes",
            "(ieee ieee, endpoint_id, cluster INTEGER, attrid INTEGER, value TEXT)",
        )
        self._create_index(
            "attribute_idx",
            "cluster_attributes",
            "ieee, endpoint_id, cluster, attrid"
        )

    def _remove_device(self, device):
        self.execute("DELETE FROM cluster_attributes WHERE ieee = ?", (device.ieee, ))
        self.execute("DELETE FROM input_clusters WHERE ieee = ?", (device.ieee, ))
        self.execute("DELETE FROM output_clusters WHERE ieee = ?", (device.ieee, ))
        self.execute("DELETE FROM endpoints WHERE ieee = ?", (device.ieee, ))
        self.execute("DELETE FROM devices WHERE ieee = ?", (device.ieee, ))
        self._db.commit()

    def _save_device(self, device):
        if device.status != bellows.zigbee.device.Status.INITIALIZED:
            return
        q = "INSERT OR REPLACE INTO devices (ieee, nwk, manufacturer) VALUES (?, ?, ?)"
        self.execute(q, (device.ieee, device.nwk, device.manufacturer_code))
        self._save_endpoints(device)
        for epid, ep in device.endpoints.items():
            if epid == 0:
                # ZDO
                continue
            self._save_input_clusters(ep)
            self._save_output_clusters(ep)
        self._db.commit()

    def _save_endpoints(self, device):
        self.execute("DELETE FROM endpoints WHERE ieee = ?", (device.ieee, ))
        q = "INSERT OR REPLACE INTO endpoints VALUES (?, ?, ?, ?)"
        endpoints = []
        for epid, ep in device.endpoints.items():
            # Skip zdo
            if epid == 0 or ep.status != bellows.zigbee.endpoint.Status.INITIALIZED:
                continue
            device_type = getattr(ep, 'device_type', None)
            eprow = (
                device.ieee,
                ep.endpoint_id,
                getattr(ep, 'profile_id', None),
                device_type,
            )
            endpoints.append(eprow)
        self._cursor.executemany(q, endpoints)
        self._db.commit()

    def _save_input_clusters(self, endpoint):
        self.execute("DELETE FROM input_clusters WHERE ieee = ?", (endpoint.device.ieee, ))
        q = "INSERT OR REPLACE INTO input_clusters VALUES (?, ?, ?)"
        clusters = [
            (endpoint.device.ieee, endpoint.endpoint_id, cluster.cluster_id)
            for cluster in endpoint.in_clusters.values()
        ]
        self._cursor.executemany(q, clusters)
        self._db.commit()

    def _save_output_clusters(self, endpoint):
        self.execute("DELETE FROM output_clusters WHERE ieee = ?", (endpoint.device.ieee, ))
        q = "INSERT OR REPLACE INTO output_clusters VALUES (?, ?, ?)"
        clusters = [
            (endpoint.device.ieee, endpoint.endpoint_id, cluster.cluster_id)
            for cluster in endpoint.out_clusters.values()
        ]
        self._cursor.executemany(q, clusters)
        self._db.commit()

    def _save_attribute(self, ieee, endpoint_id, cluster_id, attrid, value):
        q = "INSERT OR REPLACE INTO cluster_attributes VALUES (?, ?, ?, ?, ?)"
        self.execute(q, (ieee, endpoint_id, cluster_id, attrid, value))
        self._db.commit()

    def _scan(self, table):
        return self.execute("SELECT * FROM %s" % (table, ))

    def load(self):
        LOGGER.debug("Loading application state from %s", self._database_file)
        for (ieee, nwk, manufacturer) in self._scan("devices"):
            dev = self._application.add_device(ieee, nwk, manufacturer)
            dev.status = bellows.zigbee.device.Status.INITIALIZED

        for (ieee, epid, profile_id, device_type) in self._scan("endpoints"):
            dev = self._application.get_device(ieee)
            ep = dev.add_endpoint(epid)
            ep.profile_id = profile_id
            try:
                device_type = bellows.zigbee.profiles.PROFILES[profile_id].DeviceType(device_type)
            except:
                pass
            ep.device_type = device_type
            ep.status = bellows.zigbee.endpoint.Status.INITIALIZED

        for (ieee, endpoint_id, cluster) in self._scan("input_clusters"):
            dev = self._application.get_device(ieee)
            ep = dev.endpoints[endpoint_id]
            ep.add_input_cluster(cluster)

        for (ieee, endpoint_id, cluster) in self._scan("output_clusters"):
            dev = self._application.get_device(ieee)
            ep = dev.endpoints[endpoint_id]
            ep.add_output_cluster(cluster)

        for (ieee, endpoint_id, cluster, attrid, value) in self._scan("cluster_attributes"):
            dev = self._application.get_device(ieee)
            ep = dev.endpoints[endpoint_id]
            clus = ep.in_clusters[cluster]
            clus._attr_cache[attrid] = value


class ClusterPersistingListener:
    def __init__(self, applistener, cluster):
        self._applistener = applistener
        self._cluster = cluster

    def attribute_updated(self, attrid, value):
        self._applistener.attribute_updated(self._cluster, attrid, value)

    def cluster_command(self, *args, **kwargs):
        pass

    def zdo_command(self, *args, **kwargs):
        pass
