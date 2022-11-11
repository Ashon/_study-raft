#!/usr/bin/env python

import uvloop

from core.application import Raft
from core.config import RaftConfig


if __name__ == '__main__':
    config = RaftConfig()

    if not config.no_uvloop:
        uvloop.install()

    app = Raft(
        name=config.name,

        addr=config.addr,
        port=config.port,
        data_dir=config.datadir,

        log_level=config.loglevel,
        log_color=not config.no_color,

        peers=config.members,
        leader_timeout=config.leader_timeout,
        election_timeout_jitter=config.election_timeout_jitter,
        vote_interval=config.vote_interval,
        heartbeat_interval=config.heartbeat_interval,

        report_interval=config.report_interval,
    )

    app.run()
