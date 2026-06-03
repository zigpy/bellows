import bellows.types as t

from ..v17.commands import COMMANDS as COMMANDS_v17

COMMANDS = {
    **COMMANDS_v17,
    "macFilterMatchMessageHandler": (
        0x46,
        {},
        {
            "filterValueMatch": t.uint16_t,  # Was `filterIndexMatch: uint8_t`
            "legacyPassthroughType": t.EmberMacPassthroughType,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "messageContents": t.LVBytes,
        },
    ),
    # Added in Simplicity SDK 2025.12.0
    "setPendingNetworkUpdateChannel": (
        0x003D,
        {
            "channel": t.uint8_t,
        },
        {},
    ),
    # NOTE: `radioSetSchedulerPriorities` (0x012B) was removed from NCP firmware in
    # Simplicity SDK 2025.12.2 without an EZSP version bump: firmware built from
    # SiSDK 2025.6.x (also EZSP v18) still implements it.
    # Dynamic Hardware Configuration, added in Simplicity SDK 2025.12.2
    "readPaDescriptor": (
        0x0152,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "descriptor": t.SlZigbeeDhcPaDescriptor,
        },
    ),
    "writePaDescriptor": (
        0x0153,
        {
            "index": t.uint8_t,
            "descriptor": t.SlZigbeeDhcPaDescriptor,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readPaCurveSegment": (
        0x0154,
        {
            "index": t.uint8_t,
            "segment_index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "segment": t.SlZigbeeDhcPaCurveSegment,
        },
    ),
    "writePaCurveSegment": (
        0x0155,
        {
            "index": t.uint8_t,
            "segment_index": t.uint8_t,
            "segment": t.SlZigbeeDhcPaCurveSegment,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readPaCurve": (
        0x0156,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "curve": t.SlZigbeeDhcPaCurve,
        },
    ),
    "writePaCurve": (
        0x0157,
        {
            "index": t.uint8_t,
            "curve": t.SlZigbeeDhcPaCurve,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readPaTable": (
        0x0158,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "table": t.SlZigbeeDhcPaTable,
        },
    ),
    "writePaTable": (
        0x0159,
        {
            "index": t.uint8_t,
            "table": t.SlZigbeeDhcPaTable,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readRssiOffset": (
        0x015A,
        {},
        {
            "status": t.sl_Status,
            "rssi_offset": t.int8s,
        },
    ),
    "readPaVoltage": (
        0x015B,
        {},
        {
            "status": t.sl_Status,
            "pa_voltage": t.uint16_t,
        },
    ),
    "writePaVoltage": (
        0x015C,
        {
            "pa_voltage": t.uint16_t,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readPaMode": (
        0x015D,
        {},
        {
            "status": t.sl_Status,
            "pa_mode": t.uint8_t,
        },
    ),
    "writePaMode": (
        0x015E,
        {
            "pa_mode": t.uint8_t,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "writeRssiOffset": (
        0x015F,
        {
            "rssi_offset": t.int8s,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readCtune": (
        0x0160,
        {},
        {
            "status": t.sl_Status,
            "ctune": t.uint32_t,
        },
    ),
    "writeCtune": (
        0x0161,
        {
            "ctune": t.uint32_t,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readDhcVersion": (
        0x0162,
        {},
        {
            "status": t.sl_Status,
            "dhc_version": t.uint8_t,
        },
    ),
    "writeDhcVersion": (
        0x0163,
        {
            "dhc_version": t.uint8_t,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readPaVersion": (
        0x0164,
        {},
        {
            "status": t.sl_Status,
            "pa_version": t.uint8_t,
        },
    ),
    "readPaSignature": (
        0x0166,
        {},
        {
            "status": t.sl_Status,
            "pa_signature": t.uint32_t,
        },
    ),
    "writePaSignature": (
        0x0167,
        {
            "pa_signature": t.uint32_t,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "readPaMetadata": (
        0x0168,
        {},
        {
            "status": t.sl_Status,
            "metadata": t.SlZigbeeDhcPaMetadata,
        },
    ),
    "writePaMetadata": (
        0x0169,
        {
            "metadata": t.SlZigbeeDhcPaMetadata,
        },
        {
            "status": t.sl_Status,
        },
    ),
}
