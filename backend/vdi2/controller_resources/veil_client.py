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

    @cached_property
    def based_url(self):
        return 'http://{}/api/'.format(self.controller_ip)

    async def fetch_resources_usage(self, resource_category_name: str, resource_id: str):
        url = self.based_url + '{}/{}/usage/'.format(resource_category_name, resource_id)
        return await self.fetch_with_response(url=url, method='GET')

    async def fetch_resource(self, resource_category: str, resource_id: str, controller_ip: str = None):
        """Get veil resource data"""
        # use provided controller
        if controller_ip:
            url = 'http://{}/api/{}/{}/'.format(controller_ip, resource_category, resource_id)
            return await self.fetch_with_response(url=url, method='GET')
        # use self.controller_ip
        elif self.controller_ip:
            url = self.based_url + '{}/{}/'.format(resource_category, resource_id)
            return await self.fetch_with_response(url=url, method='GET')
        # determine controller
        else:
            connected_controllers = await self.discover_controllers(return_broken=False)
            for controller in connected_controllers:
                try:
                    resource_data = await self.fetch_resource(resource_category, resource_id, controller['address'])
                    return {'resource_data': resource_data,
                            'controller_address': controller['address']}
                except (HttpError, OSError):
                    continue
            raise SimpleError('Не удалось определить ip контроллера по id ресурса')

    async def fetch_node(self, node_id: str, controller_ip: str = None):
        return await self.fetch_resource('nodes', node_id, controller_ip)

    async def fetch_cluster(self, cluster_id: str, controller_ip: str = None):
        return await self.fetch_resource('clusters', cluster_id, controller_ip)

    async def fetch_datapool(self, datapool_id: str, controller_ip: str = None):
        return await self.fetch_resource('data-pools', datapool_id, controller_ip)

    async def check_controller(self, controller_ip: str):
        """check if controller accesseble"""
        url = 'http://{}/api/controllers/check/'.format(controller_ip)
        await self.fetch(url=url, method='GET')

    async def discover_controllers(self, return_broken: bool):
        """Get controllers data"""
        controllers_data = await Controller.query.gino.all()
        connected = []
        broken = []
        for controller_data in controllers_data:
            controller_dict = controller_data.__values__
            try:
                await self.check_controller(controller_ip=controller_dict['address'])
            except (HttpError, OSError):
                broken.append(controller_dict)
            else:
                connected.append(controller_dict)

        if return_broken:
            return connected, broken
        return connected

    async def fetch_node_list(self, controller_ip: str, cluster_id: str = None,
                              ordering: str = None, reversed_order: bool = None):
        custom_url_vars = {'cluster': cluster_id}
        return await self.fetch_resources_list('nodes', controller_ip, ordering, reversed_order, custom_url_vars)

    async def fetch_cluster_list(self, controller_ip: str,
                                 ordering: str = None, reversed_order: bool = None):
        return await self.fetch_resources_list('clusters', controller_ip, ordering, reversed_order)

    async def fetch_datapool_list(self, controller_ip: str, node_id: str = None, take_broken: bool = False,
                                  ordering: str = None, reversed_order: bool = None):
        datapool_list = await self.fetch_resources_list('data-pools', controller_ip, ordering, reversed_order)

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

    async def fetch_resources_list(self, resource_category: str, controller_ip: str,
                                   ordering: str = None, reversed_order: bool = None, custom_url_vars: dict = None):
        """Get veil resources data list """
        url = 'http://{}/api/{}/?'.format(controller_ip, resource_category)

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


