import argparse
import asyncio
import time

from os import getenv

import gui
from config import sender_log, reader_log, OpenConnection


HOST_CLIENT = str(getenv("HOST_CLIENT", "188.246.233.198"))
PORT_CLIENT = int(getenv("PORT_CLIENT", 5000))

sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
messages_queue = asyncio.Queue()


async def read_msgs(messages_queue, host, port):
    async with OpenConnection(host, port) as (reader, writer):
        try:
            while True:
                data = await reader.readline()
                messages_queue.put_nowait(data.decode())
        except (ConnectionRefusedError, ConnectionResetError, ConnectionError) as exc:
            reader_log.error(exc)
            writer.close()
            await writer.wait_closed()


def argparser():

    parser = argparse.ArgumentParser(description="Chat client")

    parser.add_argument(
        "-ht",
        "--host",
        type=str,
        # default=str(getenv("CHAT_HOST", "minechat.dvmn.org")),
        default=str(getenv("HOST_CLIENT", "188.246.233.198")),
        help="Enter host",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        # default=int(getenv("CHAT_PORT", 5050)),
        default=int(getenv("PORT_CLIENT", 5000)),
        help="Enter port",
    )
    parser.add_argument("-t", "--token", type=str, help="Enter hash token")
    parser.add_argument("-r", "--reg", type=str, help="Enter nickname for registration")
    # parser.add_argument("msg", type=str, help="Enter message")
    return parser.parse_args()


async def main():
    parser = argparser()
    host = parser.host
    port = parser.port
    tasks = [gui.draw(messages_queue, sending_queue, status_updates_queue), read_msgs(messages_queue, host, port)]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())


