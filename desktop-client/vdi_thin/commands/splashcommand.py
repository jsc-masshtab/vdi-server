import time

from .base import AsyncCallCmd


class SplashCommand(AsyncCallCmd):
    def run(self, splash_sleep=1):
        time.sleep(splash_sleep)
