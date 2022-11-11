import asyncio
from typing import Any

import core.logger as logger
from consensus.raft.state_machine import RaftStateMachine


class RaftStateReporter(object):
    _context: RaftStateMachine
    _report_interval: float

    def __init__(self, context: RaftStateMachine,
                 report_interval: float) -> None:

        self._context = context
        self._report_interval = report_interval

    def create_reporter(self) -> Any:
        async def run_reporter() -> None:
            logger.info(f'start state reporter [{self._report_interval=}]')

            while True:
                try:
                    logger.info(f'report state {self._context}')

                    await asyncio.sleep(self._report_interval)

                except asyncio.exceptions.CancelledError:
                    logger.trace('stop reporter')

                    # TODO: Add stopping process
                    break

            logger.info('reporter stopped')

        return run_reporter()
