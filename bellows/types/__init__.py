from .basic import *  # noqa: F401,F403
from .named import *  # noqa: F401,F403
from .struct import *  # noqa: F401,F403


def deserialize(data, schema):
    result = []
    for type_ in schema:
        value, data = type_.deserialize(data)
        result.append(value)
    return result, data


def serialize(data, schema):
    return b"".join(t(v).serialize() for t, v in zip(schema, data))


def deserialize_dict(data, schema):
    result = {}
    for key, type_ in schema.items():
        value, data = type_.deserialize(data)
        result[key] = value
    return result, data


def serialize_dict(data, schema):
    return b"".join(t(v).serialize() for v, (n, t) in zip(data, schema.items()))
