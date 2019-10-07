import asyncio
import pytest
import json
import uuid
from async_generator import async_generator, yield_, asynccontextmanager

from vdi.tasks.resources import DiscoverControllers
from vdi.tasks import resources
from vdi.tasks import vm

from vdi.graphql_api import schema
from vdi.graphql_api.pool import RemovePool

from vdi.prepare import get_most_appropriate_controller
from vdi import prepare

from db.db import db


async def get_resources_for_static_pool():
    # get the best controller
    controller_ip = await get_most_appropriate_controller()
    print('controller_ip', controller_ip)

    # find cluster with nodes
    list_of_clusters = await resources.ListClusters(controller_ip=controller_ip)
    print('list_of_clusters', list_of_clusters)
    try:
        cluster_id = next(cluster['id'] for cluster in list_of_clusters if cluster['nodes_count'] != 0)
    except StopIteration:
        raise RuntimeError('Нет кластеров содержащих серверы')

    # find active node
    list_of_nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
    print('list_of_nodes', list_of_nodes)
    try:
        node_id = next(node['id'] for node in list_of_nodes if node['status'] == 'ACTIVE')
    except StopIteration:
        raise RuntimeError('Нет активных серверов на кластере {}'.format(cluster_id))

    return {'controller_ip': controller_ip, 'cluster_id': cluster_id, 'node_id': node_id}


async def get_resources_for_automated_pool():
    # controller
    controller_ip = await get_most_appropriate_controller()

    clusters = await resources.ListClusters(controller_ip=controller_ip)
    if not clusters:
        raise RuntimeError('На контроллере {} нет кластеров'.format(controller_ip))
    templates = await vm.ListTemplates(controller_ip=controller_ip)
    if not templates:
        raise RuntimeError('На контроллере {} нет шаблонов'.format(controller_ip))

    # select appropriate template_id and node_id
    # node must be active and has a template
    for cluster in clusters:
        nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster['id'])
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
                    datapools = await resources.ListDatapools(controller_ip=controller_ip, node_id=node['id'])
                    try:
                        datapool_id = next(datapool['id'] for datapool in datapools if datapool['status'] == 'ACTIVE')
                    except StopIteration: # No active datapools
                        continue

                    return {'controller_ip': controller_ip, 'cluster_id': cluster['id'],
                            'node_id': node['id'], 'template_id': template_id, 'datapool_id': datapool_id}

    raise RuntimeError('Подходящие ресурсы не найдены')


@pytest.fixture
async def fixt_db():

    await db.get_pool()
    return db


@pytest.fixture
@async_generator
async def fixt_create_automated_pool():
    print('create_static_pool')

    resources = await get_resources_for_automated_pool()

    res = await schema.exec('''
        mutation {
          addPool(name: "test_auto_pool", controller_ip: "%s", cluster_id: "%s", node_id: "%s",
               datapool_id: "%s", template_id: "%s", initial_size: 1, reserve_size: 1, total_size: 3) {
            desktop_pool_type
            id
          }
        }
        ''' % (resources['controller_ip'], resources['cluster_id'], resources['node_id'],
               resources['datapool_id'], resources['template_id'])
    )

    pool_id = res['addPool']['id']
    await yield_({
        'id': pool_id,
    })

    print('destroy pool')
    # remove pool
    await asyncio.sleep(3) # Даем вейлу время на создание машин
    await RemovePool.do_remove(pool_id)
    # qu = '''
    # mutation {
    #   removePool(id: %(id)s) {
    #     ok
    #   }
    # }
    # ''' % locals()
    # await schema.exec(qu)


@pytest.fixture
@async_generator
async def conn():
    async with db.connect() as c:
        await yield_(c)


@pytest.fixture
@async_generator
async def fixt_create_static_pool(fixt_db):
    print('create_static_pool')
    pool_main_resources = await get_resources_for_static_pool()
    controller_ip = pool_main_resources['controller_ip']
    node_id = pool_main_resources['node_id']

    async def create_domain():
        uid = str(uuid.uuid4())[:7]
        domain_info = await vm.CreateDomain(verbose_name="test_vm_static_pool-{}".format(uid),
                                            controller_ip=controller_ip, node_id=node_id)
        return domain_info

    domain_info_1 = await create_domain()
    domain_info_2 = await create_domain()
    print('domain_info_1 id', domain_info_1['id'])

    # create pool
    vm_ids_list = json.dumps([domain_info_1['id'], domain_info_2['id']])
    qu = '''
        mutation {
          addStaticPool(name: "test_pool_static", vm_ids_list: %s) {
            id
            vms {
              id
            }
          }
        }
        ''' % vm_ids_list

    pool_create_res = await schema.exec(qu)  # ([('addStaticPool', OrderedDict([('id', 88)]))])
    print('pool_create_res', pool_create_res)

    pool_id = pool_create_res['addStaticPool']['id']
    vms = pool_create_res['addStaticPool']['vms']
    await yield_({
        'id': pool_id,
        'vms': vms
    })

    # remove pool
    await RemovePool.do_remove(pool_id)

    # as in static pool VMs are not deleted automaticlly so we delete them manually
    for single_vm in vms:
        await vm.DropDomain(id=single_vm['id'], controller_ip=controller_ip)


@pytest.fixture
@async_generator
async def fixt_create_user(fixt_db):

    username = 'test_user_name'
    password = 'test_user_password'
    remove_pool_mutation = '''
    createUser(username: "%s", password: "%s"){
      ok
    }
    ''' % (username, password)
    user_creation_res = await schema.exec(remove_pool_mutation)

    await yield_(username)

    # remove user...


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
