# -*- coding: utf-8 -*-
from resources_monitoring.handlers import VdiFrontWebSocket


ws_event_monitoring_urls = [
    (r'/subscriptions/?', VdiFrontWebSocket)
]
