import asyncio
from uvicorn import Server, Config

class Vdi:

    def get_sanic_task(self):
        from auth_server.sanic_app import app
        server = app.create_server(host="0.0.0.0", port=5000, return_asyncio_server=True)
        return asyncio.ensure_future(server)

    def starlette_co(self):
        if self.__class__ is Vdi:
            # standalone use
            from vdi.application.app import app
            config = Config(app, "0.0.0.0", 8000, log_level="info")
            server = Server(config=config)
            return server.serve(shutdown_servers=False)
        # as gunicorn worker

        self.config.app = self.wsgi
        server = Server(config=self.config)
        return server.serve(sockets=self.sockets, shutdown_servers=False)

    async def co(self):
        sanic_task = self.get_sanic_task()
        starlette_task = asyncio.create_task(self.starlette_co())
        try:
            await starlette_task
        finally:
            await self._Vdi__cancel(sanic_task)

    async def __cancel(self, task):
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    asyncio.run(Vdi().co())