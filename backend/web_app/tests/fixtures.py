import pytest
import uuid
import json
from subprocess import Popen, TimeoutExpired
import sys
import asyncio

from async_generator import async_generator, yield_
from graphene import Context

from web_app.app import start_gino, stop_gino
from common.settings import VEIL_WS_MAX_TIME_TO_WAIT
from common.veil.veil_gino import Role, Status
from common.veil.auth.veil_jwt import encode_jwt
# from common.veil.auth import fernet_crypto

from common.models.controller import Controller
# from controller_resources.veil_client import ResourcesHttpClient

# from web_app.vm.veil_client import VmHttpClient
from common.models.vm import Vm

from web_app.pool.schema import pool_schema

from common.models.auth import Group, User
from common.models.authentication_directory import AuthenticationDirectory, Mapping

from web_app.tests.utils import execute_scheme

# from front_ws_api.subscription_sources import EVENTS_SUBSCRIPTION

from common.veil.veil_redis import a_redis_wait_for_message, INTERNAL_EVENTS_CHANNEL, WS_MONITOR_CHANNEL_OUT, \
    send_cmd_to_ws_monitor, WsMonitorCmd

from common.log.journal import system_logger


async def get_resources_static_pool_test():
    """На контроллере ищутся оптимальные ресурсы для проведения теста
    Альтернативы:
    1)Держать приготовленный контроллер специально для тестов,
    на котором уже гарантировано присутствуют нужные ресурсы
    2)На контроллере при каждом тесте создавать/удалять требуемые ресурсы (это может увеличить время тестов)
    """
    # controller
    controllers_addresses = await Controller.get_addresses()
    if not controllers_addresses:
        raise RuntimeError('Нет контроллеров')

    controller_ip = controllers_addresses[0]
    resources_http_client = await ResourcesHttpClient.create(controller_ip)  # noqa
    clusters = await resources_http_client.fetch_cluster_list()
    if not clusters:
        raise RuntimeError('На контроллере {} нет кластеров'.format(controller_ip))

    vm_http_client = await VmHttpClient.create(controller_ip, '')  # noqa
    templates = await vm_http_client.fetch_templates_list()
    if not templates:
        raise RuntimeError('На контроллере {} нет шаблонов'.format(controller_ip))

    for template in templates:
        # check if template has a disk
        vm_http_client = await VmHttpClient.create(controller_ip, template['id'])  # noqa
        disks_list = await vm_http_client.fetch_vdisks_list()
        if not disks_list:
            continue

        # check if node active
        node_info = await resources_http_client.fetch_node(template['node']['id'])
        if node_info['status'] != 'ACTIVE':
            continue

        # determine cluster
        vm_http_client = await VmHttpClient.create(controller_ip, template['id'])  # noqa
        template_info = await vm_http_client.info()

        return {'controller_ip': controller_ip, 'cluster_id': template_info['cluster'],
                'node_id': template['node']['id'], 'template_id': template['id'],
                'datapool_id': disks_list[0]['datapool']['id']}

    raise RuntimeError('Подходящие ресурсы не найдены.')


async def get_resources_automated_pool_test():
    """На контроллере ищутся оптимальные ресурсы для проведения теста
    """
    # controller
    controllers_addresses = await Controller.get_addresses()
    if not controllers_addresses:
        raise RuntimeError('Нет контроллеров')

    controller_ip = controllers_addresses[0]
    resources_http_client = await ResourcesHttpClient.create(controller_ip)  # noqa
    clusters = await resources_http_client.fetch_cluster_list()
    if not clusters:
        raise RuntimeError('На контроллере {} нет кластеров'.format(controller_ip))
    vm_http_client = await VmHttpClient.create(controller_ip, '')  # noqa
    templates = await vm_http_client.fetch_templates_list()
    if not templates:
        raise RuntimeError('На контроллере {} нет шаблонов'.format(controller_ip))

    # select appropriate template_id and node_id
    # node must be active and has a template
    for cluster in clusters:
        resources_http_client = await ResourcesHttpClient.create(controller_ip)  # noqa
        nodes = await resources_http_client.fetch_node_list(cluster['id'])
        if not nodes:
            continue

        for node in nodes:
            if node['status'] == 'ACTIVE':
                # check if node has template
                try:
                    template_id = next(template['id'] for template in templates
                                       if template['node']['id'] == node['id'])
                except StopIteration:  # node doesnt have template
                    continue
                else:  # template found
                    # find active datapool
                    resources_http_client = await ResourcesHttpClient.create(controller_ip)  # noqa
                    datapools = await resources_http_client.fetch_datapool_list(node_id=node['id'])
                    # Временное решение для исключения zfs-пулов.
                    for datapool in datapools[:]:
                        if datapool.get('zfs_pool'):
                            datapools.remove(datapool)

                    try:
                        datapool_id = next(datapool['id'] for datapool in datapools if datapool['status'] == 'ACTIVE')
                    except StopIteration:  # No active datapools
                        continue

                    return {'controller_ip': controller_ip, 'cluster_id': cluster['id'],
                            'node_id': node['id'], 'template_id': template_id, 'datapool_id': datapool_id}

    raise RuntimeError('Подходящие ресурсы не найдены')


def get_test_pool_name():
    """Generate a test pool name"""
    return 'test_pool_{}'.format(str(uuid.uuid4())[:7])


@pytest.fixture
@async_generator
async def fixt_launch_workers():

    ws_listener_worker = Popen([sys.executable, "ws_listener_worker/ws_listener_worker.py"])
    pool_worker = Popen([sys.executable, "pool_worker/pool_worker.py", "-do-not-resume-tasks"])

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

    resources = await get_resources_automated_pool_test()
    if not resources:
        print('resources not found!')

    qu = '''
        mutation {
            addDynamicPool(verbose_name: "%s", controller_ip: "%s",
                           cluster_id: "%s", node_id: "%s", datapool_id: "%s", template_id: "%s",
                           max_size: 4, max_vm_amount: 4, increase_step: 1, increase_step: 1,
                           initial_size: 1, total_size: 2, max_amount_of_create_attempts: 10,
                           create_thin_clones: true){
                    ok
                    pool{
                        pool_id
                        pool_type
                    }
            }
        }
        ''' % (get_test_pool_name(), resources['controller_ip'], resources['cluster_id'], resources['node_id'],
               resources['datapool_id'], resources['template_id'])
    context = await get_auth_context()
    executed = await execute_scheme(pool_schema, qu, context=context)

    pool_id = executed['addDynamicPool']['pool']['pool_id']

    # Нужно дождаться внутреннего сообщения о создании пула.
    # pool_creation_waiter = WaiterSubscriptionObserver()
    # pool_creation_waiter.add_subscription_source(EVENTS_SUBSCRIPTION)
    # internal_event_monitor.subscribe(pool_creation_waiter)

    def _check_if_pool_created(redis_message):

        system_logger._debug('_check_if_pool_created: redis_message : ' + str(redis_message))
        try:
            redis_message_data = redis_message['data'].decode()
            redis_message_data_dict = json.loads(redis_message_data)

            if redis_message_data_dict['event'] == 'pool_creation_completed':
                return redis_message_data_dict['is_successful']
        except Exception as ex:
            print('_check_if_pool_created ' + str(ex))

        return False

    POOL_CREATION_TIMEOUT = 60

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
async def fixt_create_static_pool(fixt_db):
    """Создается ВМ, создается пул с этой ВМ, пул удаляется, ВМ удаляется."""
    pool_main_resources = await get_resources_static_pool_test()
    controller_ip = pool_main_resources['controller_ip']
    node_id = pool_main_resources['node_id']
    datapool_id = pool_main_resources['datapool_id']
    template_id = pool_main_resources['template_id']
    context = await get_auth_context()

    # --- create VM ---
    async def _create_domain():
        test_domain_name = 'domain_name_{}'.format(str(uuid.uuid4())[:7])

        params = {
            'verbose_name': test_domain_name,
            'domain_id': template_id,
            'datapool_id': datapool_id,
            'controller_ip': controller_ip,
            'node_id': node_id,
            'create_thin_clones': True,
            'domain_index': 666
        }
        vm_info = await Vm.copy(**params)
        return vm_info

    domain_info = await _create_domain()
    current_vm_task_id = domain_info['task_id']

    def _check_if_vm_created(redis_message):
        try:
            redis_message_data = redis_message['data'].decode()
            system_logger._debug('_check_if_vm_created:redis_message ' + str(redis_message_data))
            redis_message_data_dict = json.loads(redis_message_data)

            obj = redis_message_data_dict['object']
            if current_vm_task_id == obj['parent'] and obj['status'] == 'SUCCESS':
                return True
        except Exception as ex:
            system_logger._debug('_check_if_vm_created ' + str(ex))
        return False

    await a_redis_wait_for_message(WS_MONITOR_CHANNEL_OUT, _check_if_vm_created, VEIL_WS_MAX_TIME_TO_WAIT)
    # --- create pool ---
    qu = '''
        mutation {
          addStaticPool(verbose_name: "%s", vm_ids: ["%s"]) {
            ok
            pool{
                pool_id
                pool_type
            }
          }
        }
        ''' % (get_test_pool_name(), domain_info['id'])
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

    # --- remove test VM ---
    vm_http_client = await VmHttpClient.create(controller_ip, domain_info['id'])  # noqa
    await vm_http_client.remove_vm()


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
        await group.add_role(Role.READ_ONLY, creator='system')
    event_loop.run_until_complete(setup())
    return True


@pytest.fixture
def fixt_controller(request, event_loop):

    id_ = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    verbose_name = 'test controller'
    address = '192.168.11.115'
    token = 'jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxNjUsInVzZXJuYW1lIjoiYXBpLWNsaSIsImV4cCI6MTkwODI2MjI1Niwic3NvIjpmYWxzZSwib3JpZ19pYXQiOjE1OTM3NjYyNTZ9._41CVXezP1vDHoZyQ71UcadqPdti7-tmy_teEjfBgio'

    async def setup():
        await Controller.create(id=id_,
                                verbose_name=verbose_name,
                                address=address,
                                status=Status.ACTIVE,
                                token=token
                                )

        send_cmd_to_ws_monitor(id_, WsMonitorCmd.ADD_CONTROLLER)
    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Controller.delete.where(Controller.id == id_).gino.status()
            send_cmd_to_ws_monitor(id_, WsMonitorCmd.REMOVE_CONTROLLER)

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


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
