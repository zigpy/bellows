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
    thread = EventLoopThread(asyncio.sleep(0))
    await thread.start()
    yield thread
    thread.stop()
    async with asyncio_timeout(1):
        await thread.thread_complete
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


async def test_thread_start_stop():
    thread = EventLoopThread(asyncio.sleep(0))
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
    thread = EventLoopThread(asyncio.sleep(0))
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
    thread = EventLoopThread(asyncio.sleep(0))
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


async def test_thread_main_cancelled_on_stop():
    """`stop()` cancels `main`, and the thread waits for its cleanup before exiting."""
    main_loop = None
    cleaned_up = threading.Event()

    async def main():
        nonlocal main_loop
        main_loop = asyncio.get_running_loop()

        try:
            await asyncio.get_running_loop().create_future()
        finally:
            await asyncio.sleep(0.05)
            cleaned_up.set()

    thread = EventLoopThread(main())
    await thread.start()
    worker_loop = thread.loop

    await asyncio.sleep(0.05)
    assert not cleaned_up.is_set()

    thread.stop()
    async with asyncio_timeout(1):
        await thread.thread_complete

    assert cleaned_up.is_set()
    assert main_loop is worker_loop
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


async def test_thread_main_failure():
    """A `main` that fails on its own fails the thread, once it is stopped."""

    async def main():
        raise RuntimeError("main failed")

    thread = EventLoopThread(main())
    await thread.start()

    # The loop keeps running for other calls until it is told to stop
    await asyncio.sleep(0.05)
    assert thread.loop is not None

    thread.stop()

    with pytest.raises(RuntimeError, match="main failed"):
        async with asyncio_timeout(1):
            await thread.thread_complete

    assert thread.loop is None
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


async def test_thread_main_stuck_cleanup(monkeypatch, caplog):
    monkeypatch.setattr(bellows.thread, "SHUTDOWN_TIMEOUT", 0.1)

    async def main():
        try:
            await asyncio.get_running_loop().create_future()
        finally:
            await asyncio.get_running_loop().create_future()

    thread = EventLoopThread(main())
    await thread.start()
    thread.stop()

    async with asyncio_timeout(1):
        await thread.thread_complete

    assert "did not finish during shutdown" in caplog.text
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []
