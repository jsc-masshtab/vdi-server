import socket
#from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async.classy_async import Task, wait

from db.db import db

from . import UrlFetcher, Token, CheckConnection

from vdi.errors import SimpleError, FetchException, NotFound, ControllerNotAccessible


#@dataclass()
class ListClusters(UrlFetcher):

    controller_ip = ''

    def __init__(self, controller_ip: str):
        self.controller_ip = controller_ip

    @cached
    def url(self):
        return 'http://{}/api/clusters/'.format(self.controller_ip)

    async def run(self):
        resp = await super().run()
        return resp['results']


#@dataclass()
class FetchCluster(UrlFetcher):
    controller_ip = ''
    cluster_id = ''

    def __init__(self, controller_ip: str, cluster_id: str):
        self.controller_ip = controller_ip
        self.cluster_id = cluster_id

    @cached
    def url(self):
        return 'http://{}/api/clusters/{}/'.format(self.controller_ip, self.cluster_id)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Кластер не найден") from ex


class FetchDatapool(UrlFetcher):
    controller_ip = ''
    datapool_id = ''

    def __init__(self, controller_ip: str, datapool_id: str):
        self.controller_ip = controller_ip
        self.datapool_id = datapool_id

    @cached
    def url(self):
        return 'http://{}/api/data-pools/{}/'.format(self.controller_ip, self.datapool_id)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Датапул не найден") from ex


class FetchDomain(UrlFetcher):
    controller_ip = ''
    domain_id = ''

    def __init__(self, controller_ip: str, domain_id: str):
        self.controller_ip = controller_ip
        self.domain_id = domain_id

    @cached
    def url(self):
        return 'http://{}/api/domains/{}/'.format(self.controller_ip, self.domain_id)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("ВМ не найдена") from ex


#@dataclass()
class ListNodes(UrlFetcher):

    cluster_id = ''
    controller_ip = ''

    def __init__(self, cluster_id: str, controller_ip: str):
        self.cluster_id = cluster_id
        self.controller_ip = controller_ip

    @cached
    def url(self):
        return 'http://{}/api/nodes/?cluster={}'.format(self.controller_ip, self.cluster_id)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Кластер не найден") from ex

    async def run(self):
        resp = await super().run()
        return resp['results']


#@dataclass()
class FetchNode(UrlFetcher):
    node_id = ''
    controller_ip = ''

    def __init__(self, node_id: str, controller_ip: str):
        self.node_id = node_id
        self.controller_ip = controller_ip

    @cached
    def url(self):
        return 'http://{}/api/nodes/{}/'.format(self.controller_ip, self.node_id)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Узел не найден") from ex

    async def run(self):
        resp = await super().run()
        resp['cluster'] = {
            'id': resp['cluster'],
        }
        return resp


#@dataclass()
class ListDatapools(UrlFetcher):

    controller_ip = ''
    node_id = None
    take_broken = False  # property if datapool is fine

    def __init__(self, controller_ip: str, node_id: str = None, take_broken: bool = False):
        self.controller_ip = controller_ip
        self.node_id = node_id
        self.take_broken = take_broken

    @cached
    def url(self):
        return 'http://{}/api/data-pools/'.format(self.controller_ip)

    async def run(self):
        resp = await super().run()
        if self.node_id is None:
            return resp['results']
        pools = []
        for pool in tuple(resp['results']):
            for node in pool['nodes_connected']:
                if self.take_broken:  # doesnt check status and take broken datapools too
                    if self.node_id and node['id'] == self.node_id:
                        break
                else:
                    if self.node_id and node['id'] == self.node_id and node['connection_status'].upper() == 'SUCCESS':
                        break
            else:
                # pool doesn't include our node
                continue
            pools.append(pool)

        return pools


#@dataclass()
class ValidateResources(Task):
    cluster_id = ''
    node_id = ''
    controller_ip = ''

    def __init__(self, cluster_id: str, node_id: str, controller_ip: str):
        self.cluster_id = cluster_id
        self.node_id = node_id
        self.controller_ip = controller_ip

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


#@dataclass()
class DiscoverControllerIp(Task):
    cluster_id = None
    node_id = None

    def __init__(self, cluster_id: str = None, node_id: str = None):
        self.cluster_id = cluster_id
        self.node_id = node_id

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



#@dataclass()
class DiscoverControllers(Task):
    return_broken = False

    def __init__(self, return_broken: bool = False):
        self.return_broken = return_broken

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
            except ControllerNotAccessible:
                broken.append(d)
            except OSError:
                broken.append(d)
            else:
                connected.append(d)

        if self.return_broken:
            return connected, broken
        return connected


#@dataclass()
class FetchResourcesUsage(UrlFetcher):
    controller_ip = ''
    resource_category_name = ''  # clusters   nodes
    resource_id = ''

    def __init__(self, controller_ip: str, resource_category_name: str, resource_id: str):
        self.controller_ip = controller_ip
        self.resource_category_name = resource_category_name
        self.resource_id = resource_id

    @cached
    def url(self):
        return 'http://{}/api/{}/{}/usage/'.format(self.controller_ip, self.resource_category_name, self.resource_id)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Ресурс не найден") from ex


#@dataclass()
class CheckController(UrlFetcher):
    controller_ip = ''

    def __init__(self, controller_ip: str):
        self.controller_ip = controller_ip

    @cached
    def url(self):
        return 'http://{}/api/controllers/check/'.format(self.controller_ip)
