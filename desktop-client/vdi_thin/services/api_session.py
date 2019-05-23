import json
import logging
import time
from pprint import pprint
import uuid

import requests
import urllib3

urllib3.disable_warnings()

LOG = logging.getLogger(__name__)


class ApiError(Exception):
    def __str__(self):
        return "Unknown error."


class ApiAuthError(ApiError):
    def __str__(self):
        return _("Can't login with provided username and password.")


class ApiUnknownError(ApiError):
    pass


class ApiConnectionError(ApiError):
    def __str__(self):
        return _("Server unreachable.")


class ApiInvalidServerUrl(ApiConnectionError):
    def __str__(self):
        return _("Invalid server URL")


class ApiSession:
    # def __init__(self, username, password, server_url):
    def __init__(self, username, password, ip, port):
        self.username = username
        self.password = password
        self._api_session = None
        self.verify_ssl = False
        self.timeout = 60
        self.api_url = "http://{ip}".format(ip=ip)
        self.auth_url = self.api_url + ":{port}/auth/".format(port=port)

    def get(self, url, params=None, timeout=None, **kwargs):
        return self._api_call("get", url, timeout=timeout, params=params, **kwargs)

    def post(self, url, data=None, timeout=None, **kwargs):
        return self._api_call("post", url, timeout=timeout, json=data, **kwargs)

    def put(self, url, data=None, timeout=None, **kwargs):
        return self._api_call("put", url, timeout=timeout, json=data, **kwargs)

    def refresh_session_token(self):
        if not self._api_session:
            raise ValueError("self._api_session is empty. You should Call get_api_session() first")
        self._set_jwt_header(self._api_session)
        return self._api_session

    def init_session(self):
        if self._api_session:
            return self._api_session
        else:
            session = requests.Session()
            self._configure_session(session)
            self._api_session = session
            return self._api_session

    def _bad_token(self, resp):
        return resp.status_code == 401

    def _api_call(self, method, *args, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        try:
            session = self.init_session()
            func = getattr(session, method)
            r = func(*args, **kwargs)
            print method, r.status_code
            if self._bad_token(r):
                self.refresh_session_token()
                r = func(*args, **kwargs)
                if not self._bad_token(r):
                    raise ApiAuthError
            else:
                return r

        except (requests.exceptions.URLRequired,
                requests.exceptions.MissingSchema,
                requests.exceptions.InvalidSchema,
                requests.exceptions.InvalidURL):
            raise ApiInvalidServerUrl

        except requests.exceptions.RequestException as e:
            raise ApiConnectionError

    def _configure_session(self, session):
        self._set_jwt_header(session)
        session.verify = self.verify_ssl

    def _set_jwt_header(self, session):
        session.headers.update({"Authorization": "jwt {}".format(self._get_token(session)),
                                "Content-Type": "application/json; charset=utf8"})

    def _get_token(self, session):
        # pprint(session.__dict__)
        data = '{"username": "%s", "password": "%s"}' % (self.username, self.password)
        try:
            response = session.post(self.auth_url,
                                    data=data,
                                    verify=self.verify_ssl,
                                    timeout=self.timeout)
            if response.status_code == 401:
                raise ApiAuthError
            response = json.loads(response.text)
            token = response['access_token']
            # print '- Got token: ', token
            return token
        except (requests.exceptions.URLRequired,
                requests.exceptions.MissingSchema,
                requests.exceptions.InvalidSchema,
                requests.exceptions.InvalidURL):
            raise ApiInvalidServerUrl

        except requests.exceptions.RequestException as e:
            raise ApiConnectionError
        except (KeyError, TypeError, ValueError) as e:
            LOG.exception("unknown error")
            raise ApiUnknownError

    def get_desktop_pools(self):
        r = self.get(self.api_url + "/client/pools")
        r.raise_for_status()
        return r.json()#["results"]

    def start_desktop_pool(self, dp_id):
        # r = self.post("{}{}{}/start/".format(self.api_url, "desktop-pools/", dp_id))
        address = "{}{}{}".format(self.api_url, "/client/pools/", dp_id)
        # print address
        r = self.post(address)
        r.raise_for_status()
        # return str(uuid.UUID(r.json()))
        return r.json()

    def get_job(self, job_id):
        r = self.get("{}{}{}/".format(self.api_url, "jobs/", job_id))
        r.raise_for_status()
        return r.json()

    def get_connect_url(self, dp_id):
        r = self.post("{}{}{}/connect-url/".format(self.api_url, "desktop-pools/", dp_id))
        r.raise_for_status()
        return r.json()
