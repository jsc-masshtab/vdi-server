import pytest
import uuid
import json
from subprocess import Popen, TimeoutExpired
import sys
import asyncio

from async_generator import async_generator, yield_
from graphene import Context

from common.database import start_gino, stop_gino
from common.veil.veil_gino import Role
from common.veil.auth.veil_jwt import encode_jwt

from common.models.controller import Controller
from common.models.vm import Vm
from common.models.auth import Group, User
from common.models.authentication_directory import AuthenticationDirectory, Mapping


from web_app.controller.schema import controller_schema
from web_app.pool.schema import pool_schema
from web_app.tests.utils import execute_scheme

from common.veil.veil_redis import a_redis_wait_for_message, INTERNAL_EVENTS_CHANNEL

from common.log.journal import system_logger


async def get_resources_for_pool_test():
    """На контроллере ищутся оптимальные ресурсы для проведения теста
    """
    # controller
    controllers = await Controller.get_objects()
    if not controllers:
        raise RuntimeError('Нет контроллеров')

    controller = await Controller.get(controllers[0].id)

    # ids are random
    return {'controller_id': controller.id,
            'cluster_id': '6dd44376-0bf5-46b8-8a23-5a1e6fcfe376',
            'node_id': '236d318f-d57e-4f1b-9097-93d69f8782dd',
            'template_id': 'a04ed49b-ea26-4660-8112-833a6b51d0e1',
            'datapool_id': '37df3326-55b9-4af1-91b3-e54df12f24e7'}


def get_test_pool_name():
    """Generate a test pool name"""
    return 'test_pool_{}'.format(str(uuid.uuid4())[:7])


@pytest.fixture
@async_generator
async def fixt_launch_workers():

    ws_listener_worker = Popen([sys.executable, "../../ws_listener_worker/app.py"])
    pool_worker = Popen([sys.executable, "../../pool_worker/app.py", "-do-not-resume-tasks"])

    await yield_()

    def stop_worker(worker):
        worker.terminate()
        try:
            worker.wait(1)
        except TimeoutExpired:
            pass
        worker.kill()

    stop_worker(ws_listener_worker)
    stop_worker(pool_worker)


@pytest.fixture
@async_generator
async def fixt_db():
    """Actual fixture for requests working with db."""

    await start_gino()
    await yield_()
    await stop_gino()


async def get_auth_token():
    """Return JWT token for Admin user.
    Грязный хак в том, что пользователь и пароль при авторизации проверяется раньше.
    Тут напрямую вызывается уже генерация токена."""
    access_token = 'jwt ' + encode_jwt('admin').get('access_token')
    return access_token


async def get_auth_context():
    """Return auth headers in Context for Graphene query execution of protected methods."""
    auth_token = await get_auth_token()
    context = Context()
    context.headers = {'Authorization': auth_token, 'Client-Type': 'PyTest', 'Content-Type': 'application/json'}
    context.remote_ip = '127.0.0.1'
    return context


@pytest.fixture
async def fixt_auth_context():
    """Auth context fixture."""
    return await get_auth_context()


@pytest.fixture
@async_generator
async def fixt_create_automated_pool(fixt_controller):
    """Create an automated pool, yield, remove this pool"""
    # start resources_monitor to receive info  from controller. autopool creation doesnt work without it

    resources = await get_resources_for_pool_test()
    if not resources:
        print('resources not found!')

    qu = '''
            mutation {
                      addDynamicPool(
                        connection_types: [SPICE, RDP],
                        verbose_name: "%s",
                        controller_id: "%s",
                        cluster_id: "%s",
                        node_id: "%s",
                        datapool_id: "%s",
                        template_id: "%s",
                        initial_size: 1,
                        reserve_size: 1,
                        increase_step: 1,
                        total_size: 1,
                        vm_name_template: "vdi-test"), {
                        pool {
                          pool_id,
                          controller{
                            id,
                            verbose_name,
                            address
                          },
                        pool_type,
                        status
                        },
                        ok
                      }
                    }''' % (get_test_pool_name(), resources['controller_id'], resources['cluster_id'],
                            resources['node_id'], resources['datapool_id'], resources['template_id'])
    context = await get_auth_context()
    executed = await execute_scheme(pool_schema, qu, context=context)

    pool_id = executed['addDynamicPool']['pool']['pool_id']

    # Нужно дождаться внутреннего сообщения о создании пула.
    def _check_if_pool_created(redis_message):

        system_logger._debug('_check_if_pool_created: redis_message : ' + str(redis_message))
        try:
            redis_message_data = redis_message['data'].decode()
            redis_message_data_dict = json.loads(redis_message_data)

            if redis_message_data_dict['event'] == 'status_changed':
                return redis_message_data_dict['task_status'] == 'FINISHED'
        except Exception as ex:
            print('_check_if_pool_created ' + str(ex))

        return False

    POOL_CREATION_TIMEOUT = 60  # при подготовке ВМ  несколько раз используются таймауты по 10 секунд,
    # из-за чего даже с тестовым вейлом создание пула длится долго
    is_pool_successfully_created = await a_redis_wait_for_message(INTERNAL_EVENTS_CHANNEL,
                                                                  _check_if_pool_created, POOL_CREATION_TIMEOUT)

    await yield_({
        'id': pool_id,
        'is_pool_successfully_created': is_pool_successfully_created
    })

    # Слип  для обхода проблемы вейла: если создать вм и сразу попытаться удалить, то вываливает что-то типа
    # Entity  (domain) is locked by task  (MultiCreateDomain).']}}
    await asyncio.sleep(2)

    # remove pool
    qu = '''
    mutation {
      removePool(pool_id: "%s", full: true) {
        ok
      }
    }
    ''' % pool_id
    await execute_scheme(pool_schema, qu, context=context)


@pytest.fixture
@async_generator
async def fixt_create_static_pool(fixt_controller):
    """оздается пул, пул удаляется"""
    pool_main_resources = await get_resources_for_pool_test()
    controller_id = pool_main_resources['controller_id']
    cluster_id = pool_main_resources['cluster_id']
    node_id = pool_main_resources['node_id']
    datapool_id = pool_main_resources['datapool_id']
    vm_id = '37df3326-55b9-4af1-91b3-e54df12f24e7'  # random

    # --- create pool ---
    qu = '''
            mutation{addStaticPool(
              verbose_name: "%s",
              controller_id: "%s",
              cluster_id: "%s",
              node_id: "%s",
              datapool_id: "%s",
              vms:[
                {id: "%s",
                  verbose_name: "test_2"}
              ],
              connection_types: [SPICE, RDP],
            ){
              pool {
                pool_id
                node {
                  id
                }
              }
              ok
            }
            }''' % (get_test_pool_name(), controller_id, cluster_id, node_id, datapool_id, vm_id)

    context = await get_auth_context()
    pool_create_res = await execute_scheme(pool_schema, qu, context=context)
    pool_id = pool_create_res['addStaticPool']['pool']['pool_id']
    await yield_({
        'ok': pool_create_res['addStaticPool']['ok'],
        'id': pool_id
    })

    # --- remove pool ---
    qu = '''
    mutation {
      removePool(pool_id: "%s", full: true) {
        ok
      }
    }
    ''' % pool_id
    await execute_scheme(pool_schema, qu, context=context)


@pytest.fixture
def fixt_group(request, event_loop):
    group_name = 'test_group_1'

    async def setup():
        await Group.create(verbose_name=group_name, id="10913d5d-ba7a-4049-88c5-769267a6cbe4",
                           ad_guid="10913d5d-ba7a-4049-88c5-769267a6cbe5")

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Group.delete.where(Group.id == "10913d5d-ba7a-4049-88c5-769267a6cbe4").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_local_group(request, event_loop):
    group_name = 'test_group_2'

    async def setup():
        await Group.create(verbose_name=group_name, id="10913d5d-ba7a-4049-88c5-769267a6cbe3")

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Group.delete.where(Group.id == "10913d5d-ba7a-4049-88c5-769267a6cbe3").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user(request, event_loop):
    """Фикстура учитывает данные фикстуры пула."""
    user_name = 'test_user'
    user_id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    user_password = 'veil'
    creator = 'system'

    async def setup():
        await User.soft_create(username=user_name, id=user_id, password=user_password, creator=creator)

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user_admin(request, event_loop):
    user_name = 'test_user_admin'
    user_id = '10913d5d-ba7a-4049-88c5-769267a6cbe3'
    user_password = 'veil'
    creator = 'admin'

    async def setup():
        await User.soft_create(username=user_name, id=user_id, password=user_password, is_superuser=True, creator=creator)

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user_another_admin(request, event_loop):
    user_name = 'test_user_admin2'
    user_id = '10913d5d-ba7a-4149-88c5-769267a6cbe3'
    user_password = 'veil'
    creator = 'system'

    async def setup():
        await User.soft_create(username=user_name, id=user_id, password=user_password, is_superuser=True, creator=creator)

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user_locked(request, event_loop):
    user_id = '10913d5d-ba7a-4049-88c5-769267a6cbe6'

    async def setup():
        await User.soft_create(username='test_user_locked', id=user_id, is_active=False, password="qwe", creator='system')

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir(request, event_loop):
    id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    verbose_name = 'test_auth_dir'
    directory_url = 'ldap://192.168.11.180'
    domain_name = 'bazalt.team'
    creator = 'system'

    async def setup():
        await AuthenticationDirectory.soft_create(id=id, verbose_name=verbose_name, directory_url=directory_url,
                                                  domain_name=domain_name, creator=creator)
    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(AuthenticationDirectory.id == id).gino.status()
            # TODO: опасное место
            await User.delete.where(User.username == 'ad120').gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir_with_pass(request, event_loop):
    id = '10913d5d-ba7a-4049-88c5-769267a6cbe5'
    verbose_name = 'test_auth_dir'
    directory_url = 'ldap://192.168.11.180'
    domain_name = 'bazalt.team'
    encoded_service_password = 'Bazalt1!'

    async def setup():
        await AuthenticationDirectory.soft_create(id=id,
                                                  verbose_name=verbose_name,
                                                  directory_url=directory_url,
                                                  domain_name=domain_name,
                                                  service_password=encoded_service_password,
                                                  service_username='ad120',
                                                  creator='system')

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(AuthenticationDirectory.id == id).gino.status()
            # TODO: опасное место
            await User.delete.where(User.username == 'ad120').gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir_with_pass_bad(request, event_loop):
    id = '10913d5d-ba7a-4049-88c5-769267a6cbe6'
    verbose_name = 'test_auth_dir'
    directory_url = 'ldap://192.168.11.180'
    domain_name = 'bazalt.team'
    encoded_service_password = 'bad'

    async def setup():
        await AuthenticationDirectory.soft_create(id=id,
                                                  verbose_name=verbose_name,
                                                  directory_url=directory_url,
                                                  domain_name=domain_name,
                                                  service_password=encoded_service_password,
                                                  service_username='bad',
                                                  creator='system')

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(AuthenticationDirectory.id == id).gino.status()
            # TODO: опасное место
            await User.delete.where(User.username == 'ad120').gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_mapping(request, event_loop):
    """Фикстура завязана на фикстуру AD и Групп."""

    auth_dir_id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    group_id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    groups = [group_id]
    mapping_dict = {
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
        'verbose_name': 'test_mapping_fixt',
        'value_type': Mapping.ValueTypes.GROUP,
        'values': ["veil-ad-users"]

    }

    async def setup():
        auth_dir = await AuthenticationDirectory.get(auth_dir_id)
        await auth_dir.add_mapping(mapping=mapping_dict, groups=groups, creator='system')
    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Mapping.delete.where(Mapping.id == mapping_dict['id']).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_group_role(request, event_loop):
    """Фикстура завязана на фикстуру Групп"""

    group_id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'

    async def setup():
        """Подчищать не надо, группа будет удалена и эти записи удалятся каскадом"""
        group = await Group.get(group_id)
        await group.add_role(Role.SECURITY_ADMINISTRATOR, creator='system')
    event_loop.run_until_complete(setup())
    return True


@pytest.fixture
@async_generator
async def fixt_controller():

    controller_ip = '0.0.0.0'

    # add controller
    qu = """
    mutation {
        addController(
            verbose_name: "controller_added_during_test",
            address: "%s",
            description: "controller_added_during_test",
            token: "jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxOTEyOTM3NjExLCJzc28iOmZhbHNlLCJvcmlnX2lhdCI6MTU5ODQ0MTYxMX0.OSRio0EoWA8ZDtvzl3YlaBmdfbI0DQz1RiGAIMCgoX0") {
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

    context = await get_auth_context()
    executed = await execute_scheme(controller_schema, qu, context=context)
    controller_id = executed['addController']['controller']['id']
    print('controller_id ', controller_id, flush=True)
    await yield_({'controller_id': controller_id})

    # remove controller
    qu = """
    mutation {
        removeController(id_: "%s") {
            ok
        }
    }
    """ % controller_id

    executed = await execute_scheme(controller_schema, qu, context=context)
    assert executed['removeController']['ok']


@pytest.fixture
def fixt_vm(request, event_loop):

    id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    verbose_name = 'test_vm'

    async def setup():
        await Vm.create(pool_id=None, template_id=None, created_by_vdi=True, verbose_name=verbose_name, id=id)
    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Vm.delete.where(Vm.id == id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True
