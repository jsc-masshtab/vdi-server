# Adds higher directory to python modules path.
import sys
sys.path.append(".")
sys.path.append("..")
sys.path.append("...")

import asyncio
from uvicorn import Server, Config

from vdi.settings import settings

from vdi.resources_monitoring.resources_monitor import ResourcesMonitor


class Vdi:

    def get_sanic_task(self):
        from auth_server.sanic_app import app
        port = settings.auth_server['port']
        server = app.create_server(host="0.0.0.0", port=port)  # return_asyncio_server=True
        return asyncio.ensure_future(server)

    def starlette_co(self):
        if self.__class__ is Vdi:
            # standalone use
            from vdi.application.app import app
            port = settings.vdi_server['port']
            config = Config(app, "0.0.0.0", port, log_level="info")
            server = Server(config=config)
            return server.serve(shutdown_servers=False)
        # as gunicorn worker
        self.config.app = self.wsgi
        server = Server(config=self.config)
        return server.serve(sockets=self.sockets, shutdown_servers=False)

    async def co(self):
        loop = asyncio.get_event_loop()

        # start veil resources observer (Надо еще учесть что контроллеров ожет былть несколько!)
        veil_resources_monitor = ResourcesMonitor()
        veil_resources_monitor_task = loop.create_task(veil_resources_monitor.start('192.168.7.250'))

        # start authorization server
        sanic_task = self.get_sanic_task()

        # start VDI server
        starlette_task = loop.create_task(self.starlette_co())
        try:
            # wait on starlette task (vdi server)
            await starlette_task
        finally:
            # finish other tasks
            await veil_resources_monitor.stop()
            await self.cancel_task(veil_resources_monitor_task)
            await self.cancel_task(sanic_task)

    async def cancel_task(self, task):
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Vdi().co())
    loop.close()

if __name__ == '__main__':
    main()
