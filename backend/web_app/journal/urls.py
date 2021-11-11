# -*- coding: utf-8 -*-
from web_app.journal.handlers import GetStatisticsReport

journal_api_urls = [
    (r"/statistics_report/?", GetStatisticsReport),
]
