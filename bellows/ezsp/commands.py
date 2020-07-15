"""Commands module."""
import logging
from typing import Dict, Tuple

from . import v4

EZSP_VERSION_LATEST = v4.EZSP_VERSION

LOGGER = logging.getLogger(__name__)

COMMANDS = {v4.EZSP_VERSION: v4.COMMANDS}


def by_version(version: int = 4) -> Dict[str, Tuple[int, Tuple, Tuple]]:
    """Return EZSP commands for protocol version."""

    try:
        return COMMANDS[version]
    except KeyError:
        LOGGER.warning(
            "Unsupported protocol %s version. Using version %s instead",
            version,
            EZSP_VERSION_LATEST,
        )
        return COMMANDS[EZSP_VERSION_LATEST]
