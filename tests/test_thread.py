import asyncio
import sys
import threading
from unittest import mock

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

import pytest

from bellows.thread import EventLoopThread, ThreadsafeProxy


async def test_thread_start(monkeypatch):
    current_loop = asyncio.get_event_loop()
    loopmock = mock.MagicMock()

    monkeypatch.setattr(asyncio, "new_event_loop", lambda: loopmock)
    monkeypatch.setattr(asyncio, "set_event_loop", lambda loop: None)

    def mockrun(task):
        future = asyncio.run_coroutine_threadsafe(task, loop=current_loop)
        return future.result(1)

    loopmock.run_until_complete.side_effect = mockrun
    thread = EventLoopThread()
    thread_complete = await thread.start()
    await thread_complete

    assert loopmock.run_until_complete.call_count == 1
    assert loopmock.run_forever.call_count == 1
    assert loopmock.close.call_count == 1


class ExceptionCollector:
    def __init__(self):
        self.exceptions = []

    def __call__(self, thread_loop, context):
        exc = context.get("exception") or Exception(context["message"])
        self.exceptions.append(exc)


@pytest.fixture
async def thread():
    thread = EventLoopThread()
    await thread.start()
    thread.loop.call_soon_threadsafe(
        thread.loop.set_exception_handler, ExceptionCollector()
    )
    yield thread
    thread.force_stop()
    if thread.thread_complete is not None:
        async with asyncio_timeout(1):
            await thread.thread_complete
    [t.join(1) for t in threading.enumerate() if "bellows" in t.name]
    threads = [t for t in threading.enumerate() if "bellows" in t.name]
    assert len(threads) == 0


async def yield_other_thread(thread):
    await thread.run_coroutine_threadsafe(asyncio.sleep(0))

    exception_collector = thread.loop.get_exception_handler()
    if exception_collector.exceptions:
        raise exception_collector.exceptions[0]


async def test_thread_loop(thread):
    async def test_coroutine():
        return mock.sentinel.result

    future = asyncio.run_coroutine_threadsafe(test_coroutine(), loop=thread.loop)
    result = await asyncio.wrap_future(future, loop=asyncio.get_event_loop())
    assert result is mock.sentinel.result


async def test_thread_double_start(thread):
    previous_loop = thread.loop
    await thread.start()
    if sys.version_info[:2] >= (3, 6):
        threads = [t for t in threading.enumerate() if "bellows" in t.name]
        assert len(threads) == 1
    assert thread.loop is previous_loop


async def test_thread_already_stopped(thread):
    thread.force_stop()
    thread.force_stop()


async def test_thread_run_coroutine_threadsafe(thread):
    inner_loop = None

    async def test_coroutine():
        nonlocal inner_loop
        inner_loop = asyncio.get_event_loop()
        return mock.sentinel.result

    result = await thread.run_coroutine_threadsafe(test_coroutine())
    assert result is mock.sentinel.result
    assert inner_loop is thread.loop


async def test_proxy_callback(thread):
    obj = mock.MagicMock()
    proxy = ThreadsafeProxy(obj, thread.loop)
    obj.test.return_value = None
    proxy.test()
    await yield_other_thread(thread)
    assert obj.test.call_count == 1


async def test_proxy_async(thread):
    obj = mock.MagicMock()
    proxy = ThreadsafeProxy(obj, thread.loop)
    call_count = 0

    async def magic():
        nonlocal thread, call_count
        assert asyncio.get_event_loop() == thread.loop
        call_count += 1
        return mock.sentinel.result

    obj.test = magic
    result = await proxy.test()

    assert call_count == 1
    assert result == mock.sentinel.result


async def test_proxy_bad_function(thread):
    obj = mock.MagicMock()
    proxy = ThreadsafeProxy(obj, thread.loop)
    obj.test.return_value = mock.sentinel.value

    with pytest.raises(TypeError):
        proxy.test()
        await yield_other_thread(thread)


async def test_proxy_not_function():
    loop = asyncio.get_event_loop()
    obj = mock.MagicMock()
    proxy = ThreadsafeProxy(obj, loop)
    obj.test = mock.sentinel.value
    with pytest.raises(TypeError):
        proxy.test


async def test_proxy_no_thread():
    loop = asyncio.get_event_loop()
    obj = mock.MagicMock()
    proxy = ThreadsafeProxy(obj, loop)
    proxy.test()
    assert obj.test.call_count == 1


async def test_proxy_loop_closed():
    loop = asyncio.new_event_loop()
    obj = mock.MagicMock()
    proxy = ThreadsafeProxy(obj, loop)
    loop.close()
    proxy.test()
    assert obj.test.call_count == 0


async def test_thread_task_cancellation_after_stop(thread):
    loop = asyncio.get_event_loop()
    obj = mock.MagicMock()

    async def wait_forever():
        return await thread.loop.create_future()

    obj.wait_forever = wait_forever

    # Stop the thread while we're waiting
    loop.call_later(0.1, thread.force_stop)

    proxy = ThreadsafeProxy(obj, thread.loop)

    # The cancellation should propagate to the outer event loop
    with pytest.raises(asyncio.CancelledError):
        # This will stall forever without the patch
        async with asyncio_timeout(1):
            await proxy.wait_forever()
