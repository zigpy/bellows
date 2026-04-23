import bellows.types as t

from ..v12.commands import COMMANDS as COMMANDS_v12

COMMANDS = {
    **COMMANDS_v12,
    "getNetworkKeyInfo": (
        0x0116,
        {},
        {
            "status": t.sl_Status,
            "network_key_info": t.SecurityManagerNetworkKeyInfo,
        },
    ),
    "gpSecurityTestVectors": (
        0x0117,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "tokenFactoryReset": (
        0x0077,
        {
            "excludeOutgoingFC": t.Bool,
            "excludeBootCounter": t.Bool,
        },
        {},
    ),
    "gpSinkTableGetNumberOfActiveEntries": (
        0x0118,
        {},
        {
            "number_of_entries": t.uint8_t,
        },
    ),
    # The following commands are redefined because `SecurityManagerContext` changed
    "exportKey": (
        0x0114,
        {
            "context": t.SecurityManagerContextV13,
        },
        {
            "key": t.KeyData,
            "status": t.sl_Status,
        },
    ),
    "exportTransientKeyByEui": (
        0x0113,
        {
            "eui64": t.EUI64,
        },
        {
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "exportTransientKeyByIndex": (
        0x0112,
        {
            "index": t.uint8_t,
        },
        {
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "getApsKeyInfo": (
        0x010C,
        {
            "context_in": t.SecurityManagerContextV13,
        },
        {
            "eui": t.EUI64,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "importKey": (
        0x0115,
        {
            "context": t.SecurityManagerContextV13,
            "key": t.KeyData,
        },
        {
            "status": t.sl_Status,
        },
    ),
    # Redefine the Green Power incoming callback so real GPDFs from a
    # Friends of Hue class switch actually parse. The v4 schema used
    # scattered address fields (``addrType`` + ``addr:uint32`` +
    # ``applicationId`` + ``address:EUI64`` + ``endpoint``) that do not
    # match the 10-byte ``EmberGpAddress`` the NCP actually sends.
    #
    # ``status`` is kept as a plain ``uint8_t`` on purpose. The strict
    # ``sl_GpStatus`` enum only accepts 0x00..0x07, but firmware versions
    # shipped with current ZBT-1 / SkyConnect sticks return higher status
    # bytes (e.g. 0x7C observed from a Busch-Jaeger 6716 U switch) when
    # the frame was not matched against a proxy/sink table entry. Using a
    # plain ``uint8_t`` lets the frame reach the host so zigpy can decide
    # what to do with it.
    #
    # v14 and v16 inherit this override through the ``_REPLACEMENTS``
    # mechanism in ``bellows/ezsp/v14/commands.py``; v17 and later keep
    # their own schema which already uses ``EmberGpAddress``.
    "gpepIncomingMessageHandler": (
        0x00C5,
        {},
        {
            "status": t.uint8_t,
            "gpdLink": t.uint8_t,
            "sequenceNumber": t.uint8_t,
            "addr": t.EmberGpAddress,
            "gpdfSecurityLevel": t.EmberGpSecurityLevel,
            "gpdfSecurityKeyType": t.EmberGpKeyType,
            "autoCommissioning": t.Bool,
            "bidirectionalInfo": t.uint8_t,
            "gpdSecurityFrameCounter": t.uint32_t,
            "gpdCommandId": t.uint8_t,
            "mic": t.uint32_t,
            "proxyTableIndex": t.uint8_t,
            "gpdCommandPayload": t.LVBytes,
        },
    ),
}

del COMMANDS["becomeTrustCenter"]  # this one was likely removed earlier
del COMMANDS["getKey"]
del COMMANDS["getKeyTableEntry"]
del COMMANDS["setKeyTableEntry"]
del COMMANDS["addOrUpdateKeyTableEntry"]
del COMMANDS["addTransientLinkKey"]
del COMMANDS["getTransientLinkKey"]
del COMMANDS["getTransientKeyTableEntry"]
del COMMANDS["setSecurityKey"]
del COMMANDS["setSecurityParameters"]
del COMMANDS["resetToFactoryDefaults"]
del COMMANDS["getSecurityKeyStatus"]
