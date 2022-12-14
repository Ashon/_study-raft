from typing import Any
from typing import List
from typing import Optional

import core.logger as logger
from consensus.raft.base import StateMachine


STATE_FOLLOWER = 'FOLLOWER'
STATE_CANDIDATE = 'CANDIDATE'
STATE_LEADER = 'LEADER'


class StatePromotionError(RuntimeError):
    pass


class TermIsLowerThanCurrent(RuntimeError):
    pass


class RaftStateMachine(StateMachine):
    """Raft Concensus state machine
    """

    _name: str
    _leader: Optional[str]
    _term: int
    _peers: List[str]

    def __init__(self, name: str, peers: List[str]):

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
        return f'{self._term} {self._state} {self._leader}'

    @StateMachine.synchronized
    @StateMachine.before_states([STATE_FOLLOWER])
    def promote_to_candidate(self) -> None:
        self._term += 1
        self._leader = None
        self._state = STATE_CANDIDATE

    @StateMachine.synchronized
    @StateMachine.before_states([STATE_CANDIDATE])
    def promote_to_leader(self) -> None:
        self._leader = None
        self._state = STATE_LEADER

    @StateMachine.synchronized
    def step_down(self) -> None:
        self._state = STATE_FOLLOWER

    @StateMachine.synchronized
    def set_leader(self, term: int, leader_name: str) -> None:
        """Set leader and step-down state
        """

        logger.info(f'new leader elected to [{term=}] [{leader_name=}]')
        self._term = term
        self._leader = leader_name
        self._state = STATE_FOLLOWER

    async def heartbeat_from_leader(self, term: int, leader_name: str) -> str:
        """as a follower, ensure mystate is follower
        """

        logger.trace(f'got heartbeat message: {term=} {leader_name=}')

        if self._term > term:
            raise TermIsLowerThanCurrent()

        if self._leader != leader_name:
            await self.set_leader(term, leader_name)

        return self._name

    @StateMachine.before_states([STATE_FOLLOWER])
    async def vote_from_candidate(self, term: int, candidate_name: str) -> str:
        """as a follower, response vote message to candidate.

        if leader is not elected, accept voting from candidate.
        """
        logger.trace(f'got vote request: {candidate_name=}')

        if self._term > term:
            raise TermIsLowerThanCurrent()

        await self.set_leader(term, candidate_name)

        return self._name
