import asyncio

from transport.transmission import call


asyncio.run(call('127.0.0.1', 2469, 'hi'))
