import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

LOGGER = logging.getLogger(__name__)

# How long to let tasks finish on their own once the loop has been stopped, before
# cancelling them. A transport closing its file descriptor in an executor is one of them.
SHUTDOWN_TIMEOUT = 5


async def _finish_tasks() -> None:
    tasks = asyncio.all_tasks() - {asyncio.current_task()}
    if not tasks:
        return

    _, pending = await asyncio.wait(tasks, timeout=SHUTDOWN_TIMEOUT)

    for task in pending:
        LOGGER.warning("Cancelling task that did not finish during shutdown: %r", task)
        task.cancel()

    await asyncio.gather(*pending, return_exceptions=True)


class EventLoopThread:
    """Run a parallel event loop in a separate thread."""

    def __init__(self):
        self.loop = None
        self.thread_complete = None

    def run_coroutine_threadsafe(self, coroutine):
        current_loop = asyncio.get_running_loop()
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return asyncio.wrap_future(future, loop=current_loop)

    def _thread_main(self, on_started):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Signalled from inside `run_forever()`, so a `stop()` that arrives right after
            # `start()` returns is seen by the same run of the loop
            self.loop.call_soon(on_started)
            self.loop.run_forever()
            self.loop.run_until_complete(_finish_tasks())
        finally:
            loop, self.loop = self.loop, None
            loop.close()

    async def start(self):
        current_loop = asyncio.get_running_loop()
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=__name__)

        thread_started_future = current_loop.create_future()

        def on_started():
            current_loop.call_soon_threadsafe(thread_started_future.set_result, None)

        # Use current loop so current loop has a reference to the long-running thread
        # as one of its tasks
        thread_complete = current_loop.run_in_executor(
            executor, self._thread_main, on_started
        )
        self.thread_complete = thread_complete
        current_loop.call_soon(executor.shutdown, False)

        try:
            await asyncio.shield(thread_started_future)
        except BaseException:
            # The worker may not be running yet, stop it once it is
            thread_started_future.add_done_callback(lambda _: self.stop())
            await thread_complete
            raise

        return thread_complete

    def stop(self):
        loop = self.loop

        if loop is not None:
            loop.call_soon_threadsafe(loop.stop)

        return self.thread_complete
