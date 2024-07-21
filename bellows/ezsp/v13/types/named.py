from bellows.ezsp.v12.types.named import *  # noqa: F401, F403
import bellows.types as t


class SecurityManagerDerivedKeyType(t.enum16):
    """Derived keys are calculated when performing Zigbee crypto operations.
    The stack makes use of these derivations.
    """

    # Perform no derivation; use the key as is.
    NONE = 0
    # Perform the Key-Transport-Key hash.
    KEY_TRANSPORT_KEY = 1
    # Perform the Key-Load-Key hash.
    KEY_LOAD_KEY = 2
    # Perform the Verify Key hash.
    VERIFY_KEY = 3
    # Perform a simple AES hash of the key for TC backup.
    TC_SWAP_OUT_KEY = 4
    # For a TC using hashed link keys, hashed the root key against the supplied EUI in
    # context.
    TC_HASHED_LINK_KEY = 5
