import asyncio
import time

import uvloop


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 2468)

    print(f'Send({len(message)} bytes): {message!r}')

    i = 0
    now = time.perf_counter()
    for _ in range(100000):
        i += 1
        writer.write(message.encode())
        a = await reader.readline()
        if i % 10000 == 0:
            elapsed = time.perf_counter() - now
            print(f'{i / elapsed:.3f} RPS ({i} msgs {message} / {a})')

    writer.close()


uvloop.install()
asyncio.run(tcp_echo_client('get a\n'))
asyncio.run(tcp_echo_client(f'set {"a"*100} {"a"*100}\n'))
