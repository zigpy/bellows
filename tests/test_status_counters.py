"""Test unit for app status and counters."""

import bellows.zigbee.status as app_state


def test_counter():
    """Test basic counter."""

    counter = app_state.Counter("mock_counter")
    assert counter.value == 0

    counter = app_state.Counter("mock_counter", 5)
    assert counter.value == 5
    assert counter.clears == 0

    counter.update(5)
    assert counter.value == 5
    assert counter.clears == 0

    counter.update(8)
    assert counter.value == 8
    assert counter.clears == 0

    counter.update(9)
    assert counter.value == 9
    assert counter.clears == 0

    counter.clear()
    assert counter.value == 9
    assert counter._raw_value == 0
    assert counter.clears == 1

    # new value after a counter was reset/clear
    counter.update(12)
    assert counter.value == 21
    assert counter.clears == 1

    counter.update(15)
    assert counter.value == 24
    assert counter.clears == 1

    # new counter value is less than previously reported.
    # assume counter was reset
    counter.update(14)
    assert counter.value == 24 + 14
    assert counter.clears == 2

    counter.clear_and_update(14)
    assert counter.value == 38 + 14
    assert counter.clears == 3
