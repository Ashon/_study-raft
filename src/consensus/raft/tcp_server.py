import asyncio
from typing import Any
from typing import Callable

from core import logger
from consensus.raft.state_machine import RaftStateMachine
from consensus.raft.state_machine import WrongStateConditionError
from consensus.raft.state_machine import TermIsLowerThanCurrent
from transport.tcp import run_server
from transport.tcp import response_ok
from transport.tcp import response_err


ERR_WRONG_STATE = 'WRONG_STATE'
ERR_LOWER_TERM = 'TERM_IS_LOWER'


class RaftTCPServer(object):
    context: RaftStateMachine
    queue: asyncio.Queue

    addr: str
    port: int

    def __init__(self, context: RaftStateMachine,
                 queue: asyncio.Queue, addr: str, port: int):
        self.context = context
        self.queue = queue
        self.addr = addr
        self.port = port

    def heartbeat_from_leader(self, term: int, leader_name: str) -> bytes:
        """as a follower, ensure mystate is follower
        """
        logger.trace(f'tcp: handle heartbeat message: {term=} {leader_name=}')

        term = int(term)
        message: str
        handler = response_err  # type: Callable

        try:
            message = self.context.heartbeat_from_leader(term, leader_name)
            handler = response_ok

        except WrongStateConditionError:
            message = ERR_WRONG_STATE

        except TermIsLowerThanCurrent:
            message = ERR_LOWER_TERM

        logger.trace('emit message to leader waiter queue')
        self.queue.put_nowait(message)

        response = handler(message)  # type: bytes

        return response

    def vote_from_candidate(self, term: int, candidate_name: str) -> bytes:
        """as a follower, response vote message to candidate.

        if leader is not elected, accept voting from candidate.
        """
        logger.trace(f'tcp: got vote request: {term=} {candidate_name=}')

        term = int(term)
        message: str
        handler = response_err  # type: Callable

        try:
            message = self.context.vote_from_candidate(term, candidate_name)
            handler = response_ok

        except WrongStateConditionError:
            message = ERR_WRONG_STATE

        except TermIsLowerThanCurrent:
            message = ERR_WRONG_STATE

        response = handler(message)  # type: bytes

        return response

    def create_server(self) -> Any:
        return run_server(
            name='consensus', addr=self.addr, port=self.port,
            commands={
                'heartbeat': (self.heartbeat_from_leader, 2),
                'vote': (self.vote_from_candidate, 2),
            }
        )
