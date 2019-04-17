import time
import logging

from .base import AsyncCallCmd
from ..services.api_session import ApiConnectionError, ApiUnknownError

LOG = logging.getLogger()


class StartVmCommand(AsyncCallCmd):
    def run(self, dp_id, retry_count=5, retry_interval=3):
        job_id = self.retry(retry_count, retry_interval,
                            self.api_session.start_desktop_pool,
                            (dp_id,))
        self.wait_job(job_id)
        connect_data = self.retry(retry_count, retry_interval,
                                  self.api_session.get_connect_url,
                                  (dp_id,))
        return connect_data

    def on_exception(self, context, e):
        LOG.debug("vm_start_ex: {}".format(str(e)))

