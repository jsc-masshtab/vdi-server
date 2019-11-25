# -*- coding: utf-8 -*-
from cached_property import cached_property

import urllib.parse

from common.veil_decorators import check_params, prepare_body
from common.veil_client import VeilHttpClient
from controller.models import Controller


class VmHttpClient(VeilHttpClient):
    """Abstract class for Veil ECP connection. Simply non-blocking HTTP(s) fetcher from remote Controller."""

    methods = ['POST', 'GET']

    VALID_ACTIONS = [
        'start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot'
    ]

    def __init__(self, controller_ip: str, token: str, vm_id: str, verbose_name: str = None, template_name: str = None):
        super().__init__(controller_ip, token)
        self.vm_id = vm_id
        self.verbose_name = verbose_name
        self.template_name = template_name

    @classmethod
    async def create(cls, controller_ip: str, vm_id: str, verbose_name: str = None, template_name: str = None):
        """Because of we need async execute db query"""
        token = await Controller.get_token(controller_ip)
        self = cls(controller_ip, token, vm_id, verbose_name, template_name)
        return self

    @property
    def url(self):
        return 'http://{}/api/domains/{}/'.format(self.controller_ip, self.vm_id)

    async def prepare(self):
        """Prepare for the first use: enable remote access & power on"""
        await self.send_action(action='start')
        await self.enable_remote_access()
        return True

    @check_params(action=VALID_ACTIONS)
    async def send_action(self, action: str, body: str = ''):
        """Send remote action for domain on VEIL"""
        url = self.url + action + '/'
        await self.fetch(url=url, method='POST', body=body)

    async def enable_remote_access(self):
        """Enable remote access on remote VM"""
        url = self.url + 'remote-access/'
        await self.fetch(url=url, method='POST', body=dict(remote_access=True))

    async def info(self):
        """Endpoint for receiving information about VMs from a remote controller."""
        response_body = await self.fetch_with_response(url=self.url, method='GET')
        return response_body

    async def copy_vm(self, node_id: str, datapool_id: str, domain_name: str):
        url = 'http://{}/api/domains/multi-create-domain/?async=1'.format(self.controller_ip)
        body = dict(verbose_name=domain_name,
                    node=node_id,
                    datapool=datapool_id,
                    parent=self.vm_id)
        return await self.fetch_with_response(url=url, method='POST', body=body)

    async def fetch_all_vms_list(self, node_id: str = None, ordering: str = None, reversed_order: bool = None):

        url = "http://{}/api/domains/?".format(self.controller_ip)

        # apply url vars
        url_vars = {}

        if node_id:
            url_vars['node'] = node_id

        if ordering:
            order_sign = '-' if reversed_order else ''
            url_vars['ordering'] = order_sign + ordering

        if url_vars:
            url = url + urllib.parse.urlencode(url_vars)
        # request
        resources_list_data = await self.fetch_with_response(url=url, method='GET')
        all_vms_list = resources_list_data['results']

        # # filter bu cluster
        # if cluster_id:
        #     all_vms_list = list(filter(lambda vm: vm['cluster'] == cluster_id, all_vms_list))
        return all_vms_list

    async def fetch_vms_list(self, node_id: str = None, ordering: str = None, reversed_order: bool = None):
        """Fetch lists of vms"""
        all_vms_list = await self.fetch_all_vms_list(node_id, ordering, reversed_order)
        vms_list = [vm for vm in all_vms_list if not vm['template']]
        return vms_list

    async def fetch_templates_list(self, node_id: str = None, ordering: str = None, reversed_order: bool = None):
        """Fetch lists of templates"""
        all_vms_list = await self.fetch_all_vms_list(node_id, ordering, reversed_order)
        vms_list = [vm for vm in all_vms_list if vm['template']]
        return vms_list
