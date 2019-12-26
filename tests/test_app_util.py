import bellows.zigbee.util
import pytest
import voluptuous as vol


@pytest.mark.parametrize(
    "value, result",
    [
        (False, False),
        (True, True),
        ("1", True),
        ("yes", True),
        ("YeS", True),
        ("on", True),
        ("oN", True),
        ("enable", True),
        ("enablE", True),
        (0, False),
        ("no", False),
        ("nO", False),
        ("off", False),
        ("ofF", False),
        ("disable", False),
        ("disablE", False),
    ],
)
def test_config_validation_bool(value, result):
    """Test boolean config validation."""
    assert bellows.zigbee.util.cv_boolean(value) is result


@pytest.mark.parametrize("value", ["invalid", "not a bool", "something"])
def test_config_validation_bool_invalid(value):
    """Test boolean config validation."""
    with pytest.raises(vol.Invalid):
        bellows.zigbee.util.cv_boolean(value)
