#!/usr/bin/env python
import argparse

import uvloop

from core.application import start_application


DEFAULT_ADDR = '127.0.0.1'
DEFAULT_PORT = 2468
DEFAULT_NAME = 'raft-1'
DEFAULT_LOGLEVEL = 'info'
DEFAULT_DATADIR = './.data'

DEFAULT_LEADER_TIMEOUT = 5.0
DEFAULT_ELECTION_TIMEOUT_JITTER = 3.0
DEFAULT_VOTE_INTERVAL = 2.0
DEFAULT_HEARTBEAT_INTERVAL = 3.0

DEFAULT_REPORT_INTERVAL = 10.0
DEFAULT_PEERS = (
    'raft-1:127.0.0.1:2468,raft-2:127.0.0.1:2469,raft-3:127.0.0.1:2470')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Raft')
    parser.add_argument(
        '-a', '--addr', default=DEFAULT_ADDR,
        help=f'listen address (default = {DEFAULT_ADDR})')
    parser.add_argument(
        '-p', '--port', default=DEFAULT_PORT,
        help=f'listen port (default = {DEFAULT_PORT})')
    parser.add_argument(
        '-n', '--name', default=DEFAULT_NAME,
        help=f'process identifier (default = {DEFAULT_NAME})')
    parser.add_argument(
        '-l', '--loglevel', default=DEFAULT_LOGLEVEL,
        help=f'log level (default = {DEFAULT_LOGLEVEL})')
    parser.add_argument(
        '-d', '--datadir', default=DEFAULT_DATADIR,
        help=f'data directory (default = {DEFAULT_DATADIR})')

    parser.add_argument(
        '-t', '--leader-timeout', default=DEFAULT_LEADER_TIMEOUT,
        help=(
            'leader heartbeat timeout'
            f' (default = {DEFAULT_LEADER_TIMEOUT})'))
    parser.add_argument(
        '-e', '--election-timeout-jitter',
        default=DEFAULT_ELECTION_TIMEOUT_JITTER,
        help=(
            'election timeout jitter'
            f' (default = {DEFAULT_ELECTION_TIMEOUT_JITTER})'))
    parser.add_argument(
        '-i', '--vote-interval', default=DEFAULT_VOTE_INTERVAL,
        help=f'default vote interval (default = {DEFAULT_VOTE_INTERVAL})')
    parser.add_argument(
        '-b', '--heartbeat-interval', default=DEFAULT_HEARTBEAT_INTERVAL,
        help=(
            'heartbeat interval'
            f' (default = {DEFAULT_HEARTBEAT_INTERVAL})'))
    parser.add_argument(
        '-r', '--report-interval', default=DEFAULT_REPORT_INTERVAL,
        help=(
            'state report interval'
            f' (default = {DEFAULT_REPORT_INTERVAL})'))
    parser.add_argument(
        '-m', '--members', default=DEFAULT_PEERS, help=(
            'raft members (comma separated \'name:addr:port\' values.)'
            f' (default = {DEFAULT_PEERS})'
        )
    )
    parser.add_argument(
        '--no-color', action='store_true', help='no colored log')
    parser.add_argument(
        '--no-uvloop', action='store_true', help='don\'t use uvloop')

    args = parser.parse_args()

    if not args.no_uvloop:
        uvloop.install()

    start_application(
        name=args.name, addr=args.addr, port=args.port, data_dir=args.datadir,
        log_level=args.loglevel, log_color=not args.no_color,

        peers=args.members, leader_timeout=args.leader_timeout,
        election_timeout_jitter=args.election_timeout_jitter,
        vote_interval=args.vote_interval,
        heartbeat_interval=args.heartbeat_interval,

        report_interval=args.report_interval,
    )
