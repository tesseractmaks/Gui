import argparse
import asyncio
import datetime
import time
import aiofiles
from async_timeout import timeout
from os import getenv
from pathlib import Path
from tkinter import messagebox, TclError

import gui
from config import logger, watchdog_logger, OpenConnection
from sender import authorise, submit_message, register

HOST_CLIENT = str(getenv("HOST_CLIENT", "188.246.233.198"))
PORT_CLIENT = int(getenv("PORT_CLIENT", 5000))
OUT_PATH = (Path(__file__).parent / "chat.log").absolute()
TIMEOUT_CONNECTION = 5

sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
messages_queue = asyncio.Queue()
watchdog_queue = asyncio.Queue()


class InvalidToken(Exception):
    def __init__(self):
        messagebox.showinfo("Invalid Token", "Your token is not valid. Please check it and try again.")


async def write_to_disk(data, file_path=OUT_PATH):
    time_now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    async with aiofiles.open(file_path, mode="a") as f:
        if isinstance(data, bytes):
            await f.write(f"[{time_now}] {data.decode()!r}\n")
        else:
            await f.write(f"[{time_now}] {data}\n")


async def load_msg_history(filepath, queue: asyncio.Queue):
    async with aiofiles.open(filepath) as file:
        contents = await file.read()
        queue.put_nowait(contents.strip())


async def send_msgs(host, port, queue: asyncio.Queue):
    token = await queue.get()
    nickname = await authorise(host, port, token, status_updates_queue)
    if not nickname:
        raise InvalidToken
    event = gui.NicknameReceived(nickname["nickname"])
    greeting = f"Выполнена авторизация. Пользователь {nickname['nickname']}"
    status_updates_queue.put_nowait(event)
    await watchdog_queue.put("Authorization done")
    messages_queue.put_nowait(greeting)
    await write_to_disk(greeting)
    while True:
        message = await queue.get()
        messages_queue.put_nowait(message)
        await write_to_disk(message)
        await submit_message(host, port, message)
        await watchdog_queue.put("Message sent")


async def read_msgs(messages_queue, out_path, host, port):
    await load_msg_history(out_path, messages_queue)
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    async with OpenConnection(host, port) as (reader, writer):
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
        try:
            while True:
                data = await reader.readline()
                messages_queue.put_nowait(data.decode())
                await watchdog_queue.put("New message in chat")
                await write_to_disk(data, out_path)
        except (ConnectionRefusedError, ConnectionResetError, ConnectionError) as exc:
            logger.error(exc)
            writer.close()
            await writer.wait_closed()


async def watch_for_connection(queue: asyncio.Queue):
    while True:
        try:
            async with timeout(TIMEOUT_CONNECTION) as tm:
                message = await queue.get()
                watchdog_logger.debug(message)
        except asyncio.TimeoutError:
            if tm.expired:
                watchdog_logger.warning(f"{TIMEOUT_CONNECTION}s timeout is expire")
                raise ConnectionError


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
        send_msgs(host, port, sending_queue),
        watch_for_connection(watchdog_queue)
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except InvalidToken:
        logger.debug('Incorrect token. Exit.')
    except (KeyboardInterrupt, TclError, asyncio.exceptions.CancelledError):
        logger.debug('The chat is closed. Exit.')



