from asynctest import mock
import bellows.ezsp.v7
import pytest


@pytest.fixture
def ezsp_f():
    """EZSP v7 protocol handler."""
    return bellows.ezsp.v7.EZSPv7(mock.MagicMock(), mock.MagicMock())


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 7)
    assert data == b"\x22\x00\xff\x00\x00\x07"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x00\xff\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


def test_command_frames(ezsp_f):
    """Test alphabetical list of frames matches the commands."""
    assert set(ezsp_f.COMMANDS) == set(command_frames)
    for name, frame_id in command_frames.items():
        assert ezsp_f.COMMANDS[name][0] == frame_id
        assert ezsp_f.COMMANDS_BY_ID[frame_id][0] == name


command_frames = {
    "addEndpoint": 0x02,
    "addOrUpdateKeyTableEntry": 0x66,
    "addTransientLinkKey": 0xAF,
    "addressTableEntryIsActive": 0x5B,
    "aesEncrypt": 0x94,
    "aesMmoHash": 0x6F,
    "becomeTrustCenter": 0x77,
    "bindingIsActive": 0x2E,
    "bootloadTransmitCompleteHandler": 0x93,
    "broadcastNetworkKeySwitch": 0x74,
    "broadcastNextNetworkKey": 0x73,
    "calculateSmacs": 0x9F,
    "calculateSmacs283k1": 0xEA,
    "calculateSmacsHandler": 0xA0,
    "calculateSmacsHandler283k1": 0xEB,
    "callback": 0x06,
    "changeSourceRouteHandler": 0xC4,
    "childJoinHandler": 0x23,
    "clearBindingTable": 0x2A,
    "clearKeyTable": 0xB1,
    "clearStoredBeacons": 0x3C,
    "clearTemporaryDataMaybeStoreLinkKey": 0xA1,
    "clearTemporaryDataMaybeStoreLinkKey283k1": 0xEE,
    "clearTransientLinkKeys": 0x6B,
    "counterRolloverHandler": 0xF2,
    "customFrame": 0x47,
    "customFrameHandler": 0x54,
    "dGpSend": 0xC6,
    "dGpSentHandler": 0xC7,
    "debugWrite": 0x12,
    "delayTest": 0x9D,
    "deleteBinding": 0x2D,
    "dsaSign": 0xA6,
    "dsaSignHandler": 0xA7,
    "dsaVerify": 0xA3,
    "dsaVerify283k1": 0xB0,
    "dsaVerifyHandler": 0x78,
    "dutyCycleHandler": 0x4D,
    "echo": 0x81,
    "energyScanRequest": 0x9C,
    "energyScanResultHandler": 0x48,
    "eraseKeyTableEntry": 0x76,
    "findAndRejoinNetwork": 0x21,
    "findKeyTableEntry": 0x75,
    "findUnusedPanId": 0xD3,
    "formNetwork": 0x1E,
    "generateCbkeKeys": 0xA4,
    "generateCbkeKeys283k1": 0xE8,
    "generateCbkeKeysHandler": 0x9E,
    "generateCbkeKeysHandler283k1": 0xE9,
    "getAddressTableRemoteEui64": 0x5E,
    "getAddressTableRemoteNodeId": 0x5F,
    "getBinding": 0x2C,
    "getBeaconClassificationParams": 0xF3,
    "getBindingRemoteNodeId": 0x2F,
    "getCertificate": 0xA5,
    "getCertificate283k1": 0xEC,
    "getChildData": 0x4A,
    "getConfigurationValue": 0x52,
    "getCtune": 0xF6,
    "getCurrentDutyCycle": 0x4C,
    "getCurrentSecurityState": 0x69,
    "getEui64": 0x26,
    "getDutyCycleLimits": 0x4B,
    "getDutyCycleState": 0x35,
    "getExtendedTimeout": 0x7F,
    "getExtendedValue": 0x03,
    "getFirstBeacon": 0x3D,
    "getKey": 0x6A,
    "getKeyTableEntry": 0x71,
    "getLibraryStatus": 0x01,
    "getLogicalChannel": 0xBA,
    "getMfgToken": 0x0B,
    "getMulticastTableEntry": 0x63,
    "getNeighbor": 0x79,
    "getNetworkParameters": 0x28,
    "getNextBeacon": 0x04,
    "getNodeId": 0x27,
    "getNumStoredBeacons": 0x08,
    "getParentChildParameters": 0x29,
    "getParentClassificationEnabled": 0xF0,
    "getPhyInterfaceCount": 0xFC,
    "getPolicy": 0x56,
    "getRadioParameters": 0xFD,
    "getRandomNumber": 0x49,
    "getRouteTableEntry": 0x7B,
    "getRoutingShortcutThreshold": 0xD1,
    "getSecurityKeyStatus": 0xCD,
    "getSourceRouteTableEntry": 0xC1,
    "getSourceRouteTableFilledSize": 0xC2,
    "getSourceRouteTableTotalSize": 0xC3,
    "getStandaloneBootloaderVersionPlatMicroPhy": 0x91,
    "getTimer": 0x4E,
    "getToken": 0x0A,
    "getTransientKeyTableEntry": 0x6D,
    "getTransientLinkKey": 0xCE,
    "getTrueRandomEntropySource": 0x4F,
    "getValue": 0xAA,
    "getXncpInfo": 0x13,
    "getZllPrimaryChannelMask": 0xD9,
    "getZllSecondaryChannelMask": 0xDA,
    "gpProxyTableGetEntry": 0xC8,
    "gpProxyTableLookup": 0xC0,
    "gpProxyTableProcessGpPairing": 0xC9,
    "gpSinkTableClearAll": 0xE2,
    "gpSinkTableFindOrAllocateEntry": 0xE1,
    "gpSinkTableGetEntry": 0xDD,
    "gpSinkTableInit": 0x70,
    "gpSinkTableLookup": 0xDE,
    "gpSinkTableRemoveEntry": 0xE0,
    "gpSinkTableSetEntry": 0xDF,
    "gpepIncomingMessageHandler": 0xC5,
    "idConflictHandler": 0x7C,
    "incomingBootloadMessageHandler": 0x92,
    "incomingManyToOneRouteRequestHandler": 0x7D,
    "incomingMessageHandler": 0x45,
    "incomingRouteErrorHandler": 0x80,
    "incomingRouteRecordHandler": 0x59,
    "incomingSenderEui64Handler": 0x62,
    "invalidCommand": 0x58,
    "isHubConnected": 0xE6,
    "isUpTimeLong": 0xE5,
    "isZllNetwork": 0xBE,
    "joinNetwork": 0x1F,
    "joinNetworkDirectly": 0x3B,
    "launchStandaloneBootloader": 0x8F,
    "leaveNetwork": 0x20,
    "lookupEui64ByNodeId": 0x61,
    "lookupNodeIdByEui64": 0x60,
    "macFilterMatchMessageHandler": 0x46,
    "macPassthroughMessageHandler": 0x97,
    "maximumPayloadLength": 0x33,
    "messageSentHandler": 0x3F,
    "mfglibEnd": 0x84,
    "mfglibGetChannel": 0x8B,
    "mfglibGetPower": 0x8D,
    "mfglibRxHandler": 0x8E,
    "mfglibSendPacket": 0x89,
    "mfglibSetChannel": 0x8A,
    "mfglibSetPower": 0x8C,
    "mfglibStart": 0x83,
    "mfglibStartStream": 0x87,
    "mfglibStartTone": 0x85,
    "mfglibStopStream": 0x88,
    "mfglibStopTone": 0x86,
    "multiPhySetRadioChannel": 0xFB,
    "multiPhySetRadioPower": 0xFA,
    "multiPhyStart": 0xF8,
    "multiPhyStop": 0xF9,
    "neighborCount": 0x7A,
    "networkFoundHandler": 0x1B,
    "networkInit": 0x17,
    "networkState": 0x18,
    "noCallbacks": 0x07,
    "nop": 0x05,
    "overrideCurrentChannel": 0x95,
    "permitJoining": 0x22,
    "pollCompleteHandler": 0x43,
    "pollForData": 0x42,
    "pollHandler": 0x44,
    "proxyBroadcast": 0x37,
    "rawTransmitCompleteHandler": 0x98,
    "readAndClearCounters": 0x65,
    "readCounters": 0xF1,
    "remoteDeleteBindingHandler": 0x32,
    "remoteSetBindingHandler": 0x31,
    "removeDevice": 0xA8,
    "replaceAddressTableEntry": 0x82,
    "requestLinkKey": 0x14,
    "resetToFactoryDefaults": 0xCC,
    "scanCompleteHandler": 0x1C,
    "sendBootloadMessage": 0x90,
    "sendBroadcast": 0x36,
    "sendLinkPowerDeltaRequest": 0xF7,
    "sendManyToOneRouteRequest": 0x41,
    "sendMulticast": 0x38,
    "sendMulticastWithAlias": 0x3A,
    "sendPanIdUpdate": 0x57,
    "sendRawMessage": 0x96,
    "sendReply": 0x39,
    "sendTrustCenterLinkKey": 0x67,
    "sendUnicast": 0x34,
    "setAddressTableRemoteEui64": 0x5C,
    "setAddressTableRemoteNodeId": 0x5D,
    "setBeaconClassificationParams": 0xEF,
    "setBinding": 0x2B,
    "setBindingRemoteNodeId": 0x30,
    "setBrokenRouteErrorCode": 0x11,
    "setConcentrator": 0x10,
    "setConfigurationValue": 0x53,
    "setCtune": 0xF5,
    "setDutyCycleLimitsInStack": 0x40,
    "setExtendedTimeout": 0x7E,
    "setGpioCurrentConfiguration": 0xAC,
    "setGpioPowerUpDownConfiguration": 0xAD,
    "setGpioRadioPowerMask": 0xAE,
    "setHubConnectivity": 0xE4,
    "setInitialSecurityState": 0x68,
    "setKeyTableEntry": 0x72,
    "setLogicalAndRadioChannel": 0xB9,
    "setLongUpTime": 0xE3,
    "setMacPollCcaWaitTime": 0xF4,
    "setManufacturerCode": 0x15,
    "setMfgToken": 0x0C,
    "setMulticastTableEntry": 0x64,
    "setParentClassificationEnabled": 0xE7,
    "setPolicy": 0x55,
    "setPowerDescriptor": 0x16,
    "setPreinstalledCbkeData": 0xA2,
    "setPreinstalledCbkeData283k1": 0xED,
    "setRadioChannel": 0x9A,
    "setRadioPower": 0x99,
    "setRoutingShortcutThreshold": 0xD0,
    "setSecurityKey": 0xCA,
    "setSecurityParameters": 0xCB,
    "setSourceRoute": 0x5A,
    "setTimer": 0x0E,
    "setToken": 0x09,
    "setValue": 0xAB,
    "setZllAdditionalState": 0xD6,
    "setZllNodeType": 0xD5,
    "setZllPrimaryChannelMask": 0xDB,
    "setZllSecondaryChannelMask": 0xDC,
    "stackStatusHandler": 0x19,
    "stackTokenChangedHandler": 0x0D,
    "startScan": 0x1A,
    "stopScan": 0x1D,
    "switchNetworkKeyHandler": 0x6E,
    "timerHandler": 0x0F,
    "trustCenterJoinHandler": 0x24,
    "unicastCurrentNetworkKey": 0x50,
    "unicastNwkKeyUpdate": 0xA9,
    "unusedPanIdFoundHandler": 0xD2,
    "updateTcLinkKey": 0x6C,
    "version": 0x00,
    "writeNodeData": 0xFE,
    "zigbeeKeyEstablishmentHandler": 0x9B,
    "zllAddressAssignmentHandler": 0xB8,
    "zllClearTokens": 0x25,
    "zllGetTokens": 0xBC,
    "zllNetworkFoundHandler": 0xB6,
    "zllNetworkOps": 0xB2,
    "zllOperationInProgress": 0xD7,
    "zllRxOnWhenIdleGetActive": 0xD8,
    "zllScanCompleteHandler": 0xB7,
    "zllSetDataToken": 0xBD,
    "zllSetInitialSecurityState": 0xB3,
    "zllSetNonZllNetwork": 0xBF,
    "zllSetRadioIdleMode": 0xD4,
    "zllSetRxOnWhenIdle": 0xB5,
    "zllSetSecurityStateWithoutKey": 0xCF,
    "zllStartScan": 0xB4,
    "zllTouchLinkTargetHandler": 0xBB,
}
