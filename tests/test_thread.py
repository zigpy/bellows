import asyncio
from asyncio import timeout as asyncio_timeout
import threading
from unittest import mock

import pytest

import bellows.thread
from bellows.thread import EventLoopThread


def bellows_threads():
    return [t for t in threading.enumerate() if "bellows" in t.name]


@pytest.fixture
async def thread():
    thread = EventLoopThread()
    await thread.start()
    yield thread
    thread.stop()
    async with asyncio_timeout(1):
        await thread.thread_complete
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


async def test_thread_start_stop():
    thread = EventLoopThread()
    thread_complete = await thread.start()
    assert thread.loop is not None
    assert len(bellows_threads()) == 1

    assert thread.stop() is thread_complete
    async with asyncio_timeout(1):
        await thread_complete

    assert thread.loop is None
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


async def test_thread_start_cancelled():
    thread = EventLoopThread()
    task = asyncio.create_task(thread.start())
    await asyncio.sleep(0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert thread.loop is None
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


async def test_thread_clears_loop_before_closing(monkeypatch):
    """`self.loop` is cleared before the loop is closed, so it never names a closed loop."""
    thread = EventLoopThread()
    real_new_event_loop = asyncio.new_event_loop
    loop_at_close = mock.sentinel.close_not_called

    def new_event_loop():
        loop = real_new_event_loop()
        real_close = loop.close

        def close():
            nonlocal loop_at_close
            loop_at_close = thread.loop
            real_close()

        loop.close = close
        return loop

    monkeypatch.setattr(asyncio, "new_event_loop", new_event_loop)

    thread_complete = await thread.start()
    thread.stop()
    async with asyncio_timeout(1):
        await thread_complete

    assert loop_at_close is None
    assert thread.loop is None

    [t.join(1) for t in bellows_threads()]


async def test_thread_loop(thread):
    async def test_coroutine():
        return mock.sentinel.result

    future = asyncio.run_coroutine_threadsafe(test_coroutine(), loop=thread.loop)
    result = await asyncio.wrap_future(future, loop=asyncio.get_running_loop())
    assert result is mock.sentinel.result


async def test_thread_run_coroutine_threadsafe(thread):
    inner_loop = None

    async def test_coroutine():
        nonlocal inner_loop
        inner_loop = asyncio.get_running_loop()
        return mock.sentinel.result

    result = await thread.run_coroutine_threadsafe(test_coroutine())
    assert result is mock.sentinel.result
    assert inner_loop is thread.loop


async def test_thread_stop_lets_tasks_finish(thread):
    """Tasks still running when the loop is stopped get to finish before it closes."""

    async def finishes_later():
        await asyncio.sleep(0.1)
        return mock.sentinel.result

    future = thread.run_coroutine_threadsafe(finishes_later())
    thread.stop()

    async with asyncio_timeout(1):
        assert await future is mock.sentinel.result
        await thread.thread_complete


async def test_thread_stop_cancels_stuck_tasks(thread, monkeypatch, caplog):
    monkeypatch.setattr(bellows.thread, "SHUTDOWN_TIMEOUT", 0.1)

    async def wait_forever():
        await asyncio.get_running_loop().create_future()

    future = thread.run_coroutine_threadsafe(wait_forever())
    thread.stop()

    with pytest.raises(asyncio.CancelledError):
        async with asyncio_timeout(1):
            await future

    async with asyncio_timeout(1):
        await thread.thread_complete

    assert "did not finish during shutdown" in caplog.text
