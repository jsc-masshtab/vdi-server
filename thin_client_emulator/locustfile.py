# -*- coding: utf-8 -*-
# http://docs.locust.io/en/stable/quickstart.html#more-options


import json

from locust import SequentialTaskSet, User, between, task
from locust.clients import HttpSession
from locust.exception import LocustError

from spice_session import SpiceSession

from user_credentials import USER_CREDENTIALS


class ThinClientTaskSet(SequentialTaskSet):

    counter = 0  # Счетчик для использование разных учеток

    def __init__(self, parent):
        super().__init__(parent)
        self.jwt = None
        self.base_headers = None
        self.vdi_username = None
        self.pool_id = None

        # spice data
        self.spice_host = None
        self.spice_port = None
        self.spice_password = None

        self.vm_verbose_name = None

    # override
    def on_start(self):
        # get credentials for auth
        self.vdi_username, password = USER_CREDENTIALS[ThinClientTaskSet.counter]

        if ThinClientTaskSet.counter >= (len(USER_CREDENTIALS) - 1):
            ThinClientTaskSet.counter = 0
        else:
            ThinClientTaskSet.counter += 1

        # login
        body = {"username": self.vdi_username, "password": password}
        headers = {"Content-Type": "application/json"}
        response = self.user.http_client.post(url="/api/auth", data=json.dumps(body), headers=headers)

        # parse to get token
        response_dict = self._get_response_dict(response)

        try:
            self.jwt = response_dict["data"]["access_token"]
            self.base_headers = {"Content-Type": "application/json",
                                "Authorization": "jwt {}".format(self.jwt)}
        except KeyError as ex:
            errors = response_dict.get("errors")
            if errors:
                raise RuntimeError(errors)
            raise ex

    # override
    def on_stop(self):
        self.user.http_client.post(url="/api/logout", data=None, headers=self.base_headers)

    @task
    def task_get_pools(self):
        with self.user.http_client.get(url="/api/client/pools",
                                       data=None,
                                       headers=self.base_headers) as response:
            try:
                response_dict = self._get_response_dict(response)
                self.pool_id = response_dict["data"][0]["id"]
            except Exception as ex:
                response.failure("{}  User: {}".format(str(ex), self.vdi_username))
                raise ex

    @task
    def task_get_vm_from_pool(self):

        with self.user.http_client.post(url="/api/client/pools/{}".format(self.pool_id),
                                        data=None,
                                        headers=self.base_headers,
                                        catch_response=True) as response:
            try:
                if not self.pool_id:
                    raise RuntimeError("User {} is not assigned to any pool or the pool data was not fetched".
                                       format(self.vdi_username))

                response_dict = self._get_response_dict(response)
                # Parse response
                self.spice_host = response_dict["data"]["host"]
                self.spice_port = response_dict["data"]["port"]
                self.spice_password = response_dict["data"]["password"]
                self.vm_verbose_name = response_dict["data"]["vm_verbose_name"]

            except Exception as ex:
                response.failure("{}  User: {}".format(str(ex), self.vdi_username))
                raise ex

    @task
    def connect_to_vm_spice(self):
        """Проверка успешности подключения по Spice."""
        self.user.spice_client.emulate_client(self.spice_host,
                                              self.spice_port,
                                              self.spice_password,
                                              self.vdi_username,
                                              self.vm_verbose_name)

    @staticmethod
    def _get_response_dict(response):
        content_decoded = response.content.decode("utf-8")
        return json.loads(content_decoded)


class ThinClientUser(User):
    """Represents a thin client "user" which is to be spawned and "attack" the system."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.host is None:
            raise LocustError(
                "You must specify the base host."
            )

        # http
        self.http_client = HttpSession(
            base_url=self.host,
            request_event=self.environment.events.request,
            user=self,
        )
        self.http_client.trust_env = False
        self.http_client.verify = False

        # spice
        self.spice_client = SpiceSession()
        self.spice_client.locust_environment = self.environment

    tasks = [ThinClientTaskSet]
    wait_time = between(1, 2)
