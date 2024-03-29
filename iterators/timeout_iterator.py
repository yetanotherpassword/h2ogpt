import queue
import asyncio
import threading
import traceback


class TimeoutIterator:
    """
    Wrapper class to add timeout feature to synchronous iterators
    - timeout: timeout for next(). Default=ZERO_TIMEOUT i.e. no timeout or blocking calls to next. Updated using set_timeout() 
    - sentinel: the object returned by iterator when timeout happens
    - reset_on_next: if set to True, timeout is reset to the value of ZERO_TIMEOUT on each iteration

    TimeoutIterator uses a thread internally.
    The thread stops once the iterator exhausts or raises an exception during iteration.

    Any exceptions raised within the wrapped iterator are propagated as it is.
    Exception is raised when all elements generated by the actual iterator before exception have been consumed
    Timeout can be set dynamically before going for iteration
    """
    ZERO_TIMEOUT = 0.0

    def __init__(self, iterator, timeout=0.0, sentinel=object(),
                 reset_on_next=False, raise_on_exception=True,
                 whichi=None):
        self._iterator = iterator
        self._timeout = timeout
        self._sentinel = sentinel
        self._reset_on_next = reset_on_next
        self._raise_on_exception = raise_on_exception
        self._whichi = whichi

        self._interrupt = False
        self._done = False
        self._buffer = queue.Queue()
        self._thread = threading.Thread(target=self.__lookahead)
        self._thread.start()

    def get_sentinel(self):
        return self._sentinel

    def set_reset_on_next(self, reset_on_next):
        self._reset_on_next = reset_on_next

    def set_timeout(self, timeout: float):
        """
        Set timeout for next iteration
        """
        self._timeout = timeout

    def interrupt(self):
        """
        interrupt and stop the underlying thread.
        the thread actually dies only after interrupt has been set and
        the underlying iterator yields a value after that.
        """
        self._interrupt = True

    def __iter__(self):
        return self

    def __next__(self):
        """
        yield the result from iterator
        if timeout > 0:
            yield data if available.
            otherwise yield sentinel
        """
        if self._done:
            raise StopIteration

        data = self._sentinel
        try:
            if self._timeout > self.ZERO_TIMEOUT:
                data = self._buffer.get(timeout=self._timeout)
            else:
                data = self._buffer.get()
        except queue.Empty:
            pass
        finally:
            # see if timeout needs to be reset
            if self._reset_on_next:
                self._timeout = self.ZERO_TIMEOUT

        # propagate any exceptions including StopIteration
        if isinstance(data, BaseException):
            self._done = True
            if isinstance(data, StopIteration):
                raise data
            ex = ''.join(traceback.format_tb(data.__traceback__))
            print("Generation Failed: %s %s %s" % (str(data), str(ex), self._whichi), flush=True)
            if self._raise_on_exception:
                raise data
            else:
                return data

        return data

    def __lookahead(self):
        try:
            while True:
                self._buffer.put(next(self._iterator))
                if self._interrupt:
                    raise StopIteration()
        except BaseException as e:
            if not isinstance(e, StopIteration):
                print("Generation Failed lookahead: %s %s %s %s" % (str(e), type(e), self._whichi, traceback.format_exc()), flush=True)
            self._buffer.put(e)


class AsyncTimeoutIterator:
    """
    Async version of TimeoutIterator. See method documentation of TimeoutIterator
    """
    ZERO_TIMEOUT = 0.0

    def __init__(self, iterator, timeout=0.0, sentinel=object(), reset_on_next=False):
        self._iterator = iterator
        self._timeout = timeout
        self._sentinel = sentinel
        self._reset_on_next = reset_on_next

        self._interrupt = False
        self._done = False
        self._buffer = asyncio.Queue()
        self._task = asyncio.get_event_loop().create_task(self.__lookahead())

    def get_sentinel(self):
        return self._sentinel

    def set_reset_on_next(self, reset_on_next):
        self._reset_on_next = reset_on_next

    def set_timeout(self, timeout: float):
        self._timeout = timeout

    def interrupt(self):
        self._interrupt = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._done:
            raise StopAsyncIteration

        data = self._sentinel
        try:
            if self._timeout > self.ZERO_TIMEOUT:
                data = await asyncio.wait_for(self._buffer.get(), self._timeout)
            else:
                data = await self._buffer.get()
        except asyncio.TimeoutError:
            pass
        finally:
            # see if timeout needs to be reset
            if self._reset_on_next:
                self._timeout = self.ZERO_TIMEOUT

        # propagate any exceptions including StopIteration
        if isinstance(data, BaseException):
            self._done = True
            raise data

        return data

    async def __lookahead(self):
        try:
            while True:
                data = await self._iterator.__anext__()
                await self._buffer.put(data)
                if self._interrupt:
                    raise StopAsyncIteration()
        except BaseException as e:
            await self._buffer.put(e)
