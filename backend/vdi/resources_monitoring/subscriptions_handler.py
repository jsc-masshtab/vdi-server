from websockets.exceptions import ConnectionClosed as WsConnectionClosed
import asyncio

from .resources_monitoring_data import ALLOWED_SUBSCRIPTIONS_LIST, SubscriptionCmd

# {"event": "UPDATED", "msg_type": "data", "id": "da318378-2bf8-41de-8227-8392a9fdf42f",
# "object": {"luns_count": 0, "vdisks_count": 0, "tags": [],
# "id": "da318378-2bf8-41de-8227-8392a9fdf42f", "user_power_state": 1, "service_module": false,
# "verbose_name": "test_vm_static_pool-e39bd85", "memory_count": 128, "status": "ACTIVE", "hints": 0,
# "node": {"id": "6c63c7d3-e49c-406b-b2d3-7d8ffbba0941", "verbose_name": "VC-0"}, "vinterfaces_count": 0,
# "cpu_count": 1, "template": false}, "resource": "/domains/"}

class SubscriptionHandler:

    # ATTRIBUTES
    _websocket = None
    _subscriptions = []

    _message_queue = asyncio.Queue(100)
    _send_messages_flag = True
    _send_messages_task = None

    # PUBLIC METHODS
    def start(self):
        # start message sending task
        loop = asyncio.get_event_loop()
        self._send_messages_task = loop.create_task(self._send_messages())

    async def stop(self):
        # stop message sending corutine
        self._send_messages_flag = False
        if self._send_messages_task:
            await self._send_messages_task

    async def handle(self, websocket):
        self._websocket = websocket
        await self._websocket.accept()

        # listening messages from admin client
        while True:
            # receive message ands get text
            try:
                message = await self._websocket.receive()
            except WsConnectionClosed:
                break
            except OSError:
                break
            try:
                received_text = message['text']
            except KeyError:
                continue

            # determine if message contains subscription command ('delete /domains/' for example)
            try:
                subscription_cmd, subscription_source = received_text.split(' ')
            except ValueError:
                continue
            # check if allowed
            if subscription_source not in ALLOWED_SUBSCRIPTIONS_LIST:
                print('SubscriptionHandler: Unknown subscription source')
                continue

            # if 'add' cmd and not subscribed  then subscribe
            if subscription_cmd == SubscriptionCmd.ADD.name and subscription_cmd not in self._subscriptions:
                self._subscriptions.append(subscription_cmd)
            # if 'add' cmd and subscribed then do nothing
            elif subscription_cmd == SubscriptionCmd.ADD.name and subscription_cmd in self._subscriptions:
                print('SubscriptionHandler: already subscribed')
            # if 'delete' cmd and not subscribed  then do nothing
            elif subscription_cmd == SubscriptionCmd.DELETE.name and subscription_cmd not in self._subscriptions:
                print('SubscriptionHandler: not subscribed')
            # if 'delete' cmd and subscribed then unsubscribe
            elif subscription_cmd == SubscriptionCmd.DELETE.name and subscription_cmd in self._subscriptions:
                self._subscriptions.remove(subscription_cmd)

    def on_notified(self, json_message):
        print('SubscriptionHandler: ', json_message)
        try:
            self._message_queue.put_nowait(json_message)
        except asyncio.QueueFull:
            pass

    # PRIVATE METHODS
    async def _send_messages(self):
        # wait for message and send it to front client
        self._send_messages_flag = True
        while self._send_messages_flag:
            await asyncio.sleep(0.1)
            try:
                json_message = self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                continue
            if self._websocket:
                await self._websocket.send_json(json_message)


