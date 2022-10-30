import asyncio

import core.logger as logger

from transport.transmission import broadcall
import consensus.state as state


def _log_header():
    return f'[{state.get_state()} {state.get_leader()}]'


async def timeout(task: asyncio.Task, duration: float):
    """simple task timeout helper

    no use 'asyncio.wait_for' for catching CancelledError.
    """
    await asyncio.sleep(duration)
    task.cancel()


async def act_as_follower(leader_timeout: float):
    """Act as a follower

    follower only respond to leader healthcheck.
    """

    logger.info(f'{_log_header()} run as {state.STATE_FOLLOWER} state')

    while state.get_state() == state.STATE_FOLLOWER:
        logger.debug(f'{_log_header()} waiting heartbeat [{leader_timeout=}s]')

        try:
            logger.trace(f'{_log_header()} wait message from waiter queue.')
            wait_for_leader = asyncio.create_task(
                state.get_queue().get(), name='wait_for_leader')
            timer = asyncio.create_task(
                timeout(wait_for_leader, leader_timeout), name='timer')

            message = await wait_for_leader
            logger.debug(f'{_log_header()} heartbeat received: {message!r}')

        except asyncio.exceptions.CancelledError:
            if timer.cancelled():
                # when CancelledError is not raised from timer, cancel timer
                # and propagates CancelledError to outside for stopping loop.
                logger.trace(f'{_log_header()} stop timer.')
                raise

            logger.warn(f'{_log_header()} leader timeout.')

            state.set_leader(None)
            state.set_state(state.STATE_CANDIDATE)


async def act_as_candidate(name, peers, vote_interval):
    logger.info(f'{_log_header()} run as {state.STATE_CANDIDATE} state')

    while state.get_state() == state.STATE_CANDIDATE:
        logger.debug(
            f'{_log_header()} sending vote requests. [{vote_interval=}s]')
        messages = await broadcall(peers, f'vote {name}')
        votes = len([m for m in messages if m.startswith('+')])

        if votes > 0:
            # promote to leader
            state.set_leader(None)
            state.set_state(state.STATE_LEADER)

            # exit candidate loop
            break

        logger.warn(f'{_log_header()} wait for the next vote')

        await asyncio.sleep(vote_interval)


async def act_as_leader(name, peers, heartbeat_interval):
    logger.info(f'{_log_header()} run as {state.STATE_LEADER} state')

    while state.get_state() == state.STATE_LEADER:
        logger.debug(
            f'{_log_header()} sending heartbeats. [{heartbeat_interval=}s]')
        responses = await broadcall(peers, f'heartbeat {name}')

        logger.debug(f'{_log_header()} [{responses=}]')
        await asyncio.sleep(heartbeat_interval)


async def run_worker(
        name: str, peers, leader_timeout: float,
        vote_interval: float, heartbeat_interval: float):

    state.set_name(name)
    logger.info(f'{_log_header()} start raft worker')

    peer_ip_port_pairs = [
        peer_ip_port.split(':', 1)[1] for peer_ip_port in peers
        if peer_ip_port.split(':')[0] != name
    ]

    while True:
        try:
            await act_as_follower(
                leader_timeout=leader_timeout)

            await act_as_candidate(
                name, peers=peer_ip_port_pairs,
                vote_interval=vote_interval)

            await act_as_leader(
                name, peers=peer_ip_port_pairs,
                heartbeat_interval=heartbeat_interval)

        except asyncio.exceptions.CancelledError:
            logger.trace(f'{_log_header()} stop worker')

            # TODO: Add stopping process
            break

    logger.info(f'{_log_header()} worker stopped')
