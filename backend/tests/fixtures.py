import asyncio
import pytest
import json
import uuid
from async_generator import async_generator, yield_, asynccontextmanager

from database import db
from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST, WS_PING_INTERVAL, WS_PING_TIMEOUT

from controller.models import Controller
from controller_resources.veil_client import ResourcesHttpClient

from vm.veil_client import VmHttpClient
from vm.models import Vm

from pool.schema import pool_schema

from utils import execute_scheme

from resources_monitoring.resources_monitor_manager import resources_monitor_manager


async def get_resources_for_static_pool():
    # get the best controller
    controllers_addresses = await Controller.get_controllers_addresses()
    if not controllers_addresses:
        raise RuntimeError('Нет контроллеров')

    controller_ip = controllers_addresses[0]
    print('controller_ip', controller_ip)

    # find cluster with nodes
    resources_http_client = await ResourcesHttpClient.create(controller_ip)
    list_of_clusters = await resources_http_client.fetch_cluster_list()
    print('list_of_clusters', list_of_clusters)
    try:
        cluster_id = next(cluster['id'] for cluster in list_of_clusters if cluster['nodes_count'] != 0)
    except StopIteration:
        raise RuntimeError('Нет кластеров содержащих серверы')

    # find active node
    resources_http_client = await ResourcesHttpClient.create(controller_ip)
    list_of_nodes = await resources_http_client.fetch_node_list(cluster_id)
    print('list_of_nodes', list_of_nodes)
    try:
        node_id = next(node['id'] for node in list_of_nodes if node['status'] == 'ACTIVE')
    except StopIteration:
        raise RuntimeError('Нет активных серверов на кластере {}'.format(cluster_id))

    return {'controller_ip': controller_ip, 'cluster_id': cluster_id, 'node_id': node_id}


async def get_resources_for_automated_pool():
    # controller
    controllers_addresses = await Controller.get_controllers_addresses()
    if not controllers_addresses:
        raise RuntimeError('Нет контроллеров')

    controller_ip = controllers_addresses[0]
    print('controller_ip', controller_ip)

    resources_http_client = await ResourcesHttpClient.create(controller_ip)
    clusters = await resources_http_client.fetch_cluster_list()
    if not clusters:
        raise RuntimeError('На контроллере {} нет кластеров'.format(controller_ip))
    vm_http_client = await VmHttpClient.create(controller_ip, '')
    templates = await vm_http_client.fetch_templates_list()
    if not templates:
        raise RuntimeError('На контроллере {} нет шаблонов'.format(controller_ip))

    # select appropriate template_id and node_id
    # node must be active and has a template
    for cluster in clusters:
        resources_http_client = await ResourcesHttpClient.create(controller_ip)
        nodes = await resources_http_client.fetch_node_list(cluster['id'])
        if not nodes:
            continue

        for node in nodes:
            if node['status'] == 'ACTIVE':
                # check if node has template
                try:
                    template_id = next(template['id'] for template in templates
                                       if template['node']['id'] == node['id'])
                except StopIteration: # node doesnt have template
                    continue
                else: # template found
                    # find active datapool
                    resources_http_client = await ResourcesHttpClient.create(controller_ip)
                    datapools = await resources_http_client.fetch_datapool_list(node_id=node['id'])
                    try:
                        datapool_id = next(datapool['id'] for datapool in datapools if datapool['status'] == 'ACTIVE')
                    except StopIteration: # No active datapools
                        continue

                    return {'controller_ip': controller_ip, 'cluster_id': cluster['id'],
                            'node_id': node['id'], 'template_id': template_id, 'datapool_id': datapool_id}

    raise RuntimeError('Подходящие ресурсы не найдены')


@pytest.fixture
async def fixt_db():
    await db.set_bind('postgresql://localhost/vdi', host=DB_HOST,
                      port=DB_PORT,
                      user=DB_USER,
                      password=DB_PASS)


@pytest.fixture
@async_generator
async def fixt_create_automated_pool():

    # start resources_monitor to receive info  from controller. autopool creation doesnt work without it
    await resources_monitor_manager.start()

    resources = await get_resources_for_automated_pool()

    test_pool_name = 'test_pool_{}'.format(str(uuid.uuid4())[:7])
    qu = '''
        mutation {
            addDynamicPool(verbose_name: "%s", controller_ip: "%s", 
                           cluster_id: "%s", node_id: "%s", datapool_id: "%s", template_id: "%s",
                           initial_size: 1, total_size: 2, max_amount_of_create_attempts: 10){
                    ok
                    pool{
                        pool_id
                        pool_type
                    }
            }
        }
        ''' % (test_pool_name, resources['controller_ip'], resources['cluster_id'], resources['node_id'],
               resources['datapool_id'], resources['template_id'])

    executed = await execute_scheme(pool_schema, qu)

    pool_id = executed['addDynamicPool']['pool']['pool_id']
    await yield_({
        'id': pool_id,
    })

    # remove pool
    qu = '''
    mutation {
      removePool(pool_id: "%s") {
        ok
      }
    }
    ''' % pool_id
    await execute_scheme(pool_schema, qu)

    # stop monitor
    await resources_monitor_manager.stop()


# @pytest.fixture
# @async_generator
# async def fixt_create_static_pool(fixt_db):
#     print('create_static_pool')
#     pool_main_resources = await get_resources_for_static_pool()
#     controller_ip = pool_main_resources['controller_ip']
#     node_id = pool_main_resources['node_id']
#
#     async def create_domain():
#         test_domain_name = 'domain_name_{}'.format(str(uuid.uuid4())[:7])
#         # domain_info = await vm.CreateDomain(verbose_name=test_domain_name,
#         #                                     controller_ip=controller_ip, node_id=node_id)
#         params = {
#             'verbose_name': test_domain_name,
#             'name_template': '',
#             'domain_id': str(self.template_id),
#             'datapool_id': str(self.datapool_id),  # because of UUID
#             'controller_ip':controller_ip,
#             'node_id': node_id,
#         }
#
#         return domain_info
#
#     domain_info_1 = await create_domain()
#     domain_info_2 = await create_domain()
#     print('domain_info_1 id', domain_info_1['id'])
#
#     # create pool
#     vm_ids_list = json.dumps([domain_info_1['id'], domain_info_2['id']])
#     qu = '''
#         mutation {
#           addStaticPool(name: "test_pool_static", vm_ids_list: %s) {
#             id
#             vms {
#               id
#             }
#           }
#         }
#         ''' % vm_ids_list
#
#     pool_create_res = await schema.exec(qu)  # ([('addStaticPool', OrderedDict([('id', 88)]))])
#     print('pool_create_res', pool_create_res)
#
#     pool_id = pool_create_res['addStaticPool']['id']
#     vms = pool_create_res['addStaticPool']['vms']
#     await yield_({
#         'id': pool_id,
#         'vms': vms
#     })
#
#     # remove pool
#     await RemovePool.do_remove(pool_id)
#
#     # as in static pool VMs are not deleted automaticlly so we delete them manually
#     for single_vm in vms:
#         await vm.DropDomain(id=single_vm['id'], controller_ip=controller_ip)


@pytest.fixture
@async_generator
async def fixt_create_user(fixt_db):

    username = 'test_user_name'
    password = 'test_user_password'

    # since we cant remove users so check if the user already exists
    qu = '''
    {
    users{    
      username  
    }
    }
    '''
    res = await schema.exec(qu)
    users = res['users']

    # check if already exists and create user
    user_names = [user['username'] for user in users]
    if username not in user_names:
        qu = '''
        mutation {
        createUser(username: "%s", password: "%s", email: "email"){
          ok
        }
        }
        ''' % (username, password)
        await schema.exec(qu)

    await yield_({
        'username': username,
        'password': password
    })


@pytest.fixture
@async_generator
async def fixt_entitle_user_to_pool(fixt_create_static_pool):

    pool_id = fixt_create_static_pool['id']

    # entitle user to pool
    user_name = "admin"
    qu = '''
    mutation {
      entitleUsersToPool(pool_id: %i, entitled_users: ["%s"]) {
        ok
      }
    }
    ''' % (pool_id, user_name)
    res = await schema.exec(qu)
    print('test_res', res)

    await yield_({
        'pool_id': pool_id,
        'ok': res['entitleUsersToPool']['ok']
    })

    # remove entitlement
    qu = '''
    mutation {
    removeUserEntitlementsFromPool(pool_id: %i, entitled_users: ["%s"]
      free_assigned_vms: true
    ) {
    freed {
      id
    }
    }
    }
    ''' % (pool_id, user_name)
    res = await schema.exec(qu)
