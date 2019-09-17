import asyncio


from uvicorn.workers import UvicornWorker
from vdi.main import Vdi


class VdiWorker(Vdi, UvicornWorker):

    def run(self):
        #asyncio.run(self.co())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.co())
        loop.close()


