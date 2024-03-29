import argparse
import asyncio
import json

import aiofiles
from dotenv import load_dotenv
from config import logger, OpenConnection
import gui
from os import getenv


load_dotenv()


def encode_utf8(data):
    return data.encode("utf-8", "ignore")


def sanitize(string: str) -> str:
    string = string.replace('\n', ' ')
    string = string.replace('\t', '    ')
    return string


async def register(username: str, host, port: int) -> dict | None:
    reader, writer = await asyncio.open_connection(host, port)

    await reader.readline()
    writer.write(f'\n'.encode())
    await writer.drain()

    await reader.readline()
    writer.write(f'{sanitize(username)}\n'.encode())
    await writer.drain()

    response = await reader.readline()
    credentials = json.loads(response.decode())
    if not credentials:
        logger.error("Server Error: can't get token")
        return

    async with aiofiles.open('credentials.json', 'w') as file:
        await file.write(json.dumps(credentials))
        logger.info("Username and token saved.")

    return credentials


async def authorise(host, port, token, status_updates_queue):
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

    async with OpenConnection(host, port) as (reader, writer):
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
        data = await reader.readline()
        logger.debug(f"{data.decode()!r}")

        writer.write(token.encode())
        logger.debug(f"{token} --")
        await writer.drain()

        writer.write("\n".encode())
        await writer.drain()

        nickname = await reader.readline()
        if json.loads(nickname.decode()):
            return json.loads(nickname)

        data3 = await reader.readline()
        logger.debug(f"{data3.decode()!r}")

        # await submit_message(host, port, parser.msg)


async def submit_message(host, port, message):
    async with OpenConnection(host, port) as (reader, writer):
        # writer.write("\n".encode())
        # await writer.drain()

        # data = await reader.readline()
        # writer.write(data)
        # await writer.drain()
        #
        # writer.write("\n".encode())
        # await writer.drain()

        writer.write(encode_utf8(f"{message.strip()}\n"))
        logger.debug(message)
        await writer.drain()

        # writer.write("\n".encode())
        # await writer.drain()


def argparser():

    parser = argparse.ArgumentParser(description="Chat client")

    parser.add_argument(
        "-ht",
        "--host",
        type=str,
        default=str(getenv("CHAT_HOST", "minechat.dvmn.org")),
        help="Enter host",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=int(getenv("CHAT_PORT", 5050)),
        help="Enter port",
    )
    parser.add_argument("-t", "--token", type=str, help="Enter hash token")
    parser.add_argument("-r", "--reg", type=str, help="Enter nickname for registration")
    # parser.add_argument("msg", type=str, help="Enter message")
    return parser.parse_args()


# async def main():
#     parser = argparser()
#     host = parser.host
#     port = parser.port
#
#     if parser.reg:
#         await register(host, port, parser)
#
#     if parser.token:
#         await authorise(host, port, parser)


# if __name__ == "__main__":
#     asyncio.run(main())
