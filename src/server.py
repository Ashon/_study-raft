#!/usr/bin/env python
import argparse

import uvloop

from core.application import Raft
from core import defaults


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Raft')

    parser.add_argument(
        '-a', '--addr',
        default=defaults.DEFAULT_ADDR,
        help=f'listen address (default = {defaults.DEFAULT_ADDR})')
    parser.add_argument(
        '-p', '--port',
        default=defaults.DEFAULT_PORT,
        help=f'listen port (default = {defaults.DEFAULT_PORT})')
    parser.add_argument(
        '-n', '--name',
        default=defaults.DEFAULT_NAME,
        help=f'process identifier (default = {defaults.DEFAULT_NAME})')
    parser.add_argument(
        '-l', '--loglevel',
        default=defaults.DEFAULT_LOGLEVEL,
        help=f'log level (default = {defaults.DEFAULT_LOGLEVEL})')
    parser.add_argument(
        '-d', '--datadir',
        default=defaults.DEFAULT_DATADIR,
        help=f'data directory (default = {defaults.DEFAULT_DATADIR})')
    parser.add_argument(
        '-t', '--leader-timeout',
        default=defaults.DEFAULT_LEADER_TIMEOUT,
        help=('leader heartbeat timeout'
              f' (default = {defaults.DEFAULT_LEADER_TIMEOUT})'))
    parser.add_argument(
        '-e', '--election-timeout-jitter',
        default=defaults.DEFAULT_ELECTION_TIMEOUT_JITTER,
        help=('election timeout jitter'
              f' (default = {defaults.DEFAULT_ELECTION_TIMEOUT_JITTER})'))
    parser.add_argument(
        '-i', '--vote-interval',
        default=defaults.DEFAULT_VOTE_INTERVAL,
        help=('default vote interval'
              f' (default = {defaults.DEFAULT_VOTE_INTERVAL})'))
    parser.add_argument(
        '-b', '--heartbeat-interval',
        default=defaults.DEFAULT_HEARTBEAT_INTERVAL,
        help=('heartbeat interval'
              f' (default = {defaults.DEFAULT_HEARTBEAT_INTERVAL})'))
    parser.add_argument(
        '-r', '--report-interval',
        default=defaults.DEFAULT_REPORT_INTERVAL,
        help=('state report interval'
              f' (default = {defaults.DEFAULT_REPORT_INTERVAL})'))
    parser.add_argument(
        '-m', '--members',
        default=defaults.DEFAULT_PEERS,
        help=('raft members (comma separated \'name:addr:port\' values.)'
              f' (default = {defaults.DEFAULT_PEERS})'))
    parser.add_argument(
        '--no-color', action='store_true', help='no colored log')
    parser.add_argument(
        '--no-uvloop', action='store_true', help='don\'t use uvloop')

    args = parser.parse_args()

    if not args.no_uvloop:
        uvloop.install()

    app = Raft(
        name=args.name, addr=args.addr, port=args.port, data_dir=args.datadir,
        log_level=args.loglevel, log_color=not args.no_color,

        peers=args.members, leader_timeout=args.leader_timeout,
        election_timeout_jitter=args.election_timeout_jitter,
        vote_interval=args.vote_interval,
        heartbeat_interval=args.heartbeat_interval,

        report_interval=args.report_interval,
    )

    app.run()
