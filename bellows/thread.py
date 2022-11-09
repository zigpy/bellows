import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools
import logging
import sys

LOGGER = logging.getLogger(__name__)


class EventLoopThread:
    """Run a parallel event loop in a separate thread."""

    def __init__(self):
        self.loop = None
        self.thread_complete = None

    def run_coroutine_threadsafe(self, coroutine):
        current_loop = asyncio.get_event_loop()
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return asyncio.wrap_future(future, loop=current_loop)

    def _thread_main(self, init_task):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(init_task)
            self.loop.run_forever()
        finally:
            self.loop.close()
            self.loop = None

    async def start(self):
        current_loop = asyncio.get_event_loop()
        if self.loop is not None and not self.loop.is_closed():
            return

        executor_opts = {"max_workers": 1}
        if sys.version_info[:2] >= (3, 6):
            executor_opts["thread_name_prefix"] = __name__
        executor = ThreadPoolExecutor(**executor_opts)

        thread_started_future = current_loop.create_future()

        async def init_task():
            current_loop.call_soon_threadsafe(thread_started_future.set_result, None)

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
        if self.loop is None:
            return

        def cancel_tasks_and_stop_loop():
            tasks = asyncio.all_tasks(loop=self.loop)

            for task in tasks:
                self.loop.call_soon_threadsafe(task.cancel)

            gather = asyncio.gather(*tasks, return_exceptions=True)
            gather.add_done_callback(
                lambda _: self.loop.call_soon_threadsafe(self.loop.stop)
            )

        self.loop.call_soon_threadsafe(cancel_tasks_and_stop_loop)


class ThreadsafeProxy:
    """Proxy class which enforces threadsafe non-blocking calls
    This class can be used to wrap an object to ensure any calls
    using that object's methods are done on a particular event loop
    """

    def __init__(self, obj, obj_loop):
        self._obj = obj
        self._obj_loop = obj_loop

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
            if loop.is_closed():
                # Disconnected
                LOGGER.warning("Attempted to use a closed event loop")
                return
            if asyncio.iscoroutinefunction(func):
                future = asyncio.run_coroutine_threadsafe(call(), loop)
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

                loop.call_soon_threadsafe(check_result_wrapper)

        return func_wrapper
