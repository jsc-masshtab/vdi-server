# -*- coding: utf-8 -*-
from web_app.auth.handlers import AuthHandler, KerberosAuthHandler, LogoutHandler, SettingsHandler, VersionHandler


auth_api_urls = [
    (r"/auth/?", AuthHandler),
    (r"/logout/?", LogoutHandler),
    (r"/version/?", VersionHandler),
    (r"/settings/?", SettingsHandler),
    (r"/sso/?", KerberosAuthHandler),
]
