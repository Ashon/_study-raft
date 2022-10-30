import asyncio

from services.raft import call


asyncio.run(call('127.0.0.1', 2469, 'hi'))
