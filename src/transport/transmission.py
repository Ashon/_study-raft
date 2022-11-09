import asyncio

import core.logger as logger


async def call(ip: str, port: int, message: str):
    logger.trace(f'[{ip}:{port}] open connection')
    reader, writer = await asyncio.open_connection(ip, port)
    logger.trace(f'[{ip}:{port}] connection opened')

    payload = f'{message}\n'.encode()
    logger.trace(f'[{ip}:{port}] write: {payload.decode()!r}')

    writer.write(payload)
    await writer.drain()

    data = await reader.readline()
    logger.trace(f'[{ip}:{port}] received: {data.decode()!r}')

    logger.trace(f'[{ip}:{port}] close connection')
    writer.close()
    await writer.wait_closed()
    logger.trace(f'[{ip}:{port}] connection closed')

    return data.decode()


async def broadcall(ip_ports, message: str):
    """send & receive response from ip port list

    not broadcast, because this waits response from dst.
    """

    responses = []

    print(ip_ports)
    for ip_port in ip_ports:

        ip, port = ip_port.split(':')
        logger.trace(f'dialup {ip}:{port}')

        try:
            response = await call(ip, int(port), message)
            logger.debug(f'got message from {ip}:{port} [{response=!r}]')

            responses.append(response)

        except ConnectionRefusedError:
            logger.warn(f'dialup failed {ip}:{port}')

    return responses
