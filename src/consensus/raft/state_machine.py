from typing import Any
from typing import Callable
from typing import List
from typing import Optional

import core.logger as logger


STATE_FOLLOWER = 'FOLLOWER'
STATE_CANDIDATE = 'CANDIDATE'
STATE_LEADER = 'LEADER'


class StatePromotionError(RuntimeError):
    pass


class StateMachine(object):
    _state: str

    def __init__(self, state: str) -> None:
        self._state = state


def before_states(states: List[str]) -> Callable:
    def _decorator(fn: Callable) -> Callable:
        def _wrap(self: StateMachine, *args: tuple, **kwargs: dict) -> Any:
            logger.trace(
                f'before_states {fn.__name__=}, {self._state=}, {states=}')

            if self._state not in states:
                raise StatePromotionError()

            return fn(self, *args, **kwargs)
        return _wrap

    return _decorator


class RaftStateMachine(StateMachine):
    """Raft Concensus state machine
    """

    _name: str
    _leader: Optional[str]
    _term: int

    def __init__(self, name: str, peers: List[Any]):

        # initialized as follower node
        super().__init__(STATE_FOLLOWER)

        self._name = name
        self._peers = peers

        self._leader = None
        self._term = 0

    def __setattr__(self, __name: str, __value: Any) -> None:
        logger.trace(f'set {__name} as {__value!r}')
        super().__setattr__(__name, __value)

    @property
    def log_header(self) -> str:
        return f'[{self._term} {self._state} {self._leader}]'

    @before_states([STATE_FOLLOWER])
    def promote_to_candidate(self) -> None:
        self._term += 1
        self._leader = None
        self._state = STATE_CANDIDATE

    @before_states([STATE_CANDIDATE])
    def promote_to_leader(self) -> None:
        self._leader = None
        self._state = STATE_LEADER

    @before_states([STATE_FOLLOWER, STATE_CANDIDATE])
    def demote_to_follower(self) -> None:
        self._state = STATE_FOLLOWER

    def set_leader(self, term: int, leader_name: str) -> None:
        logger.info(f'new leader elected to [{term=}] [{leader_name=}]')
        self._term = term
        self._leader = leader_name
