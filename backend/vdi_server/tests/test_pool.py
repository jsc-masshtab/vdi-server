
from vdi.fixtures import (
    db, image_name, create_template, create_pool, pool_name, pool_settings as fixture_pool_settings,
    conn,
)

from vdi.graphql import schema
from graphql import GraphQLError
from vdi.pool import Pool
from vdi.tasks import resources
from vdi import db

import pytest
import json

import asyncio


@pytest.fixture
def pool_settings(fixture_pool_settings):
    vars = dict(fixture_pool_settings)
    vars['settings']['initial_size'] = 1
    return vars


@pytest.mark.asyncio
async def test_create_pool(create_pool, pool_settings):
    id = create_pool['id']

    qu = """{
      pool(id: %(id)s) {
        settings {
          initial_size
        }
        state {
          running
          available {
            id
          }
        }
      }
    }""" % locals()
    r = await schema.exec(qu)
    assert r['pool']['settings']['initial_size'] == 1
    li = r['pool']['state']['available']
    assert len(li) == 1


@pytest.mark.asyncio
async def test_remove_pool(create_pool, pool_settings):
    pass


@pytest.mark.asyncio
async def test_pools_list(create_pool, pool_settings):
    qu = """{
      pools {
        id
        settings {
          initial_size
          reserve_size
        }
      }
    }""" % locals()
    r = await schema.exec(qu)
    for p in r['pools']:
        assert p['settings']['initial_size']
        assert p['settings']['reserve_size']


#@pytest.mark.asyncio
#async def test_wake_pool(create_pool, pool_settings, conn):
#    pool_id = create_pool['id']
#    ins = await Pool.get_pool(pool_id)
#    vms = await ins.load_vms(conn)
#    Pool.instances.pop(pool_id)
#    ins = await Pool.wake_pool(pool_id)
#    new_vms = await ins.load_vms(conn)
#    assert new_vms == vms


@pytest.mark.asyncio
async def test_create_static_pool():

    from vdi.db import db
    await db.init()

    print('create_static_pool')

    from vdi.tasks.resources import DiscoverController
    controller_ip = await DiscoverController()
    #  choose resources to create vms
    list_of_clusters = await resources.ListClusters(controller_ip=controller_ip)
    print('list_of_clusters', list_of_clusters)
    cluster_id = list_of_clusters[-1]['id']

    list_of_nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
    print('list_of_nodes', list_of_nodes)
    node_id = list_of_nodes[-1]['id']

    list_of_datapools = await resources.ListDatapools(controller_ip=controller_ip, node_id=node_id)
    print('list_of_datapools', list_of_datapools)
    datapool_id = list_of_datapools[0]['id']

    # create 2 vms for test
    from vdi.tasks.vm import CreateDomain
    domain_info_1 = await CreateDomain(verbose_name = 'test_vm_static_pool_1', controller_ip=controller_ip,
                              node_id=node_id)
    domain_info_2 = await CreateDomain(verbose_name='test_vm_static_pool_2', controller_ip=controller_ip,
                                       node_id=node_id)
    print('domain_info_1 id', domain_info_1['id'])

    # create pool
    vm_ids_list = json.dumps([domain_info_1['id'], domain_info_2['id']])
    graphql_str = '''
        mutation {
          addStaticPool(name: "test_pool_static", cluster_id: "%s",
            node_id: "%s", datapool_id: "%s", vm_ids_list: %s) {
            id
          }
        }
        ''' % (cluster_id, node_id, datapool_id, vm_ids_list)

    pool_create_res = await schema.exec(graphql_str)  # ([('addStaticPool', OrderedDict([('id', 88)]))])
    print('pool_create_res', pool_create_res)

    # checks
    if hasattr(pool_create_res, 'errors'):
        assert not pool_create_res.errors

    # remove pool
    pool_id = pool_create_res['addStaticPool']['id']
    remove_pool_mutation = '''
    mutation {
      removePool(id: %i) {
        ok
      }
    }
    ''' % pool_id

    print('remove_pool_mutation', remove_pool_mutation)
    pool_removal_res = await schema.exec(remove_pool_mutation)
    print('pool_removal_res', pool_removal_res)