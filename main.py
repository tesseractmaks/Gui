import argparse
import asyncio
import datetime
import time
import aiofiles

from os import getenv
from pathlib import Path

import gui
from config import sender_log, reader_log, OpenConnection
from sender import authorise, submit_message, register

HOST_CLIENT = str(getenv("HOST_CLIENT", "188.246.233.198"))
PORT_CLIENT = int(getenv("PORT_CLIENT", 5000))
OUT_PATH = (Path(__file__).parent / "chat.log").absolute()

sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
messages_queue = asyncio.Queue()


async def write_to_disk(data, file_path):
    time_now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    async with aiofiles.open(file_path, mode="a") as f:
        await f.write(f"[{time_now}] {data.decode()!r}\n")


async def load_msg_history(filepath, queue: asyncio.Queue):
    async with aiofiles.open(filepath) as file:
        contents = await file.read()
        queue.put_nowait(contents.strip())


async def send_msgs(host, port, queue: asyncio.Queue):
    token = await queue.get()
    nickname = await authorise(host, port, token)
    messages_queue.put_nowait(f"Выполнена авторизация. Пользователь {nickname['nickname']}")

    while True:
        message = await queue.get()
        messages_queue.put_nowait(message)

        await submit_message(host, port, message)


async def read_msgs(messages_queue, out_path, host, port):
    await load_msg_history(out_path, messages_queue)
    async with OpenConnection(host, port) as (reader, writer):
        try:
            while True:
                data = await reader.readline()
                messages_queue.put_nowait(data.decode())
                await write_to_disk(data, out_path)
        except (ConnectionRefusedError, ConnectionResetError, ConnectionError) as exc:
            reader_log.error(exc)
            writer.close()
            await writer.wait_closed()


def argparser():

    parser = argparse.ArgumentParser(description="Chat client")

    parser.add_argument(
        "-ph",
        "--path",
        type=str,
        default=OUT_PATH,
        help="Set path to catalog use arguments: '--path'"
    )

    parser.add_argument(
        "-ht",
        "--host",
        type=str,
        default=str(getenv("CHAT_HOST", "minechat.dvmn.org")),
        # default=str(getenv("HOST_CLIENT", "188.246.233.198")),
        help="Enter host",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=int(getenv("CHAT_PORT", 5050)),
        # default=int(getenv("PORT_CLIENT", 5000)),
        help="Enter port",
    )
    parser.add_argument("-t", "--token", type=str, help="Enter hash token")
    parser.add_argument("-r", "--reg", type=str, help="Enter nickname for registration")
    parser.add_argument("msg", type=str, help="Enter message")
    return parser.parse_args()


async def main():
    parser = argparser()
    host = parser.host
    port = parser.port
    out_path = parser.path
    message = parser.msg
    # print(message, "----")
    # sending_queue.put_nowait(message)

    # if parser.reg:
    #     await register(host, port, parser)
    # if parser.token:
    #     nickname = await authorise(host, port, parser)
    #     messages_queue.put_nowait(f"Выполнена авторизация. Пользователь {nickname['nickname']}")
    tasks = [
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(messages_queue, out_path, host, port),
        send_msgs(host, port, sending_queue)
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())


