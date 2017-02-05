from bellows.zigbee.zcl import Cluster


class LightLink(Cluster):
    cluster_id = 0x1000
    attributes = {}
    server_commands = {}
    client_commands = {}
