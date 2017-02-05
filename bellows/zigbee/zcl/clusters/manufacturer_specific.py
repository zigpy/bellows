from bellows.zigbee.zcl import Cluster


class ManufacturerSpecificCluster(Cluster):
    cluster_id = 0xffff
    attributes = {}
    server_commands = {}
    client_commands = {}
