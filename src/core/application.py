import asyncio
import os
import sys
import signal
import traceback

import core.logger as logger
from consensus.raft import run_worker
from consensus.state import run_reporter
from consensus.state import heartbeat_from_leader
from consensus.state import vote_from_candidate
from transport.tcp import run_server


def prepare_service(name: str, log_level: str, log_color: bool, settings):
    logger.set_logger(name, log_level.upper(), color=log_color)

    # ensure data directory
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    # TODO: Implement log transactions.

    return True


async def wrap_generator(generator):
    """Wraps async generator for failfast.
    """

    try:
        await generator

    except Exception as e:
        logger.critical('critical error occurred')
        traceback.print_exception(e)

        sys.exit(255)


def _raise_sigint(*args, **kwargs):
    raise KeyboardInterrupt()


def start_application(
        name: str, addr: str, port: int,
        log_level: str, log_color: bool, settings) -> None:

    # prepare service
    prepare_service(name, log_level, log_color, settings)

    loop = asyncio.new_event_loop()

    generators = [
        run_server(
            name='consensus', addr=addr, port=port,
            commands={
                'heartbeat': (heartbeat_from_leader, 1),
                'vote': (vote_from_candidate, 1),
            }
        ),
        run_worker(
            name=name, peers=settings.PEERS,
            leader_timeout=settings.LEADER_TIMEOUT,
            vote_interval=settings.VOTE_INTERVAL,
            heartbeat_interval=settings.HEARTBEAT_INTERVAL
        ),
        run_reporter(
            report_interval=settings.REPORT_INTERVAL
        )
    ]

    for generator in generators:
        loop.create_task(
            wrap_generator(generator),
            name=generator.__name__)

    signal.signal(signal.SIGINT, _raise_sigint)
    signal.signal(signal.SIGTERM, _raise_sigint)

    try:
        logger.trace(f'run event loop [{loop=}]')
        loop.run_forever()

    except KeyboardInterrupt:
        pass

    finally:
        for task in asyncio.all_tasks(loop):
            taskname = task.get_name()
            logger.trace(f'canceling task: {taskname}')
            task.cancel()
            logger.trace(f'task canceled: {taskname}')

        logger.trace('close event loop')
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logger.trace('event loop closed')

    logger.info('bye')
