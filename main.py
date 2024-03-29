import argparse
import asyncio
import datetime
import os

import aiofiles
import socket
from async_timeout import timeout
from anyio import create_task_group
from dotenv import load_dotenv
from pathlib import Path
from tkinter import messagebox, TclError

import gui
from config import logger, watchdog_logger, OpenConnection
from sender import authorise, submit_message


OUT_PATH = (Path(__file__).parent / "chat.log").absolute()
READ_TIMEOUT = 5
PING_TIMEOUT = 2
TIMEOUT_CONNECTION = 20

load_dotenv()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
messages_queue = asyncio.Queue()
watchdog_queue = asyncio.Queue()
saving_queue = asyncio.Queue()


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


def add_timestamp(message: str | bytes, stamp_format: str = "[%d.%m.%Y %H:%M]") -> str:
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    timestamp = datetime.datetime.now().strftime(stamp_format)
    return f'{timestamp} {message.strip()}'


async def load_msg_history(filepath, queue: asyncio.Queue):
    async with aiofiles.open(filepath) as file:
        contents = await file.read()
        queue.put_nowait(contents.strip())


async def send_msgs(host: str, port: int, queue: asyncio.Queue):

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


async def read_msgs(host: str, port: int, messages_queue: asyncio.Queue):
    await load_msg_history(out_path, messages_queue)
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    async with OpenConnection(host, port) as (reader, writer):
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
        try:
            while True:
                data = await asyncio.wait_for(reader.readline(), READ_TIMEOUT)
                messages_queue.put_nowait(data.decode())
                await watchdog_queue.put("New message in chat")
                stamped_phrase = add_timestamp(data)
                messages_queue.put_nowait(stamped_phrase)
                await saving_queue.put(stamped_phrase)
                await write_to_disk(data, out_path)
        except (ConnectionRefusedError, ConnectionResetError, ConnectionError) as exc:
            logger.error(exc)
            writer.close()
            await writer.wait_closed()


async def ping(queue: asyncio.Queue):
    while True:
        queue.put_nowait("")
        await asyncio.sleep(PING_TIMEOUT)


async def handle_connection():
    while True:
        try:
            async with create_task_group() as task_group:
                task_group.start_soon(read_msgs, host, port_read, messages_queue)
                task_group.start_soon(send_msgs, host, port_write, sending_queue)
                task_group.start_soon(watch_for_connection, watchdog_queue)
                task_group.start_soon(ping, sending_queue)
        except (ConnectionError, TimeoutError, socket.gaierror):
            logger.debug("Reconnect")
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
            status_updates_queue.put_nowait(gui.NicknameReceived("unknown"))
            await asyncio.sleep(1)


async def watch_for_connection(queue: asyncio.Queue):
    while True:
        try:
            async with timeout(TIMEOUT_CONNECTION) as tm:
                message = await queue.get()
                watchdog_logger.debug(message)
        except asyncio.TimeoutError:
            if tm.expired:
                watchdog_logger.warning(f"{TIMEOUT_CONNECTION}s timeout is elapsed")
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
        default=str(os.getenv("CHAT_HOST", "minechat.dvmn.org")),
        help="Enter host",
    )
    parser.add_argument(
        "-pr",
        "--port_read",
        type=int,
        default=int(os.getenv("PORT_READ", 5000)),
        help="Enter port read",
    )
    parser.add_argument(
        "-pw",
        "--port_write",
        type=int,
        default=int(os.getenv("PORT_WRITE", 5050)),
        help="Enter port write",
    )
    parser.add_argument("-t", "--token", type=str, default=os.getenv("TOKEN"), help="Enter hash token")
    return parser.parse_args()


async def main():
    async with create_task_group() as task_group:
        task_group.start_soon(gui.draw, messages_queue, sending_queue, status_updates_queue)
        task_group.start_soon(load_msg_history, out_path, messages_queue)
        task_group.start_soon(handle_connection)


if __name__ == "__main__":
    load_dotenv()
    parser = argparser()
    host = parser.host or str(os.getenv('HOST', 'minechat.dvmn.org'))
    port_read = parser.port_read or int(os.getenv('PORT_READ', 5000))
    port_write = parser.port_write or int(os.getenv('PORT_WRITE', 5050))
    token = parser.token or str(os.getenv("TOKEN"))
    out_path = parser.path or OUT_PATH

    try:
        asyncio.run(main())
    except InvalidToken:
        logger.debug('Incorrect token. Exit.')
    except (KeyboardInterrupt, TclError, gui.TkAppClosed, asyncio.exceptions.CancelledError):
        logger.debug('The chat is closed. Exit.')
