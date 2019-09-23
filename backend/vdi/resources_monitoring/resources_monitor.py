import asyncio
import websockets

from ..tasks.base import Token

class ResourcesMonitor:

    # ATTRIBUTES
    websocket = None
    running_flag = True
    controller_ip = None
    list_of_subscriptions = ['clusters', 'nodes', 'data-pools', 'domains']

    list_of_observers = []

    # PUBLIC SECTION
    async def start(self, controller_ip):
        self.controller_ip = controller_ip
        await self._connect()

        # receive messages
        while self.running_flag:
            await asyncio.sleep(0)
            try:
                message = await self.websocket.recv()
                await self._on_message_received(message)

            except websockets.ConnectionClosed:
                await self._on_connection_closed()
            except Exception:
                await self._on_error_occurred()

    async def stop(self):
        # stop recv
        self._stop_message_recv()
        # close connection
        if self.websocket:
            await self.websocket.close()

    def subscribe(self, observer):
        self.list_of_observers.append(observer)

    def unsubscribe(self, observer):
        self.list_of_observers.remove(observer)

    # PRIVATE SECTION
    async def _connect(self):
        # create ws connection
        token = await Token(controller_ip=self.controller_ip)
        connect_url = 'ws://{}/ws/?token={}'.format(self.controller_ip, token)
        self.websocket = await websockets.connect(connect_url)

        # subscribe to events on veil
        for subscription_name in self.list_of_subscriptions:
            await self.websocket.send('add /{}/'.format(subscription_name))

    def _stop_message_recv(self):
        self.running_flag = False

    async def _on_message_received(self, message):
        print("WS: {}".format(message))
        #  notify subscribed observers
        for observer in self.list_of_observers:
            observer.on_notified(message)

    async def _on_connection_closed(self):
        print('WS: cconnection closed')
        await self._try_to_recconect()

    async def _on_error_occurred(self):
        print('WS: An error occurred')
        await self._try_to_recconect()

    async def _try_to_recconect(self):
        # if running_flag is raised then try to reconnect
        if self.running_flag:
            await self._connect()

