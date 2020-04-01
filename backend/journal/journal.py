# -*- coding: utf-8 -*-
from functools import partialmethod

from journal.log.logging import Logging
from journal.event.models import Event


class Log:
    TYPE_INFO = 0
    TYPE_WARNING = 1
    TYPE_ERROR = 2

    def debug(self):
        Logging.logger_application_debug(self)

    def name(self):
        Logging.logger_name(self)

    # TODO: @e.gareev сомневаюсь, что это работает. create_event это корутина, без await она не выполнится.
    info = partialmethod(Event.create_event, event_type=TYPE_INFO)
    warning = partialmethod(Event.create_event, event_type=TYPE_WARNING)
    error = partialmethod(Event.create_event, event_type=TYPE_ERROR)
