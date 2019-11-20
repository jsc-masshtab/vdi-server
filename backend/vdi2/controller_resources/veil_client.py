# -*- coding: utf-8 -*-
from cached_property import cached_property

from common.veil_client import VeilHttpClient
from common.veil_errors import HttpError, SimpleError

import urllib.parse

from database import get_list_of_values_from_db

from controller.models import Controller


class ResourcesHttpClient(VeilHttpClient):
    """Http resources requests to controller"""

    methods = ['POST', 'GET']

    def __init__(self, controller_ip: str):
        super().__init__(controller_ip)

    @classmethod
    async def create(cls, controller_ip: str):
        """Because of we need async execute db query"""
        self = cls(controller_ip)
        self.controller_uid = await Controller.get_controller_id_by_ip(controller_ip)
        return self

    @cached_property
    def api_url(self):
        return 'http://{}/api/'.format(self.controller_ip)

    async def fetch_resources_usage(self, resource_category_name: str, resource_id: str):
        url = self.api_url + '{}/{}/usage/'.format(resource_category_name, resource_id)
        return await self.fetch_with_response(url=url, method='GET')

    async def fetch_resource(self, resource_category: str, resource_id: str):
        """Get veil resource data"""
        url = self.api_url + '{}/{}/'.format(resource_category, resource_id)
        return await self.fetch_with_response(url=url, method='GET')

    async def fetch_node(self, node_id: str):
        return await self.fetch_resource('nodes', node_id)

    async def fetch_cluster(self, cluster_id: str):
        return await self.fetch_resource('clusters', cluster_id)

    async def fetch_datapool(self, datapool_id: str):
        return await self.fetch_resource('data-pools', datapool_id)

    async def check_controller(self):
        """check if controller accesseble"""
        url = self.api_url + '/controllers/check/'
        await self.fetch(url=url, method='GET')

    # async def discover_controllers(self, return_broken: bool):
    #     """Get controllers data"""
    #     controllers_data = await Controller.query.gino.all()
    #     connected = []
    #     broken = []
    #     for controller_data in controllers_data:
    #         controller_dict = controller_data.__values__
    #         try:
    #             await self.check_controller(controller_ip=controller_dict['address'])
    #         except (HttpError, OSError):
    #             broken.append(controller_dict)
    #         else:
    #             connected.append(controller_dict)
    #
    #     if return_broken:
    #         return connected, broken
    #     return connected

    async def fetch_node_list(self, cluster_id: str = None, ordering: str = None, reversed_order: bool = None):
        custom_url_vars = {'cluster': cluster_id}
        return await self.fetch_resources_list('nodes', ordering, reversed_order, custom_url_vars)

    async def fetch_cluster_list(self, ordering: str = None, reversed_order: bool = None):
        return await self.fetch_resources_list('clusters', ordering, reversed_order)

    async def fetch_datapool_list(self, node_id: str = None, take_broken: bool = False,
                                  ordering: str = None, reversed_order: bool = None):
        datapool_list = await self.fetch_resources_list('data-pools', ordering, reversed_order)

        # todo: looks like code repeat
        # filter by node
        if node_id:
            filtered_datapool_list = []
            for datapool in tuple(datapool_list):
                for node in datapool['nodes_connected']:
                    if node['id'] == node_id:
                        filtered_datapool_list.append(datapool)
                        break
            datapool_list = filtered_datapool_list

        # filter if we dont need broken datapools
        if not take_broken:
            filtered_datapool_list = []
            for datapool in tuple(datapool_list):
                for node in datapool['nodes_connected']:
                    if node['connection_status'].upper() == 'SUCCESS':
                        filtered_datapool_list.append(datapool)
                        break
            datapool_list = filtered_datapool_list

        return datapool_list

    async def fetch_resources_list(self, resource_category: str,
                                   ordering: str = None, reversed_order: bool = None, custom_url_vars: dict = None):
        """Get veil resources data list """
        url = self.api_url + '{}/?'.format(resource_category)

        # apply url vars
        url_vars = {}

        if custom_url_vars:
            url_vars.update(custom_url_vars)

        if ordering:
            order_sign = '-' if reversed_order else ''
            url_vars['ordering'] = order_sign + ordering

        if not url_vars:
            url = url + urllib.parse.urlencode(url_vars)

        resources_list_data = await self.fetch_with_response(url=url, method='GET')
        return resources_list_data['results']


