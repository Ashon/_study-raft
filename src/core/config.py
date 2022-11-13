import argparse
import configparser
from dataclasses import dataclass
from typing import Any
from typing import Mapping


@dataclass
class RaftConfig(object):
    name: str = 'raft-1'

    addr: str = '127.0.0.1'
    port: int = 2468
    loglevel: str = 'info'
    datadir: str = './.data'

    members: str = (
        'raft-1:127.0.0.1:2468,'
        'raft-2:127.0.0.1:2469,'
        'raft-3:127.0.0.1:2470'
    )
    leader_timeout: float = 3.0
    election_timeout_jitter: float = .3
    vote_interval: float = 3.0
    heartbeat_interval: float = 2.0
    report_interval: float = 60.0

    no_color: bool = False
    no_uvloop: bool = False

    def __init__(self) -> None:
        # config precedence is `cli > envvar > file > defaults`

        cli_config = self.config_from_args()

        config_path = cli_config.get('config')  # type: Any
        file_config = configparser.ConfigParser()
        file_config.read(config_path)

        self.override(file_config.defaults())
        self.override(cli_config)

    def override(self, args_dict: Mapping) -> None:
        for key in self.__dataclass_fields__.keys():
            if value := args_dict.get(key):
                setattr(self, key, value)

    def config_from_args(self) -> dict:
        parser = argparse.ArgumentParser(prog='Raft')

        parser.add_argument(
            '-n', '--name',
            help=f'node identifier (default = {RaftConfig.name})')

        parser.add_argument(
            '-c', '--config', help='config file path')

        parser.add_argument(
            '-a', '--addr',
            help=f'listen address (default = {RaftConfig.addr})')
        parser.add_argument(
            '-p', '--port',
            help=f'listen port (default = {RaftConfig.port})')

        parser.add_argument(
            '-l', '--loglevel',
            help=f'log level (default = {RaftConfig.loglevel})')
        parser.add_argument(
            '-d', '--datadir',
            help=f'data directory (default = {RaftConfig.datadir})')
        parser.add_argument(
            '-t', '--leader-timeout',
            help=('leader heartbeat timeout'
                  f' (default = {RaftConfig.leader_timeout})'))
        parser.add_argument(
            '-e', '--election-timeout-jitter',
            help=('election timeout jitter'
                  f' (default = {RaftConfig.election_timeout_jitter})'))
        parser.add_argument(
            '-i', '--vote-interval',
            help=('default vote interval'
                  f' (default = {RaftConfig.vote_interval})'))
        parser.add_argument(
            '-b', '--heartbeat-interval',
            help=('heartbeat interval'
                  f' (default = {RaftConfig.heartbeat_interval})'))
        parser.add_argument(
            '-r', '--report-interval',
            help=('state report interval'
                  f' (default = {RaftConfig.report_interval})'))
        parser.add_argument(
            '-m', '--members',
            help=('raft members (comma separated \'name:addr:port\' values.)'
                  f' (default = {RaftConfig.members})'))
        parser.add_argument(
            '--no-color', action='store_true', help='no colored log')
        parser.add_argument(
            '--no-uvloop', action='store_true', help='don\'t use uvloop')

        args = parser.parse_args()
        return dict(args._get_kwargs())
