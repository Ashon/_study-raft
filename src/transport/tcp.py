import asyncio
from asyncio.streams import StreamReader
from asyncio.streams import StreamWriter
from typing import Callable

import core.logger as logger


CMD_OK = '+OK'
CMD_ERR = '-ERR'


async def run_server(name: str, addr: str, port: int, commands: dict) -> None:
    logger.info(f'[{name=}] start tcp server')

    # create TCP server
    handler = get_handler(name=name, commands=commands)
    server = await asyncio.start_server(handler, addr, port)

    try:
        async with server:
            (_ip, _port) = server.sockets[0].getsockname()
            logger.info(f'[{name=}] server listen at {_ip}:{_port}')
            await server.serve_forever()

    except asyncio.exceptions.CancelledError:
        logger.trace(f'[{name=}] close server')
        server.close()

    logger.info(f'[{name=}] server closed')


def parse_message(commands: dict, message: str) -> tuple:
    (cmd, raw_args) = message.split('\n')[0].split(maxsplit=1)

    if method_arg_length := commands.get(cmd):
        method, length = method_arg_length

    args = raw_args.split(maxsplit=length)

    return method, args


async def close_connection(writer: StreamWriter) -> None:
    await writer.drain()

    writer.close()


def response_ok(message: str) -> bytes:
    return f'{CMD_OK}:{message}\r\n'.encode()


def response_err(message: str) -> bytes:
    return f'{CMD_ERR}:{message}\r\n'.encode()


def get_handler(name: str, commands: dict) -> Callable:
    async def _handle_request(
            reader: StreamReader, writer: StreamWriter) -> None:

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

                response = await method(*args)
                logger.trace(
                    f'[{name}] msg from client {ip}:{port} : {message!r}')

            except Exception as e:
                response = response_err('UNKNOWN_ERROR')
                logger.error(
                    f'[{name}] [{ip}:{port}] error occurred. [{message=}] {e}')

            logger.trace(
                f'[{name}] send to client {ip}:{port} message: {response!r}')
            writer.write(response)

    return _handle_request
