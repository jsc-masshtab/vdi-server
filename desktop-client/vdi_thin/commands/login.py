import time
import logging

from .base import AsyncCallCmd
from ..services.api_session import ApiConnectionError, ApiInvalidServerUrl

LOG = logging.getLogger()


class LoginCommand(AsyncCallCmd):
    @property
    def login_handler(self):
        return self.kwargs["login_handler"]

    def run(self, retry_count=3, retry_interval=3):
        for n in range(retry_count):
            try:
                self.api_session.init_session()
                return self.api_session
            except ApiInvalidServerUrl as e:
                raise e
            except ApiConnectionError:
                time.sleep(retry_interval)
                continue
        raise ApiConnectionError

    def on_finish(self, context, r):
        LOG.debug("finish handler")
        self.app.api_session = r
        self.app.do_main()

    def on_exception(self, context, e):
        LOG.debug("exc handler")
        self.login_handler.set_msg(str(e))
        self.login_handler.normal_state()

    def on_cancel(self, context):
        LOG.debug("cancel handler")
        self.app.do_quit()