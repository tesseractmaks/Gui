import asyncio
import logging

logger = logging.getLogger("main")
logger_handler = logging.StreamHandler()
logger_fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_handler.setFormatter(logger_fmt)
logger.setLevel(logging.DEBUG)
logger.addHandler(logger_handler)

watchdog_logger = logging.getLogger(name="watchdog_logger")
watchdog_handler = logging.StreamHandler()
watchdog_logger_fmt = logging.Formatter(fmt='[%(created)d] Connection is alive. %(message)s')
watchdog_handler.setFormatter(watchdog_logger_fmt)
watchdog_logger.setLevel(logging.DEBUG)
watchdog_logger.addHandler(watchdog_handler)



class OpenConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        return self.reader, self.writer

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.writer.close()
        await self.writer.wait_closed()




