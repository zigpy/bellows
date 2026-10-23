import asyncio
from concurrent.futures import ThreadPoolExecutor
import contextlib
import functools
import inspect
import logging

LOGGER = logging.getLogger(__name__)


class EventLoopThread:
    """Run a parallel event loop in a separate thread."""

    def __init__(self):
        self.loop = None
        self.thread_complete = None
        # Published by `force_stop()` before it schedules anything. `loop.is_closed()`
        # only becomes `True` once the loop has actually been closed, so it cannot answer
        # "will this loop still run what I hand it?" during the shutdown window: between
        # `force_stop()` and `loop.close()` the loop accepts work it will never run.
        self.stopping = False

    def run_coroutine_threadsafe(self, coroutine):
        current_loop = asyncio.get_event_loop()
        # Snapshot: the worker thread publishes `None` when it exits
        loop = self.loop
        if loop is None or self.stopping:
            coroutine.close()
            raise RuntimeError("Event loop is not running")
        try:
            future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        except RuntimeError:
            # The worker thread may close the loop after our None check
            coroutine.close()
            raise
        return asyncio.wrap_future(future, loop=current_loop)

    def _thread_main(self, init_task):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(init_task)
            self.loop.run_forever()
        finally:
            # Publish `None` before closing: `self.loop` then never names a closed loop, and
            # this thread no longer writes `self.loop` after a concurrent `start()` may have
            # replaced it.
            loop, self.loop = self.loop, None
            loop.close()

    async def start(self):
        current_loop = asyncio.get_event_loop()
        if self.loop is not None and not self.loop.is_closed():
            # Note this returns a thread that is still stopping, if one is: reusing a loop
            # that is winding down is not safe, and spawning a second thread while the
            # first is in its `finally` would have it close the new loop out from under us
            return

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=__name__)

        thread_started_future = current_loop.create_future()

        async def init_task():
            current_loop.call_soon_threadsafe(thread_started_future.set_result, None)

        self.stopping = False

        # Use current loop so current loop has a reference to the long-running thread
        # as one of its tasks
        thread_complete = current_loop.run_in_executor(
            executor, self._thread_main, init_task()
        )
        self.thread_complete = thread_complete
        current_loop.call_soon(executor.shutdown, False)
        await thread_started_future
        return thread_complete

    def force_stop(self):
        # Published before anything is scheduled below: from here on the loop may stop at
        # any moment, so work handed to it may never run.
        self.stopping = True

        loop = self.loop
        if loop is None or loop.is_closed():
            return

        def cancel_tasks_and_stop_loop():
            tasks = asyncio.all_tasks(loop=loop)

            for task in tasks:
                loop.call_soon_threadsafe(task.cancel)

            gather = asyncio.gather(*tasks, return_exceptions=True)
            gather.add_done_callback(lambda _: loop.call_soon_threadsafe(loop.stop))

        # The worker thread may close the loop after our is_closed() check.
        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(cancel_tasks_and_stop_loop)


class ThreadsafeProxy:
    """Proxy class which enforces threadsafe non-blocking calls
    This class can be used to wrap an object to ensure any calls
    using that object's methods are done on a particular event loop
    """

    def __init__(self, obj, obj_loop, loop_thread=None):
        self._obj = obj
        self._obj_loop = obj_loop
        # The `EventLoopThread` running `obj_loop`, when there is one. Only it knows that a
        # stop has been requested; the loop object itself still looks perfectly usable.
        self._loop_thread = loop_thread

    def __getattr__(self, name):
        func = getattr(self._obj, name)
        if not callable(func):
            raise TypeError(
                "Can only use ThreadsafeProxy with callable attributes: {}.{}".format(
                    self._obj.__class__.__name__, name
                )
            )

        def func_wrapper(*args, **kwargs):
            loop = self._obj_loop
            curr_loop = asyncio.get_running_loop()
            call = functools.partial(func, *args, **kwargs)
            if loop == curr_loop:
                return call()

            def disconnected_result(message="Attempted to use a closed event loop"):
                # Disconnected: sync calls are dropped, async calls resolve to None
                LOGGER.warning(message)
                if not inspect.iscoroutinefunction(func):
                    return None
                future = curr_loop.create_future()
                future.set_result(None)
                return future

            if loop.is_closed():
                return disconnected_result()
            if self._loop_thread is not None and self._loop_thread.stopping:
                # The loop is still open, but it has been asked to stop: anything handed
                # to it from here on may never run, and `run_coroutine_threadsafe()` will
                # not complain. Without this branch the caller waits on a future that is
                # never resolved -- a silent, unbounded hang.
                return disconnected_result(
                    "Attempted to use an event loop that is shutting down"
                )
            if inspect.iscoroutinefunction(func):
                coro = call()
                try:
                    future = asyncio.run_coroutine_threadsafe(coro, loop)
                except RuntimeError:
                    # The worker thread may close the loop after our is_closed() check
                    coro.close()
                    return disconnected_result()
                return asyncio.wrap_future(future, loop=curr_loop)
            else:

                def check_result_wrapper():
                    result = call()
                    if result is not None:
                        raise TypeError(
                            (
                                "ThreadsafeProxy can only wrap functions with no return"
                                "value \nUse an async method to return values: {}.{}"
                            ).format(self._obj.__class__.__name__, name)
                        )

                try:
                    loop.call_soon_threadsafe(check_result_wrapper)
                except RuntimeError:
                    # The worker thread may close the loop after our is_closed() check
                    return disconnected_result()

        return func_wrapper
