# -*- coding: utf-8 -*-
from web_app.front_ws_api.handlers import VdiFrontWsHandler


ws_event_monitoring_urls = [
    (r'/ws/subscriptions/?', VdiFrontWsHandler),
]
