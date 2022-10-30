import asyncio

import core.logger as logger
import transport.messages as messages


STATE_FOLLOWER = 'FOLLOWER'
STATE_CANDIDATE = 'CANDIDATE'
STATE_LEADER = 'LEADER'

ERR_NOT_FOLLOWER = 'NOT_FOLLOWER'
ERR_LEADER_ALREADY_ELECTED = 'LEADER_ALREADY_ELECTED'

_NAME = None
_STATE = STATE_FOLLOWER
_LEADER = None
_QUEUE = asyncio.Queue()


def set_name(name):
    logger.trace(f'set name as {name}')
    global _NAME
    _NAME = name


def get_name():
    return _NAME


def set_state(state):
    logger.trace(f'set state as {state}')
    global _STATE
    _STATE = state


def get_state():
    return _STATE


def set_leader(name):
    logger.trace(f'set leader as {name}')
    global _LEADER
    _LEADER = name


def get_leader():
    return _LEADER


def get_queue():
    return _QUEUE


def heartbeat_from_leader(leader_name):
    """as a follower, ensure mystate is follower
    """
    logger.trace(f'got heartbeat message: {leader_name=}')

    if _STATE not in (STATE_FOLLOWER, STATE_CANDIDATE):
        return f'{messages.CMD_ERR}:{ERR_NOT_FOLLOWER}'

    set_state(STATE_FOLLOWER)
    set_leader(leader_name)

    logger.trace('emit message to leader waiter queue')
    _QUEUE.put_nowait(leader_name)

    return f'{messages.CMD_OK}:{_NAME}'


def vote_from_candidate(candidate_name):
    """as a follower, response vote message to candidate.

    if leader is not elected, accept voting from candidate.
    """
    logger.trace(f'got vote request: {candidate_name=}')

    if _LEADER:
        return f'{messages.CMD_ERR}:{ERR_LEADER_ALREADY_ELECTED}'

    if _STATE != STATE_FOLLOWER:
        return f'{messages.CMD_ERR}:{ERR_NOT_FOLLOWER}'

    set_leader(candidate_name)

    return f'{messages.CMD_OK}:{_NAME}'


async def run_reporter(report_interval: float):
    logger.info(f'start state reporter [{report_interval=}]')

    while True:
        try:
            logger.info(f'report state [{_NAME=}] [{_STATE=}] [{_LEADER=}]')
            await asyncio.sleep(report_interval)

        except asyncio.exceptions.CancelledError:
            logger.trace('stop reporter')

            # TODO: Add stopping process
            break

    logger.info('reporter stopped')
