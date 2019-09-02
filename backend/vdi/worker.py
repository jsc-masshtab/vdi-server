import asyncio


from uvicorn.workers import UvicornWorker
from vdi.main import Vdi


class VdiWorker(Vdi, UvicornWorker):

    def run(self):
        asyncio.run(self.co())


