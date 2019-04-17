import time

from .base import AsyncCallCmd
from ..services.api_session import ApiConnectionError, ApiInvalidServerUrl


class LoadVms(AsyncCallCmd):
    def run(self):
        return self.api_session.get_desktop_pools()

