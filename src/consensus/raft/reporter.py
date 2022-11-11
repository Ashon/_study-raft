import asyncio
from typing import Any

import core.logger as logger
from consensus.raft.state_machine import RaftStateMachine


class RaftStateReporter(object):
    context: RaftStateMachine
    report_interval: float

    def __init__(self, context: RaftStateMachine,
                 report_interval: float) -> None:

        self.context = context
        self.report_interval = report_interval

    def create_reporter(self) -> Any:
        async def run_reporter() -> None:
            logger.info(f'start state reporter [{self.report_interval=}]')

            while True:
                try:
                    logger.info((
                        'report state'
                        f' [name={self.context._name}]'
                        f' [term={self.context._term}]'
                        f' [state={self.context._state}]'
                        f' [leader={self.context._leader}]'
                    ))

                    await asyncio.sleep(self.report_interval)

                except asyncio.exceptions.CancelledError:
                    logger.trace('stop reporter')

                    # TODO: Add stopping process
                    break

            logger.info('reporter stopped')

        return run_reporter()
