# -*- coding: utf-8 -*-

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

    def logger_application_error(self):
        app_log = logging.getLogger('tornado.application')
        app_log.setLevel(logging.ERROR)
        app_log.error(self)

    def logger_application_info(self):
        app_log = logging.getLogger('tornado.application')
        app_log.setLevel(logging.INFO)
        app_log.info(self)

    def logger_application_warning(self):
        app_log = logging.getLogger('tornado.application')
        app_log.setLevel(logging.WARNING)
        app_log.warning(self)

    def logger_name(self):
        name_log = logging.getLogger(__name__)
        name_log.setLevel(logging.INFO)
        name_log.info(self)
