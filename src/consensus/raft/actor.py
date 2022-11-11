import asyncio
import random
from typing import Any
from typing import List

import core.logger as logger
from transport.transmission import broadcast
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
    _context: RaftStateMachine
    _event: asyncio.Event

    _leader_timeout: float
    _election_timeout_jitter: float
    _vote_interval: float
    _heartbeat_interval: float

    def __init__(
            self, context: RaftStateMachine, event: asyncio.Event,
            leader_timeout: float, election_timeout_jitter: float,
            vote_interval: float, heartbeat_interval: float):

        self._context = context
        self._event = event
        self._leader_timeout = leader_timeout
        self._election_timeout_jitter = election_timeout_jitter
        self._vote_interval = vote_interval
        self._heartbeat_interval = heartbeat_interval

    async def _wait_for_leader(self, timeout_seconds: float) -> bool:
        try:
            logger.trace('wait leader heartbeat.')
            wait_for_leader = asyncio.create_task(
                self._event.wait(), name='wait_for_leader')

            timer = asyncio.create_task(
                timeout(wait_for_leader, timeout_seconds),
                name='timer')

            await wait_for_leader
            self._event.clear()
            logger.debug('heartbeat received.')

        except asyncio.exceptions.CancelledError:
            if timer.cancelled():
                # when CancelledError is not raised from timer,
                # cancel timer and propagates CancelledError to
                # outside for stopping loop.
                logger.trace('stop timer.')
                raise

            raise LeaderTimeoutError()

        return True

    async def _act_as_follower(self) -> None:
        """Act as a follower

        follower only respond to leader healthcheck.
        """

        logger.info(f'run as {STATE_FOLLOWER} state')

        while self._context._state == STATE_FOLLOWER:
            logger.debug((
                'waiting heartbeat'
                f' [{self._leader_timeout=}s]'
            ))

            try:
                await self._wait_for_leader(self._leader_timeout)
                logger.debug('heartbeat received.')
                continue

            except LeaderTimeoutError:
                logger.warn('leader timeout.')

            try:
                election_timeout = random.uniform(
                    0, self._election_timeout_jitter)
                logger.warn((
                    'wait for election timeout.',
                    f' [{election_timeout=}]'
                ))
                await self._wait_for_leader(election_timeout)
                continue

            except LeaderTimeoutError:
                logger.warn('election timeout.')
                await self._context.promote_to_candidate()

    async def _act_as_candidate(self) -> None:
        logger.info(
            f'run as {STATE_CANDIDATE} state')

        while self._context._state == STATE_CANDIDATE:
            logger.debug((
                'sending vote requests.'
                f' [{self._vote_interval=}s]'
            ))
            messages = await broadcast(
                self._context._peers,
                f'vote {self._context._term} {self._context._name}'
            )
            votes = len([m for m in messages if m.startswith('+')])

            if votes > 0:
                await self._context.promote_to_leader()
                # exit candidate loop
                break

            logger.warn('wait for the next vote')

            await asyncio.sleep(self._vote_interval)

    async def _act_as_leader(self) -> None:
        logger.info(f'run as {STATE_LEADER} state')

        while self._context._state == STATE_LEADER:
            await self.send_heartbeats_to_peers()
            await asyncio.sleep(self._heartbeat_interval)

    async def send_heartbeats_to_peers(self) -> List[str]:
        logger.debug((
            'sending heartbeats.'
            f' [{self._heartbeat_interval=}s]'
        ))
        responses = await broadcast(
            self._context._peers,
            f'heartbeat {self._context._term} {self._context._name}'
        )  # type: List[str]
        logger.debug(f'[{responses=}]')

        return responses

    def create_worker(self) -> Any:
        async def run_worker() -> None:
            logger.info('start raft worker')

            while True:
                try:
                    await self._act_as_follower()
                    await self._act_as_candidate()
                    await self._act_as_leader()

                except asyncio.exceptions.CancelledError:
                    logger.trace('stop worker')

                    # TODO: Add stopping process
                    break

            logger.info('worker stopped')

        return run_worker()
