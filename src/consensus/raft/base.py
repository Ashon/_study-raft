import asyncio
from typing import Any
from typing import List
from typing import Callable
from core import logger


class WrongStateConditionError(RuntimeError):
    pass


class StateMachine(object):
    _state: str
    _lock: asyncio.Lock

    def __init__(self, state: str) -> None:
        self._state = state
        self._lock = asyncio.Lock()


def threadsafe(fn) -> Callable:
    async def _wrap(self: StateMachine, *args: tuple, **kwargs: dict) -> Any:
        logger.trace('threadsafe: acquire lock')
        await self._lock.acquire()
        try:
            return fn(self, *args, **kwargs)

        finally:
            logger.trace('threadsafe: release lock')
            self._lock.release()

    return _wrap


def before_states(states: List[str]) -> Callable:
    def _decorator(fn: Callable) -> Callable:
        def _wrap(self: StateMachine, *args: tuple, **kwargs: dict) -> Any:
            logger.trace(
                f'before_states {fn.__name__=}, {self._state=}, {states=}')

            if self._state not in states:
                raise WrongStateConditionError()

            return fn(self, *args, **kwargs)
        return _wrap

    return _decorator
