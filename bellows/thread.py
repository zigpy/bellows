from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
import contextlib
import functools
import logging
from typing import Any, TypeVar

_T = TypeVar("_T")

LOGGER = logging.getLogger(__name__)


class EventLoopThread:
    """Run a parallel event loop in a separate thread."""

    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None
        self.thread_complete: asyncio.Future[None] | None = None

    def run_coroutine_threadsafe(
        self, coroutine: Coroutine[Any, Any, _T]
    ) -> asyncio.Future[_T]:
        current_loop = asyncio.get_event_loop()
        assert self.loop is not None
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return asyncio.wrap_future(future, loop=current_loop)

    def _thread_main(self, init_task: Coroutine[Any, Any, None]) -> None:
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

    async def start(self) -> asyncio.Future[None] | None:
        current_loop = asyncio.get_event_loop()
        if self.loop is not None and not self.loop.is_closed():
            return None

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=__name__)

        thread_started_future = current_loop.create_future()

        async def init_task() -> None:
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

    def force_stop(self) -> None:
        loop = self.loop
        if loop is None or loop.is_closed():
            return

        def cancel_tasks_and_stop_loop() -> None:
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

    def __init__(self, obj: Any, obj_loop: asyncio.AbstractEventLoop) -> None:
        self._obj = obj
        self._obj_loop = obj_loop

    def __getattr__(self, name: str) -> Callable[..., Any]:
        func = getattr(self._obj, name)
        if not callable(func):
            raise TypeError(
                f"Can only use ThreadsafeProxy with callable attributes: {self._obj.__class__.__name__}.{name}"
            )

        def func_wrapper(*args: Any, **kwargs: Any) -> Any:
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

                def check_result_wrapper() -> None:
                    result = call()
                    if result is not None:
                        raise TypeError(
                            "ThreadsafeProxy can only wrap functions with no return"
                            f"value \nUse an async method to return values: {self._obj.__class__.__name__}.{name}"
                        )

                loop.call_soon_threadsafe(check_result_wrapper)

        return func_wrapper
