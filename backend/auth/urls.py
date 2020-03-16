# -*- coding: utf-8 -*-
from auth.handlers import AuthHandler, LogoutHandler, VersionHandler


auth_api_urls = [
    (r'/auth/?', AuthHandler),
    (r'/logout/?', LogoutHandler),
    (r'/version/?', VersionHandler)
]
