import asyncio
from asyncio.streams import StreamReader
from asyncio.streams import StreamWriter

import core.logger as logger
import transport.messages as messages


async def run_server(name: str, addr: str, port: int, commands: dict) -> None:
    logger.info(f'[{name}] start tcp server')

    # create TCP server
    handler = get_handler(name=name, commands=commands)
    server = await asyncio.start_server(handler, addr, port)

    try:
        async with server:
            (_ip, _port) = server.sockets[0].getsockname()
            logger.info(f'[{name}] server listen at {_ip}:{_port}')
            await server.serve_forever()

    except asyncio.exceptions.CancelledError:
        logger.trace(f'[{name}] close server')
        server.close()

    logger.info(f'[{name}] server closed')


def parse_message(commands, message: str):
    (cmd, raw_args) = message.split('\n')[0].split(maxsplit=1)

    method, length = commands.get(cmd)
    args = raw_args.split(maxsplit=length)

    return method, args


async def close_connection(writer: StreamWriter):
    await writer.drain()

    writer.close()


def get_handler(name, commands):
    async def _handle_request(reader: StreamReader, writer: StreamWriter):
        (ip, port) = writer.get_extra_info('peername')
        logger.trace(f'[{name}] client {ip}:{port} is connected')

        while True:
            buffer = await reader.readline()
            message = buffer.decode()

            if not message:
                logger.trace(f'[{name}] client {ip}:{port} closed')
                await close_connection(writer)
                break

            try:
                (method, args) = parse_message(commands, message)
                logger.debug(f'[{name}] {method.__name__=}, {args}')

                return_value = method(*args)
                logger.trace(
                    f'[{name}] msg from client {ip}:{port} : {message!r}')

            except Exception as e:
                return_value = messages.CMD_ERR
                logger.error(
                    f'[{name}] [{ip}:{port}] error occurred. [{message=}] {e}')

            response = f'{return_value}\r\n'.encode()

            logger.trace(
                f'[{name}] send to client {ip}:{port} message: {response!r}')
            writer.write(response)

    return _handle_request
