# -*- coding: utf-8 -*-
from auth.handlers import AuthHandler


auth_urls = [
    (r'/auth/?', AuthHandler),  # client url
]
