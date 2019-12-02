# -*- coding: utf-8 -*-
from auth.handlers import AuthHandler


auth_api_urls = [
    (r'/auth/?', AuthHandler),
    # (r'/auth/refresh-token/?', RefreshAuthHandler),
]
