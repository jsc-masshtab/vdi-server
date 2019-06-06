import json
import uuid
from dataclasses import dataclass
from classy_async import Task

from .base import CONTROLLER_IP, Token
from .client import HttpClient
from .ws import WsConnection

from . import UrlFetcher


from cached_property import cached_property as cached

from pathlib import Path

@dataclass()
class ListClusters(UrlFetcher):

    controller_ip: str

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/clusters/'

    async def run(self):
        resp = await super().run()
        return resp['results']


@dataclass()
class FetchCluster(UrlFetcher):
    controller_ip: str
    cluster_id: str

    def url(self):
        return f'http://{self.controller_ip}/api/clusters/{self.cluster_id}/'



@dataclass()
class ListNodes(UrlFetcher):

    cluster_id: str
    controller_ip: str

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/nodes/?cluster={self.cluster_id}'

    async def run(self):
        resp = await super().run()
        return resp['results']


@dataclass()
class FetchNode(UrlFetcher):
    node_id: str
    controller_ip: str

    def url(self):
        return f'http://{self.controller_ip}/api/nodes/{self.node_id}/'

    async def run(self):
        resp = await super().run()
        resp['cluster'] = {
            'id': resp['cluster'],
        }
        return resp


@dataclass()
class ListDatapools(UrlFetcher):
    controller_ip: str
    node_id: str = None

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/data-pools/'

    async def run(self):
        resp = await super().run()
        if self.node_id is None:
            return resp['results']
        pools = []
        for pool in tuple(resp['results']):
            for node in pool['nodes_connected']:
                if self.node_id and node['id'] == self.node_id and node['connection_status'].upper() == 'SUCCESS':
                    break
            else:
                # pool doesn't include our node
                continue
            pools.append(pool)

        return pools

