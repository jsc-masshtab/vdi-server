import pytest

from vdi.graphql_api import schema


@pytest.mark.asyncio
async def test_add_remove_controller_old():
    controller_ip = '192.168.6.122'
    # add controller
    qu = """
    mutation {
      addController(ip: "%s", description: "added during test", set_default: false){
        ok
      }
    }
    """ % controller_ip
    res = await schema.exec(qu)
    assert res['addController']['ok']

    # remove controller
    qu = """
    mutation {
      removeController(controller_ip: "%s"){
        ok
      }
    }
    """ % controller_ip
    res = await schema.exec(qu)
    assert res['removeController']['ok']


@pytest.mark.asyncio
async def test_add_remove_controller_new():
    controller_ip = '192.168.6.122'
    # add controller
    qu = """
    mutation {
      addController(verbose_name: "controller_added_by_test",
                  address: "%s",
                  description: "added during test",
                  default: false){
        ok
      }
    }
    """ % controller_ip
    res = await schema.exec(qu)
    assert res['addController']['ok']

    # remove controller
    qu = """
    mutation {
      removeController(controller_ip: "%s"){
        ok
      }
    }
    """ % controller_ip
    res = await schema.exec(qu)
    assert res['removeController']['ok']
