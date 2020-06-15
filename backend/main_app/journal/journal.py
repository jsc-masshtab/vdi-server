# -*- coding: utf-8 -*-
# import asyncio

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

    def general(self):
        Logging.logger_genaral(self)

    # Не работает с async with!
    # @staticmethod
    # def info(message, **kwargs):
        # TYPE_INFO = 0
        # native_loop = asyncio.get_event_loop()
        # native_loop.create_task(Event.create_event(message, event_type=TYPE_INFO, **kwargs))

    # @staticmethod
    # def warning(message, **kwargs):
        # TYPE_WARNING = 1
        # native_loop = asyncio.get_event_loop()
        # native_loop.create_task(Event.create_event(message, event_type=TYPE_WARNING, **kwargs))

    # @staticmethod
    # def error(message, **kwargs):
        # TYPE_ERROR = 2
        # native_loop = asyncio.get_event_loop()
        # native_loop.create_task(Event.create_event(message, event_type=TYPE_ERROR, **kwargs))

    info = partialmethod(Event.create_event, event_type=TYPE_INFO)
    warning = partialmethod(Event.create_event, event_type=TYPE_WARNING)
    error = partialmethod(Event.create_event, event_type=TYPE_ERROR)
