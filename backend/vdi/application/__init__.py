
from .vars import Request


# def __getattr__(name):
#     if name == 'application':
#         from vdi.application import app, client_routes, admin_routes
#         return app.app
#     raise AttributeError