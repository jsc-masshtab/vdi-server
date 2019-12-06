# -*- coding: utf-8 -*-
from resources_monitoring.handlers import VdiFrontWsHandler


ws_event_monitoring_urls = [
    (r'/subscriptions/?', VdiFrontWsHandler),
]
