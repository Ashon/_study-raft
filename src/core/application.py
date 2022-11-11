import asyncio
import os
import signal
import sys
import traceback
from typing import Awaitable
from typing import Optional
from types import FrameType

import core.logger as logger
from consensus.raft.state_machine import RaftStateMachine
from consensus.raft.actor import RaftActor
from consensus.raft.tcp_server import RaftTCPServer
from consensus.raft.reporter import RaftStateReporter


def raise_sigint(signum: int, frame: Optional[FrameType]) -> None:
    raise KeyboardInterrupt()


async def wrap_awaitable(awaitable: Awaitable) -> None:
    """Wraps async generator for failfast.
    """

    try:
        await awaitable

    except Exception as e:
        logger.critical('critical error occurred')
        traceback.print_exception(e)

        sys.exit(255)


def prepare_service(name: str, log_level: str,
                    log_color: bool, datadir: str) -> bool:

    logger.set_logger(name, log_level.upper(), color=log_color)

    # ensure data directory
    os.makedirs(datadir, exist_ok=True)

    # TODO: Implement log transactions.

    return True


class Raft(object):
    _loop: asyncio.AbstractEventLoop
    _event: asyncio.Event

    _context: RaftStateMachine
    _tcp_server: RaftTCPServer
    _actor: RaftActor

    _reporter: RaftStateReporter

    def __init__(
            self, name: str, addr: str, port: int,
            log_level: str, log_color: bool,
            data_dir: str, peers: str, leader_timeout: float,
            election_timeout_jitter: float, vote_interval: float,
            heartbeat_interval: float, report_interval: float) -> None:

        peer_list = peers.split(',')
        peer_ip_port_pairs = [
            peer_ip_port.split(':', 1)[1] for peer_ip_port in peer_list
            if peer_ip_port.split(':')[0] != name
        ]

        # prepare service
        prepare_service(name, log_level, log_color, data_dir)

        self._loop = asyncio.new_event_loop()
        self._event = asyncio.Event()  # type: asyncio.Event

        # weave components
        self._context = RaftStateMachine(name=name, peers=peer_ip_port_pairs)
        self._tcp_server = RaftTCPServer(
            context=self._context, event=self._event, addr=addr, port=port)
        self._actor = RaftActor(
            context=self._context, event=self._event,
            leader_timeout=leader_timeout,
            election_timeout_jitter=election_timeout_jitter,
            vote_interval=vote_interval, heartbeat_interval=heartbeat_interval
        )
        self._reporter = RaftStateReporter(
            context=self._context, report_interval=report_interval)

        logger.set_context(self._context)

        # prepare awaitable loops, and load to eventloop
        awaitables = [
            self._actor.create_worker(),
            self._tcp_server.create_server(),
            self._reporter.create_reporter()
        ]

        for awaitable in awaitables:
            self._loop.create_task(
                wrap_awaitable(awaitable),
                name=awaitable.__name__)

    def run(self) -> None:
        signal.signal(signal.SIGINT, raise_sigint)
        signal.signal(signal.SIGTERM, raise_sigint)

        try:
            logger.trace(f'run event loop [{self._loop=}]')
            self._loop.run_forever()

        except KeyboardInterrupt:
            pass

        finally:
            for task in asyncio.all_tasks(self._loop):
                taskname = task.get_name()
                logger.trace(f'canceling task: {taskname}')
                task.cancel()
                logger.trace(f'task canceled: {taskname}')

            logger.trace('close event loop')
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            logger.trace('event loop closed')

        logger.info('bye')
