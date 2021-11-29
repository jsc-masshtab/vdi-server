import base64
import os
import sys
from abc import abstractmethod
from typing import Awaitable, Optional

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web

# Platform-specific Kerberos requirements
if sys.platform == "win32":
    import kerberos_sspi as kerberos
    import pywintypes

    pywintypes_error = pywintypes.error
else:
    import kerberos

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
        if auth_header and auth_header.startswith("Negotiate"):
            self.auth_negotiate(auth_header, callback)
        elif auth_header and auth_header.startswith("Basic "):
            self.auth_basic(auth_header, callback)

    def auth_negotiate(self, auth_header, callback):
        auth_str = auth_header.split()[1]
        # Initialize Kerberos Context
        context = None
        try:
            result, context = kerberos.authGSSServerInit(self.settings["sso_service"])
            if result is not kerberos.AUTH_GSS_COMPLETE:
                raise tornado.web.HTTPError(500, "Kerberos Init failed")
            result = kerberos.authGSSServerStep(context, auth_str)
            if result is kerberos.AUTH_GSS_COMPLETE:
                gss_string = kerberos.authGSSServerResponse(context)
                self.set_header("WWW-Authenticate", "Negotiate {}".format(gss_string))
            else:    # Fall back to Basic auth
                self.auth_basic(auth_header, callback)
            # NOTE: The user we get from Negotiate is a full UPN (user@REALM)
            user = kerberos.authGSSServerUserName(context)
        except (kerberos.GSSError, pywintypes_error) as e:
            print("Kerberos Error: {}".format(e))
            raise tornado.web.HTTPError(500, "Kerberos Init failed")
        finally:
            if context:
                kerberos.authGSSServerClean(context)
        callback(user)

    def auth_basic(self, auth_header, callback):
        auth_decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, password = auth_decoded.split(":", 1)
        try:
            kerberos.checkPassword(username, password, self.settings["sso_service"], self.settings["sso_realm"])
        except Exception as e:    # Basic auth failed
            if self.settings["debug"]:
                print(e)    # Very useful for debugging Kerberos errors
            return self.authenticate_redirect()
        # NOTE: Basic auth just gives us the username without the @REALM part
        #       so we have to add it:
        user = "{}@{}".format(username, self.settings["sso_realm"])
        callback(user)

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


class KerberosAuthHandler(KerberosAuthMixin):
    def get(self):
        auth_header = self.request.headers.get("Authorization", None)
        if auth_header:
            self.get_authenticated_user(self._on_auth)
            return
        self.authenticate_redirect()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Kerberos auth failed")
        self.set_secure_cookie("user", tornado.escape.json_encode(user))
        print("KerberosAuthHandler user: {}".format(user))   # To see what you get
        next_url = self.get_argument("next", None)    # To redirect properly
        if next_url:
            self.redirect(next_url)
        else:
            self.redirect("/")

    def data_received(self, chunk: bytes):
        super().data_received(chunk)
