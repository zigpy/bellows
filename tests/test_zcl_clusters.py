import bellows.zigbee.zcl as zcl


def test_cluster_id():
    for cluster_id, cluster in zcl.Cluster._registry.items():
        assert 0 <= getattr(cluster, 'cluster_id', -1) <= 65535
        assert cluster_id == cluster.cluster_id


def test_attributes():
    for cluster_id, cluster in zcl.Cluster._registry.items():
        for attrid, attrspec in cluster.attributes.items():
            assert 0 <= attrid <= 0xffff
            assert isinstance(attrspec, tuple)
            assert isinstance(attrspec[0], str)
            assert hasattr(attrspec[1], 'serialize')
            assert hasattr(attrspec[1], 'deserialize')


def _test_commands(cmdattr):
    for cluster_id, cluster in zcl.Cluster._registry.items():
        print(cluster.cluster_id)
        for cmdid, cmdspec in getattr(cluster, cmdattr).items():
            assert 0 <= cmdid <= 0xff
            assert isinstance(cmdspec, tuple), "Cluster %s" % (cluster_id, )
            assert len(cmdspec) == 3
            assert isinstance(cmdspec[0], str)
            assert isinstance(cmdspec[1], tuple)
            assert isinstance(cmdspec[2], bool)
            for t in cmdspec[1]:
                assert hasattr(t, 'serialize')
                assert hasattr(t, 'deserialize')


def test_server_commands():
    _test_commands('server_commands')


def test_client_commands():
    _test_commands('client_commands')
