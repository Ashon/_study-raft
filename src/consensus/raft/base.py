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

    @staticmethod
    def synchronized(fn) -> Callable:
        """Wraps function with lock for synchronized transaction
        """

        async def _wrap(self: StateMachine,
                        *args: tuple, **kwargs: dict) -> Any:
            logger.trace(f'synchronized [fn={fn.__name__}] acquire lock')
            await self._lock.acquire()
            try:
                return fn(self, *args, **kwargs)

            finally:
                logger.trace(f'synchronized [fn={fn.__name__}] release lock')
                self._lock.release()

        _wrap.__name__ = fn.__name__
        return _wrap

    @staticmethod
    def before_states(states: List[str]) -> Callable:
        def _decorator(fn: Callable) -> Callable:
            def _wrap(self: StateMachine, *args: tuple, **kwargs: dict) -> Any:
                logger.trace((
                    f'before_states [fn={fn.__name__}]'
                    f' [state={self._state}] [desired={states}]'
                ))

                if self._state not in states:
                    raise WrongStateConditionError()

                return fn(self, *args, **kwargs)

            _wrap.__name__ = fn.__name__
            return _wrap

        return _decorator
