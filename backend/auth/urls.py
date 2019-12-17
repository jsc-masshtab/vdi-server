# -*- coding: utf-8 -*-
from auth.handlers import AuthHandler, LogoutHandler


auth_api_urls = [
    (r'/auth/?', AuthHandler),
    (r'/logout/?', LogoutHandler),
    # (r'/auth/refresh-token/?', RefreshAuthHandler),
]
