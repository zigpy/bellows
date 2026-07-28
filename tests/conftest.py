"""Common pytest fixtures for all tests."""

import logging

import pytest


class FailOnBadFormattingHandler(logging.Handler):
    def emit(self, record):
        try:
            record.msg % record.args
        except Exception as e:  # noqa: BLE001
            pytest.fail(
                f"Failed to format log message {record.msg!r} with {record.args!r}: {e}"
            )


@pytest.fixture(autouse=True)
def raise_on_bad_log_formatting():
    handler = FailOnBadFormattingHandler()

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    try:
        yield
    finally:
        root.removeHandler(handler)
