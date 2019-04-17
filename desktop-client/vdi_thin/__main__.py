#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from .app import Application

try:
    # settings.py is in .gitignore
    import settings
except:
    settings = None

app = Application()
app.settings = settings
app.run(sys.argv)


