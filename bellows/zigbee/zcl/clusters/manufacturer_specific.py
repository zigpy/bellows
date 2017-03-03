from bellows.zigbee.zcl import Cluster


class ManufacturerSpecificCluster(Cluster):
    cluster_id = 0xffff
    ep_attribute = 'manufacturer_specific'
    attributes = {}
    server_commands = {}
    client_commands = {}
