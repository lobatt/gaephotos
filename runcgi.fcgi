#!/usr/bin/env python
#coding=utf-8

import os, sys

path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)
apps_dir = os.path.join(path, 'apps')

from flup.server.fcgi import WSGIServer
from uliweb.manage import make_application
app = make_application(apps_dir=apps_dir)
WSGIServer(app).run()
