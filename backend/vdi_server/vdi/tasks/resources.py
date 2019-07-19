import socket
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task, wait

from vdi.db import db

from . import UrlFetcher, Token
from .client import FetchException


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


class ValidationError(Exception):
    pass


@dataclass()
class ValidateResources(Task):
    cluster_id: str
    node_id: str
    controller_ip: str

    async def run(self):
        if self.cluster_id and not self.node_id:
            try:
                await FetchCluster(controller_ip=self.controller_ip, cluster_id=self.cluster_id)
                return True
            except (FetchException, socket.gaierror) as ex:
                return False
        try:
            node = await FetchNode(controller_ip=self.controller_ip, node_id=self.node_id)
        except (FetchException, socket.gaierror) as ex:
            return False
        if node['cluster']['id'] != self.cluster_id:
            raise ValidationError
        return True


class NoControllers(Exception):
    pass


@dataclass()
class DiscoverController(Task):
    cluster_id: str = None
    node_id: str = None

    async def run(self):
        controllers = await ListControllers()
        if not self.cluster_id and not self.node_id:
            [one] = controllers
            return one['ip']
        tasks = {
            co['ip']: ValidateResources(controller_ip=co['ip'], node_id=self.node_id, cluster_id=self.cluster_id)
            for co in controllers
        }
        async for controller_ip, ok in wait(**tasks).items():
            if ok:
                return controller_ip



class ListControllers(Task):

    async def run(self):
        async with db.connect() as conn:
            default = await conn.fetch("SELECT ip FROM default_controller")
            if default:
                [(default,)] = default
            else:
                default = None
            query = "SELECT ip, description from controller"
            items = await conn.fetch(query)
        li = []
        for d in items:
            d = dict(d.items())
            d['default'] = d['ip'] == default
            try:
                await Token(controller_ip=d['ip'])
            except (FetchException, socket.gaierror) as ex:
                continue
            li.append(d)
        return li