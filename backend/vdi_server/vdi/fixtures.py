
import pytest
import json
import uuid

from vdi.tasks.resources import DiscoverControllerIp
from vdi.tasks.base import DiscoverController
from vdi.graphql import schema
from vdi.tasks import resources
from vdi.tasks import vm
from vdi.graphql.pool import RemovePool
from vdi.settings import settings

@pytest.fixture
async def fixt_db():
    from vdi.db import db
    await db.init()
    return db


@pytest.fixture
async def image_name():
    from vdi import prepare
    await prepare.main()
    yield 'image'
    print('image destroy')


@pytest.fixture
async def create_template(fixt_db, image_name):
    qu = '''
    mutation {
      createTemplate(image_name: "%(image_name)s") {
        poolwizard {
          reserve_size
          initial_size
          datapool_id
          node_id
          cluster_id
          controller_ip
          template_id
        }
      }
    }
    ''' % locals()
    r = await schema.exec(qu)
    poolwizard = r['createTemplate']['poolwizard']
    yield poolwizard
    print('destroy vm')
    qu = '''
    mutation {
      dropTemplate(id: "%(template_id)s") {
        ok
      }
    }
    ''' % poolwizard
    await schema.exec(qu)


@pytest.fixture
async def pool_settings(create_template):
    return {
        'settings': create_template,
    }



@pytest.fixture
def pool_name():
    import random, string
    uid = ''.join(
        random.choice(string.ascii_letters) for _ in range(3)
    )
    return f"pool-{uid}"



@pytest.fixture
async def create_pool(create_template, pool_name, pool_settings):
    r = await schema.exec('''
        mutation($settings: PoolSettingsInput) {
          addPool(name: "%(pool_name)s", settings: $settings, block: true) {
            id
          }
        }
        ''' % locals(), pool_settings)
    id = r['addPool']['id']
    yield {
        'id': id,
    }
    print('destroy pool')
    qu = '''
    mutation {
      removePool(id: %(id)s) {
        ok
      }
    }
    ''' % locals()
    await schema.exec(qu)

@pytest.fixture
async def conn():
    from vdi.db import db
    async with db.connect() as c:
        yield c


@pytest.fixture
async def fixt_create_static_pool(fixt_db):

    print('create_static_pool')

    controller_ip = settings['controller_ip'] # await DiscoverController()

    # choose resources to create vms
    list_of_clusters = await resources.ListClusters(controller_ip=controller_ip)
    print('list_of_clusters', list_of_clusters)

    # find cluster with nodes
    cluster_id = next(cluster['id'] for cluster in list_of_clusters if cluster['nodes_count'] != 0)

    list_of_nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
    print('list_of_nodes', list_of_nodes)
    # find active node
    node_id = next(node['id'] for node in list_of_nodes if node['status'] == 'ACTIVE')

    async def create_domain():
        uid = str(uuid.uuid4())[:7]
        domain_info = await vm.CreateDomain(verbose_name=f"test_vm_static_pool-{uid}",
                                            controller_ip=controller_ip, node_id=node_id)
        return domain_info

    domain_info_1 = await create_domain()
    domain_info_2 = await create_domain()
    print('domain_info_1 id', domain_info_1['id'])

    # create pool
    vm_ids_list = json.dumps([domain_info_1['id'], domain_info_2['id']])
    qu = '''
        mutation {
          addStaticPool(name: "test_pool_static", node_id: "", datapool_id: "", cluster_id: "", vm_ids_list: %s) {
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
    yield {
        'id': pool_id,
        'vms': vms
    }

    # remove pool
    await RemovePool.do_remove(pool_id)


@pytest.fixture
async def fixt_create_user(fixt_db):

    username = 'test_user_name'
    password = 'test_user_password'
    remove_pool_mutation = '''
    createUser(username: "%s", password: "%s"){
      ok
    }
    ''' % (username, password)
    user_creation_res = await schema.exec(remove_pool_mutation)

    yield username

    # remove user...

