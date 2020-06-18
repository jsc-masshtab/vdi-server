# -*- coding: utf-8 -*-
from front_ws_api.handlers import VdiFrontWsHandler


ws_event_monitoring_urls = [
    (r'/subscriptions/?', VdiFrontWsHandler),
]
