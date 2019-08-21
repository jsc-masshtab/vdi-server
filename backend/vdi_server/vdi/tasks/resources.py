import socket
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task, wait

from vdi.db import db

from . import UrlFetcher, Token, CheckConnection

from vdi.errors import SimpleError, FetchException, NotFound, ControllerNotAccessible


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

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/clusters/{self.cluster_id}/'

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Кластер не найден") from ex


@dataclass()
class ListNodes(UrlFetcher):

    cluster_id: str
    controller_ip: str

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/nodes/?cluster={self.cluster_id}'

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Кластер не найден") from ex

    async def run(self):
        resp = await super().run()
        return resp['results']


@dataclass()
class FetchNode(UrlFetcher):
    node_id: str
    controller_ip: str

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/nodes/{self.node_id}/'

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Узел не найден") from ex

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
        except (NotFound, socket.gaierror) as ex:
            return False
        if self.cluster_id and node['cluster']['id'] != self.cluster_id:
            return False
        return True


@dataclass()
class DiscoverControllerIp(Task):
    cluster_id: str = None
    node_id: str = None

    async def run(self):
        connected, broken = await DiscoverControllers(return_broken=True)
        if not connected:
            if broken:
                raise SimpleError("Отсутствует подключение к контроллерам")
            raise SimpleError("Нет добавленных контроллеров")
        if not self.cluster_id and not self.node_id:
            if len(connected) > 1:
                raise SimpleError("Multiple controllers")
            [one] = connected
            return one['ip']
        tasks = {
            co['ip']: ValidateResources(controller_ip=co['ip'], node_id=self.node_id, cluster_id=self.cluster_id)
            for co in connected
        }
        async for controller_ip, ok in wait(**tasks).items():
            if ok:
                return controller_ip



@dataclass()
class DiscoverControllers(Task):
    return_broken: bool = False

    async def run(self):
        async with db.connect() as conn:
            default = await conn.fetch("SELECT ip FROM default_controller")
            if default:
                [(default,)] = default
            else:
                default = None
            query = "SELECT ip, description from controller"
            items = await conn.fetch(query)
        connected = []
        broken = []
        for d in items:
            d = dict(d.items())
            d['default'] = d['ip'] == default
            try:
                await CheckConnection(controller_ip=d['ip'])
            except ControllerNotAccessible as ex:
                broken.append(d)
            else:
                connected.append(d)

        if self.return_broken:
            return connected, broken
        return connected


@dataclass()
class FetchResourcesUsage(UrlFetcher):
    controller_ip: str
    resource_category_name: str  # clusters   nodes
    resource_id: str

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/{self.resource_category_name}/{self.resource_id}/usage/'

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Ресурс не найден") from ex


