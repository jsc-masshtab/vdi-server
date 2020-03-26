# -*- coding: utf-8 -*-
from auth.license.handlers import LicenseHandler


license_api_urls = [
    (r'/license/?', LicenseHandler),
]
