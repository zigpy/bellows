"""Protocol Interfaces Functional Domain"""

import bellows.types as t
from bellows.zigbee.zcl import Cluster


class DateTime(t.EzspStruct):
    _fields = [
        ('date', t.uint32_t),
        ('time', t.uint32_t),
    ]


class GenericTunnel(Cluster):
    cluster_id = 0x0600
    attributes = {
        0x0001: ('max_income_trans_size', t.uint16_t),
        0x0002: ('max_outgo_trans_size', t.uint16_t),
        0x0003: ('protocol_addr', t.LVBytes),
    }
    server_commands = {
        0x0000: ('match_protocol_addr', (), False),
    }
    client_commands = {
        0x0000: ('match_protocol_addr_response', (), True),
        0x0001: ('advertise_protocol_address', (), False),
    }


class BacnetProtocolTunnel(Cluster):
    cluster_id = 0x0601
    attributes = {}
    server_commands = {
        0x0000: ('transfer_npdu', (), False),
    }
    client_commands = {}


class AnalogInputReg(Cluster):
    cluster_id = 0x0602
    attributes = {
        0x0016: ('cov_increment', t.Single),
        0x001f: ('device_type', t.LVBytes),
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x0076: ('update_interval', t.uint8_t),
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class AnalogInputExt(Cluster):
    cluster_id = 0x0603
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0011: ('notification_class', t.uint16_t),
        0x0019: ('deadband', t.Single),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x002d: ('high_limit', t.Single),
        0x0034: ('limit_enable', t.uint8_t),  # bitmap8
        0x003b: ('low_limit', t.Single),
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {
        0x0000: ('transfer_apdu', (), False),
        0x0001: ('connect_req', (), False),
        0x0002: ('disconnect_req', (), False),
        0x0003: ('connect_status_noti', (), False),
    }
    client_commands = {}


class AnalogOutputReg(Cluster):
    cluster_id = 0x0604
    attributes = {
        0x0016: ('cov_increment', t.Single),
        0x001f: ('device_type', t.LVBytes),
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x0076: ('update_interval', t.uint8_t),
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class AnalogOutputExt(Cluster):
    cluster_id = 0x0605
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0011: ('notification_class', t.uint16_t),
        0x0019: ('deadband', t.Single),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x002d: ('high_limit', t.Single),
        0x0034: ('limit_enable', t.uint8_t),  # bitmap8
        0x003b: ('low_limit', t.Single),
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class AnalogValueReg(Cluster):
    cluster_id = 0x0606
    attributes = {
        0x0016: ('cov_increment', t.Single),
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class AnalogValueExt(Cluster):
    cluster_id = 0x0607
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0011: ('notification_class', t.uint16_t),
        0x0019: ('deadband', t.Single),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x002d: ('high_limit', t.Single),
        0x0034: ('limit_enable', t.uint8_t),  # bitmap8
        0x003b: ('low_limit', t.Single),
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class BinaryInputReg(Cluster):
    cluster_id = 0x0608
    attributes = {
        0x000f: ('change_of_state_count', t.uint32_t),
        0x0010: ('change_of_state_time', DateTime),
        0x001f: ('device_type', t.LVBytes),
        0x0021: ('elapsed_active_time', t.uint32_t),
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x0072: ('time_of_at_reset', DateTime),
        0x0073: ('time_of_sc_reset', DateTime),
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class BinaryInputExt(Cluster):
    cluster_id = 0x0609
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0006: ('alarm_value', t.Bool),
        0x0011: ('notification_class', t.uint16_t),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class BinaryOutputReg(Cluster):
    cluster_id = 0x060a
    attributes = {
        0x000f: ('change_of_state_count', t.uint32_t),
        0x0010: ('change_of_state_time', DateTime),
        0x001f: ('device_type', t.LVBytes),
        0x0021: ('elapsed_active_time', t.uint32_t),
        0x0028: ('feed_back_value', t.uint8_t),  # enum8
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x0072: ('time_of_at_reset', DateTime),
        0x0073: ('time_of_sc_reset', DateTime),
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class BinaryOutputExt(Cluster):
    cluster_id = 0x060b
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0011: ('notification_class', t.uint16_t),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class BinaryValueReg(Cluster):
    cluster_id = 0x060c
    attributes = {
        0x000f: ('change_of_state_count', t.uint32_t),
        0x0010: ('change_of_state_time', DateTime),
        0x0021: ('elapsed_active_time', t.uint32_t),
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x0072: ('time_of_at_reset', DateTime),
        0x0073: ('time_of_sc_reset', DateTime),
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class BinaryValueExt(Cluster):
    cluster_id = 0x060d
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0006: ('alarm_value', t.Bool),
        0x0011: ('notification_class', t.uint16_t),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class MultistateInputReg(Cluster):
    cluster_id = 0x060e
    attributes = {
        0x001f: ('device_type', t.LVBytes),
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class MultistateInputExt(Cluster):
    cluster_id = 0x060f
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0006: ('alarm_value', t.uint16_t),
        0x0011: ('notification_class', t.uint16_t),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x0025: ('fault_values', t.uint16_t),
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class MultistateOutputReg(Cluster):
    cluster_id = 0x0610
    attributes = {
        0x001f: ('device_type', t.LVBytes),
        0x0028: ('feed_back_value', t.uint8_t),  # enum8
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class MultistateOutputExt(Cluster):
    cluster_id = 0x0611
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0011: ('notification_class', t.uint16_t),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class MultistateValueReg(Cluster):
    cluster_id = 0x0612
    attributes = {
        0x004b: ('object_id', t.fixed_list(4, t.uint8_t)),
        0x004d: ('object_name', t.LVBytes),
        0x004f: ('object_type', t.uint16_t),  # enum16
        0x00a8: ('profile_name', t.LVBytes),
    }
    server_commands = {}
    client_commands = {}


class MultistateValueExt(Cluster):
    cluster_id = 0x0613
    attributes = {
        0x0000: ('acked_transitions', t.uint8_t),  # bitmap8
        0x0006: ('alarm_value', t.uint16_t),
        0x0011: ('notification_class', t.uint16_t),
        0x0023: ('event_enable', t.uint8_t),  # bitmap8
        0x0024: ('event_state', t.uint8_t),  # enum8
        0x0025: ('fault_values', t.uint16_t),
        0x0048: ('notify_type', t.uint8_t),  # enum8
        0x0071: ('time_delay', t.uint8_t),
        # 0x0082: ('event_time_stamps', TODO.array),  # Array[3] of (16-bit unsigned integer, time of day, or structure of (date, time of day))
    }
    server_commands = {}
    client_commands = {}


class BACNetProtocolTunnel(Cluster):
    cluster_id = 0x0614
    attributes = {
        # 0x0000: ('deviceid_list', UNKNOWN),
        # 0x0001: ('manager_target', UNKNOWN),
        # 0x0002: ('manager_endpoint', UNKNOWN),
        # 0x0003: ('connected', UNKNOWN),
        # 0x0004: ('preemptible', UNKNOWN),
        # 0x0005: ('idle_timeout', UNKNOWN),
    }
    server_commands = {
        0x0000: ('transfer_apdu', (), False),
        0x0001: ('connect_req', (), False),
        0x0002: ('disconnect_req', (), False),
        0x0003: ('connect_status_noti', (), False),
    }
    client_commands = {}
