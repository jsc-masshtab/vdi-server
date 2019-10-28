# -*- coding: utf-8 -*-
from tornado import gen
from cached_property import cached_property

from common.veil_decorators import check_params
from common.veil_client import VeilHttpClient


class VmHttpClient(VeilHttpClient):
    """Abstract class for Veil ECP connection. Simply non-blocking HTTP(s) fetcher from remote Controller."""

    methods = ['POST', 'GET']

    VALID_ACTIONS = [
        'start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot'
    ]

    def __init__(self, controller_ip: str, vm_id: str):
        super().__init__()
        self.controller_ip = controller_ip
        self.vm_id = vm_id

    @cached_property
    def url(self):
        return "http://{}/api/domains/{}/".format(self.controller_ip, self.vm_id)

    @gen.coroutine
    def prepare(self):
        """Prepare for the first use: enable remote access & power on"""
        yield self.send_action('start')
        yield self.enable_remote_access()
        return True

    @check_params
    @gen.coroutine
    def send_action(self, action: str):
        """Send remote action for domain on VEIL"""
        url = self.url + action + '/'
        yield self.fetch(url=url, method='POST')

    @gen.coroutine
    def enable_remote_access(self):
        """Enable remote access on remote VM"""
        url = self.url + 'remote-access/'
        yield self.fetch(url=url, method='POST', body=dict(remote_access=True))

    @gen.coroutine
    def info(self):
        """Endpoint for receiving information about VMs from a remote controller."""
        response_body = yield self.fetch_with_response(url=self.url, method='GET')
        return response_body

