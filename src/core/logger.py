import logging
import typing
from functools import partial
from typing import Any
from typing import Optional


if typing.TYPE_CHECKING:
    from consensus.raft.state_machine import RaftStateMachine


DEFAULT_LOG_FORMAT = (
    '[%(asctime)s.%(msecs)03d] [%(levelname)8s] [%(name)s %(process)s] '
    '[%(filename)s:%(lineno)d %(funcName)s] [%(context)s] %(message)s'
)
DEFAULT_LOG_DATE_FORMAT = '%Y-%m-%d:%H:%M:%S'

TRACE = 5
logging.addLevelName(TRACE, 'TRACE')
_LOG = logging.getLogger()
_LOG_CONTEXT: Optional[Any]

GRAY = '\x1b[38;5;240m'
BLUE = '\x1b[38;5;39m'
YELLOW = '\x1b[38;5;208m'
RED = '\x1b[38;5;196m'
BOLD_RED = '\x1b[31;1m'
RESET = '\x1b[0m'


class ColorFormatter(logging.Formatter):
    def __init__(self, fmt: str) -> None:
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            TRACE: f'{GRAY}{self.fmt}{RESET}',
            logging.DEBUG: f'{BLUE}{self.fmt}{RESET}',
            logging.INFO: self.fmt,
            logging.WARNING: f'{YELLOW}{self.fmt}{RESET}',
            logging.ERROR: f'{RED}{self.fmt}{RESET}',
            logging.CRITICAL: f'{BOLD_RED}{self.fmt}{RESET}'
        }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class ContextFilter(logging.Filter):
    context: 'RaftStateMachine'

    def __init__(self, context: Optional['RaftStateMachine']) -> None:
        super(ContextFilter, self).__init__()
        self.context = context

    def filter(self, record: logging.LogRecord) -> bool:
        if self.context:
            record.context = self.context.log_header
        else:
            record.context = '-'
        return True


def set_logger(name: str, log_level: str, color: bool) -> None:
    global _LOG
    global _LOG_CONTEXT

    formatter: logging.Formatter
    if color:
        formatter = ColorFormatter(DEFAULT_LOG_FORMAT)
    else:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.name = name
    logger.setLevel(log_level)
    logger.addHandler(handler)
    _LOG_CONTEXT = ContextFilter(None)

    _LOG.addFilter(_LOG_CONTEXT)
    _LOG = logger


def set_context(context: object) -> None:
    global _LOG_CONTEXT
    _LOG_CONTEXT.context = context  # type: ignore


trace = partial(_LOG.log, TRACE)
debug = _LOG.debug
info = _LOG.info
warning = _LOG.warning
warn = _LOG.warn
error = _LOG.error
critical = _LOG.critical
