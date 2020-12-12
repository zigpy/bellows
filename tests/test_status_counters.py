"""Test unit for app status and counters."""

import pytest

import bellows.zigbee.status as app_state


def test_counter():
    """Test basic counter."""

    counter = app_state.Counter("mock_counter")
    assert counter.value == 0

    counter = app_state.Counter("mock_counter", 5)
    assert counter.value == 5
    assert counter.reset_count == 0

    counter.update(5)
    assert counter.value == 5
    assert counter.reset_count == 0

    counter.update(8)
    assert counter.value == 8
    assert counter.reset_count == 0

    counter.update(9)
    assert counter.value == 9
    assert counter.reset_count == 0

    counter.reset()
    assert counter.value == 9
    assert counter._raw_value == 0
    assert counter.reset_count == 1

    # new value after a counter was reset/clear
    counter.update(12)
    assert counter.value == 21
    assert counter.reset_count == 1

    counter.update(15)
    assert counter.value == 24
    assert counter.reset_count == 1

    # new counter value is less than previously reported.
    # assume counter was reset
    counter.update(14)
    assert counter.value == 24 + 14
    assert counter.reset_count == 2

    counter.reset_and_update(14)
    assert counter.value == 38 + 14
    assert counter.reset_count == 3


def test_counter_str():
    """Test counter str representation."""

    counter = app_state.Counter("some_counter", 8)
    assert str(counter) == "some_counter = 8"


def test_counters_init():
    """Test counters initialization."""

    counters = app_state.Counters(("counter_1", "counter_2", "some random name"))

    assert counters.list
    assert len(counters.list) == 3

    cnt_1, cnt_2, cnt_3 = counters.list
    assert cnt_1.name == "counter_1"
    assert cnt_2.name == "counter_2"
    assert cnt_3.name == "some random name"

    assert cnt_1.value == 0
    assert cnt_2.value == 0
    assert cnt_3.value == 0

    with pytest.raises(KeyError):
        counters["no such counter"]

    counters["some random name"] = 2
    assert cnt_3.value == 2
    assert counters["some random name"].value == 2
