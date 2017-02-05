import bellows.zigbee.zdo as zdo


def test_commands():
    for cmdid, cmdspec in zdo.types.CLUSTERS.items():
        assert 0 <= cmdid <= 0xffff
        assert isinstance(cmdspec, tuple)
        assert isinstance(cmdspec[0], str)
        for paramname, paramtype in zip(cmdspec[1], cmdspec[2]):
            assert isinstance(paramname, str)
            assert hasattr(paramtype, 'serialize')
            assert hasattr(paramtype, 'deserialize')
