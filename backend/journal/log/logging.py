# -*- coding: utf-8 -*-
# TODO: init_logging перенести в конструктор
# TODO: уровень логов для лога принимать из параметров при запуске приложения

import logging
import sys


class Logging:
    @staticmethod
    def init_logging(access_to_stdout=False):
        if access_to_stdout:
            access_log = logging.getLogger('tornado.access')
            access_log.propagate = False
            access_log.setLevel(logging.INFO)
            stdout_handler = logging.StreamHandler(sys.stdout)
            access_log.addHandler(stdout_handler)

        # Disable query logging.
        logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
        logging.getLogger('gino').setLevel(logging.ERROR)

    def logger_application_debug(self):
        app_log = logging.getLogger('tornado.application')
        app_log.setLevel(logging.DEBUG)
        app_log.debug(self)

    def logger_application_error(self, description):
        app_log = logging.getLogger('tornado.application')
        app_log.setLevel(logging.ERROR)
        msg = '{}\nDescription: {}'.format(self, description)
        if description is None:
            msg = self
        app_log.error(msg)

    def logger_application_info(self, description):
        app_log = logging.getLogger('tornado.application')
        app_log.setLevel(logging.INFO)
        msg = '{}\nDescription: {}'.format(self, description)
        if description is None:
            msg = self
        app_log.info(msg)

    def logger_application_warning(self, description):
        app_log = logging.getLogger('tornado.application')
        app_log.setLevel(logging.WARNING)
        msg = '{}\nDescription: {}'.format(self, description)
        if description is None:
            msg = self
        app_log.warning(msg)

    def logger_name(self):
        name_log = logging.getLogger(__name__)
        name_log.setLevel(logging.INFO)
        name_log.info(self)

    def logger_genaral(self):
        general_log = logging.getLogger('tornado.general')
        general_log.setLevel(logging.WARNING)
        general_log.warning(self)
