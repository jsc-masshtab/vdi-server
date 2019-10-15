from websockets.exceptions import ConnectionClosed as WsConnectionClosed
import asyncio
import json

from .resources_monitoring_data import VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST, SubscriptionCmd


class SubscriptionHandler:

    def __init__(self):
        self._websocket = None
        self._subscriptions = []
        self._message_queue = asyncio.Queue(100)  # 100 - max queue size
        self._send_messages_flag = True
        self._send_messages_task = None

    def __del__(self):
        print(__class__.__name__, ' In destructor')

    # PUBLIC METHODS
    async def handle(self, websocket):
        self._start_message_sending()
        try:
            await self._process_subscriptions(websocket)
        except:
            pass
        await self._stop_message_sending()

    def on_notified(self, json_message):
        """
        invoked by ResourcesMonitor when message received
        :param json_message:
        :return:
        """
        print(__class__.__name__, json_message)
        try:
            self._message_queue.put_nowait(json_message)
        except asyncio.QueueFull:
            pass

    def get_subscriptions(self):
        return self._subscriptions

    # PRIVATE METHODS
    def _start_message_sending(self):
        # start message sending task
        loop = asyncio.get_event_loop()
        self._send_messages_task = loop.create_task(self._send_messages())

    async def _stop_message_sending(self):
        # stop message sending corutine
        self._send_messages_flag = False
        if self._send_messages_task:
            await self._send_messages_task

    async def _process_subscriptions(self, websocket):
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

            response_dict = {'msg_type': 'control', 'error': False}
            # determine if message contains subscription command ('delete /domains/' for example)
            try:
                subscription_cmd, subscription_source = received_text.split(' ')
                response_dict['msg'] = subscription_cmd
                response_dict['resource'] = subscription_source
            except ValueError:
                response_dict['error'] = True
                await self._dump_dict_and_send(response_dict)
                continue
            # check if allowed
            if subscription_source not in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
                print(__class__.__name__, ' Unknown subscription source')
                response_dict['error'] = True
                await self._dump_dict_and_send(response_dict)
                continue
            print('Test Length', len(self._subscriptions))
            # if 'add' cmd and not subscribed  then subscribe
            if subscription_cmd == SubscriptionCmd.add and subscription_source not in self._subscriptions:
                self._subscriptions.append(subscription_source)
                response_dict['error'] = False
            # if 'add' cmd and subscribed then do nothing
            elif subscription_cmd == SubscriptionCmd.add and subscription_source in self._subscriptions:
                print(__class__.__name__, 'already subscribed')
                response_dict['error'] = True
            # if 'delete' cmd and not subscribed  then do nothing
            elif subscription_cmd == SubscriptionCmd.delete and subscription_source not in self._subscriptions:
                print(__class__.__name__, 'not subscribed')
                response_dict['error'] = True
            # if 'delete' cmd and subscribed then unsubscribe
            elif subscription_cmd == SubscriptionCmd.delete and subscription_source in self._subscriptions:
                self._subscriptions.remove(subscription_source)
                response_dict['error'] = False

            # send response
            await self._dump_dict_and_send(response_dict)

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

    async def _dump_dict_and_send(self, dictionary):
        await self._websocket.send_json(dictionary)


