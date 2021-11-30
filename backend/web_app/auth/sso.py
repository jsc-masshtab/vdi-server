import os
from abc import abstractmethod
from typing import Awaitable, Optional

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web

pywintypes_error = OSError


class HeadersAlreadyWrittenException(Exception):
    pass


class KerberosAuthMixin(tornado.web.RequestHandler):
    @abstractmethod
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def initialize(self):
        self.require_setting("sso_realm", "Kerberos/GSSAPI Single Sign-On")
        self.require_setting("sso_service", "Kerberos/GSSAPI Single Sign-On")

    def get_authenticated_user(self, callback):
        keytab = self.settings.get("sso_keytab", None)
        if keytab:
            # The kerberos module does not take a keytab as a parameter when
            # performing authentication but you can still specify it via an
            # environment variable:
            os.environ["KRB5_KTNAME"] = keytab
        auth_header = self.request.headers.get("Authorization", None)
        print(auth_header)

    def authenticate_redirect(self):
        # NOTE: I know this isn't technically a redirect but I wanted to make
        # this process as close as possible to how things work in tornado.auth.
        if self._headers_written:
            raise HeadersAlreadyWrittenException
        self.set_status(401)
        self.add_header("WWW-Authenticate", "Negotiate")
        self.add_header("WWW-Authenticate", "Basic realm={}".format(self.settings["realm"]))
        self.finish()
        return False
