import argparse
import asyncio
import gui

from os import getenv
from pathlib import Path


OUT_PATH = (Path(__file__).parent / "chat.log").absolute()
HOST_CLIENT = str(getenv("HOST_CLIENT", "188.246.233.198"))
PORT_CLIENT = int(getenv("PORT_CLIENT", 5000))


async def generate_msgs(messages_queue):
    messages_queue.put_nowait('Иван: Привет всем в этом чатике!')
    return messages_queue


async def draw_gui(messages_queue):
    loop = asyncio.get_event_loop()
    # messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    loop.run_until_complete(gui.draw(messages_queue, sending_queue, status_updates_queue))


def get_arguments():
    parser = argparse.ArgumentParser(description="The code run chat.")
    parser.add_argument(
        "-ph", "--path", type=str, default=OUT_PATH, help="Set path to catalog use arguments: '--path'"
    )
    parser.add_argument(
        "-ht", "--host", type=str, default=HOST_CLIENT, help="Enter host use arguments: '--host'"
    )
    parser.add_argument(
        "p", "--port", type=int, default=PORT_CLIENT, help="Enter port use argument: '--port' set number"
    )
    args = parser.parse_args()
    return args.path, args.host, args.port


async def main():

    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    tasks = []
    messages_queue = asyncio.Queue()
    # generate = await generate_msgs(messages_queue)

    for _ in range(5):
        await asyncio.sleep(3)
        tasks.append(generate_msgs(messages_queue))

    await asyncio.gather(*tasks)

    await gui.draw(messages_queue, sending_queue, status_updates_queue)


if __name__ == "__main__":
    # messages_queue = asyncio.Queue()
    # draw_gui(messages_queue)

    asyncio.run(main())


