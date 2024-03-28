import asyncio
import logging
logging.basicConfig(format='%(levelname)s:%(module)s:%(lineno)s:%(message)s', level=logging.DEBUG)
sender_log = logging.getLogger("sender")
reader_log = logging.getLogger("reader")


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




