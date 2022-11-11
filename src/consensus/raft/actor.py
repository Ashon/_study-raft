import asyncio
import random
from typing import Any
from typing import List

import core.logger as logger
from transport.transmission import broadcall
from consensus.raft.state_machine import RaftStateMachine
from consensus.raft.state_machine import STATE_FOLLOWER
from consensus.raft.state_machine import STATE_CANDIDATE
from consensus.raft.state_machine import STATE_LEADER


class LeaderTimeoutError(RuntimeError):
    pass


async def timeout(task: asyncio.Task, duration: float) -> None:
    """simple task timeout helper

    no use 'asyncio.wait_for' for catching CancelledError.
    """
    await asyncio.sleep(duration)
    task.cancel()


class RaftActor(object):
    context: RaftStateMachine
    queue: asyncio.Queue

    leader_timeout: float
    election_timeout_jitter: float
    vote_interval: float
    heartbeat_interval: float

    def __init__(
            self, context: RaftStateMachine, queue: asyncio.Queue,
            leader_timeout: float, election_timeout_jitter: float,
            vote_interval: float, heartbeat_interval: float):

        self.context = context
        self.queue = queue
        self.leader_timeout = leader_timeout
        self.election_timeout_jitter = election_timeout_jitter
        self.vote_interval = vote_interval
        self.heartbeat_interval = heartbeat_interval

    async def _wait_for_leader(self, timeout_seconds: float) -> str:
        try:
            logger.trace(
                f'{self.context.log_header} wait message from waiter queue.')
            wait_for_leader = asyncio.create_task(
                self.queue.get(), name='wait_for_leader')

            timer = asyncio.create_task(
                timeout(wait_for_leader, timeout_seconds),
                name='timer')

            message = await wait_for_leader  # type: str
            logger.debug(
                f'{self.context.log_header} heartbeat received: {message!r}')

        except asyncio.exceptions.CancelledError:
            if timer.cancelled():
                # when CancelledError is not raised from timer,
                # cancel timer and propagates CancelledError to
                # outside for stopping loop.
                logger.trace(f'{self.context.log_header} stop timer.')
                raise

            raise LeaderTimeoutError()

        return message

    async def _act_as_follower(self) -> None:
        """Act as a follower

        follower only respond to leader healthcheck.
        """

        logger.info(f'{self.context.log_header} run as {STATE_FOLLOWER} state')

        while self.context._state == STATE_FOLLOWER:
            logger.debug((
                f'{self.context.log_header} waiting heartbeat'
                f' [{self.leader_timeout=}s]'
            ))

            try:
                message = await self._wait_for_leader(self.leader_timeout)
                logger.debug((
                    f'{self.context.log_header}'
                    f' heartbeat received: {message!r}'
                ))
                continue

            except LeaderTimeoutError:
                logger.warn(f'{self.context.log_header} leader timeout.')

            try:
                election_timeout = random.uniform(
                    0, self.election_timeout_jitter)
                logger.warn((
                    f'{self.context.log_header} wait for election timeout.',
                    f' [{election_timeout=}]'
                ))
                message = await self._wait_for_leader(election_timeout)
                continue

            except LeaderTimeoutError:
                logger.warn(f'{self.context.log_header} election timeout.')
                self.context.promote_to_candidate()

    async def _act_as_candidate(self) -> None:
        logger.info(
            f'{self.context.log_header} run as {STATE_CANDIDATE} state')

        while self.context._state == STATE_CANDIDATE:
            logger.debug((
                f'{self.context.log_header} sending vote requests.'
                f' [{self.vote_interval=}s]'
            ))
            messages = await broadcall(
                self.context._peers,
                f'vote {self.context._term} {self.context._name}'
            )
            votes = len([m for m in messages if m.startswith('+')])

            if votes > 0:
                self.context.promote_to_leader()
                # exit candidate loop
                break

            logger.warn(f'{self.context.log_header} wait for the next vote')

            await asyncio.sleep(self.vote_interval)

    async def _act_as_leader(self) -> None:
        logger.info(f'{self.context.log_header} run as {STATE_LEADER} state')

        while self.context._state == STATE_LEADER:
            await self.send_heartbeats_to_peers()
            await asyncio.sleep(self.heartbeat_interval)

    async def send_heartbeats_to_peers(self) -> List[str]:
        logger.debug((
            f'{self.context.log_header} sending heartbeats.'
            f' [{self.heartbeat_interval=}s]'
        ))
        responses = await broadcall(
            self.context._peers,
            f'heartbeat {self.context._term} {self.context._name}'
        )  # type: List[str]
        logger.debug(f'{self.context.log_header} [{responses=}]')

        return responses

    def create_worker(self) -> Any:
        async def run_worker() -> None:
            logger.info(f'{self.context.log_header} start raft worker')

            while True:
                try:
                    await self._act_as_follower()
                    await self._act_as_candidate()
                    await self._act_as_leader()

                except asyncio.exceptions.CancelledError:
                    logger.trace(f'{self.context.log_header} stop worker')

                    # TODO: Add stopping process
                    break

            logger.info(f'{self.context.log_header} worker stopped')

        return run_worker()
