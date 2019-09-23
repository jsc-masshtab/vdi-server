


class SubscriptionHandler:

    # ATTRIBUTES
    websocket = None

    # PUBLIC SECTION
    async def handle(self, websocket):
        self.websocket = websocket
        await websocket.accept()

    def on_notified(self, message):
        pass