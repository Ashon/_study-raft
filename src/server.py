#!/usr/bin/env python
import argparse

import uvloop

import settings
from core.application import start_application


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Raft')
    parser.add_argument(
        '-a', '--addr', default='127.0.0.1', help='listen address')
    parser.add_argument(
        '-p', '--port', default='2468', help='listen port')
    parser.add_argument(
        '-n', '--name', default='raft-1', help='process identifier')
    parser.add_argument(
        '-l', '--loglevel', default='INFO', help='log level')
    parser.add_argument(
        '--no-color', action='store_true', help='no colored log')
    parser.add_argument(
        '--no-uvloop', action='store_true', help='don\'t use uvloop')
    args = parser.parse_args()

    if not args.no_uvloop:
        uvloop.install()

    start_application(
        name=args.name,
        addr=args.addr,
        port=args.port,
        log_level=args.loglevel,
        log_color=not args.no_color,
        settings=settings
    )
