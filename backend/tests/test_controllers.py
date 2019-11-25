import pytest

from graphene.test import Client

from controller.schema import controller_schema


def test_add_remove_controller():
    controller_ip = '192.168.6.122'
    client = Client(controller_schema)

    # add controller
    qu = """
    mutation {
        addController(
            verbose_name: "controller_added_during_test",
            address: "%s",
            description: "controller_added_during_test",
            username: "test_vdi_user",
            password: "test_vdi_user",
            ldap_connection: false) {
                ok
                controller
                {
                    id
                    verbose_name
                    description
                    address
                    status
                }
            }
    }
    """ % controller_ip

    executed = client.execute(qu)
    assert executed['addController']['ok']

    controller_id = executed['addController']['controller']['id']

    # remove controller
    qu = """
    mutation {
        removeController(id: "%s") {
            ok
        }
    }
    """ % controller_id

    executed = client.execute(qu)
    assert executed['removeController']['ok']
