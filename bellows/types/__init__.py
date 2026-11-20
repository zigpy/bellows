from typing import Any

from .basic import *  # noqa: F401,F403
from .named import *  # noqa: F401,F403
from .struct import *  # noqa: F401,F403


def deserialize_dict(
    data: bytes, schema: dict[str, Any]
) -> tuple[dict[str, Any], bytes]:
    result = {}
    for key, type_ in schema.items():
        value, data = type_.deserialize(data)
        result[key] = value
    return result, data


def serialize_dict(
    args: tuple[Any, ...], kwargs: dict[str, Any], schema: dict[str, Any]
) -> bytes:
    params = {
        **dict(zip(schema.keys(), args, strict=False)),
        **kwargs,
    }

    return b"".join(t(params[k]).serialize() for k, t in schema.items())
