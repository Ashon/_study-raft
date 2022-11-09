import asyncio

from core import logger
from consensus.raft.state_machine import RaftStateMachine
from consensus.raft.state_machine import STATE_FOLLOWER
from consensus.raft.state_machine import STATE_CANDIDATE
from transport.tcp import run_server


CMD_OK = '+OK'
CMD_ERR = '-ERR'
CMD_DATAEMPTY = '-EMPTY'

ERR_NOT_FOLLOWER = 'NOT_FOLLOWER'
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

    def heartbeat_from_leader(self, term, leader_name) -> str:
        """as a follower, ensure mystate is follower
        """
        logger.trace(f'got heartbeat message: {leader_name=}')

        if self.context._state not in (STATE_FOLLOWER, STATE_CANDIDATE):
            return f'{CMD_ERR}:{ERR_NOT_FOLLOWER}'

        term = int(term)
        if self.context._term > term:
            return f'{CMD_ERR}:{ERR_LOWER_TERM}'

        self.context.demote_to_follower()
        if self.context._leader != leader_name:
            self.context.set_leader(term, leader_name)

        logger.trace('emit message to leader waiter queue')
        self.queue.put_nowait(leader_name)

        return f'{CMD_OK}:{self.context._name}'

    def vote_from_candidate(self, term, candidate_name):
        """as a follower, response vote message to candidate.

        if leader is not elected, accept voting from candidate.
        """
        logger.trace(f'got vote request: {candidate_name=}')

        term = int(term)
        if self.context._term > term:
            return f'{CMD_ERR}:{ERR_LOWER_TERM}'

        if self.context._state != STATE_FOLLOWER:
            return f'{CMD_ERR}:{ERR_NOT_FOLLOWER}'

        self.context.set_leader(term, candidate_name)

        return f'{CMD_OK}:{self.context._name}'

    def create_server(self):
        return run_server(
            name='consensus', addr=self.addr, port=self.port,
            commands={
                'heartbeat': (self.heartbeat_from_leader, 2),
                'vote': (self.vote_from_candidate, 2),
            }
        )
