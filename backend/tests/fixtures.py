import pytest
import uuid
from async_generator import async_generator, yield_
from graphene import Context

from app import start_gino, stop_gino
from settings import VEIL_WS_MAX_TIME_TO_WAIT
from database import Role, Status
from auth.utils.veil_jwt import encode_jwt
from auth.utils import crypto

from controller.models import Controller
from controller_resources.veil_client import ResourcesHttpClient
from controller.client import ControllerClient

from vm.veil_client import VmHttpClient
from vm.models import Vm

from pool.schema import pool_schema

from auth.models import Group, User
from auth.authentication_directory.models import AuthenticationDirectory, Mapping

from tests.utils import execute_scheme

from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from resources_monitoring.internal_event_monitor import internal_event_monitor
from resources_monitoring.handlers import WaiterSubscriptionObserver
from resources_monitoring.resources_monitoring_data import VDI_TASKS_SUBSCRIPTION


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
    resources_http_client = await ResourcesHttpClient.create(controller_ip)
    clusters = await resources_http_client.fetch_cluster_list()
    if not clusters:
        raise RuntimeError('На контроллере {} нет кластеров'.format(controller_ip))

    vm_http_client = await VmHttpClient.create(controller_ip, '')
    templates = await vm_http_client.fetch_templates_list()
    if not templates:
        raise RuntimeError('На контроллере {} нет шаблонов'.format(controller_ip))

    for template in templates:
        # check if template has a disk
        vm_http_client = await VmHttpClient.create(controller_ip, template['id'])
        disks_list = await vm_http_client.fetch_vdisks_list()
        if not disks_list:
            continue

        # check if node active
        node_info = await resources_http_client.fetch_node(template['node']['id'])
        if node_info['status'] != 'ACTIVE':
            continue

        # determine cluster
        vm_http_client = await VmHttpClient.create(controller_ip, template['id'])
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
                except StopIteration:  # node doesnt have template
                    continue
                else:  # template found
                    # find active datapool
                    resources_http_client = await ResourcesHttpClient.create(controller_ip)
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
async def fixt_create_automated_pool():
    """Create an automated pool, yield, remove this pool"""
    # start resources_monitor to receive info  from controller. autopool creation doesnt work without it
    await resources_monitor_manager.start()

    resources = await get_resources_automated_pool_test()
    if not resources:
        print('resources not found!')

    qu = '''
        mutation {
            addDynamicPool(verbose_name: "%s", controller_ip: "%s",
                           cluster_id: "%s", node_id: "%s", datapool_id: "%s", template_id: "%s",
                           max_size: 4, max_vm_amount: 4, increase_step: 1, min_free_vms_amount: 1,
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
    pool_creation_waiter = WaiterSubscriptionObserver()
    pool_creation_waiter.add_subscription_source(VDI_TASKS_SUBSCRIPTION)
    internal_event_monitor.subscribe(pool_creation_waiter)

    def _check_if_pool_created(json_message):
        try:
            if json_message['event'] == 'pool_creation_completed':
                return json_message['is_successful']
        except KeyError:
            pass

        return False

    POOL_CREATION_TIMEOUT = 80
    is_pool_successfully_created = await pool_creation_waiter.wait_for_message(
        _check_if_pool_created, POOL_CREATION_TIMEOUT)
    internal_event_monitor.unsubscribe(pool_creation_waiter)

    await yield_({
        'id': pool_id,
        'is_pool_successfully_created': is_pool_successfully_created
    })

    # remove pool
    qu = '''
    mutation {
      removePool(pool_id: "%s", full: true) {
        ok
      }
    }
    ''' % pool_id
    await execute_scheme(pool_schema, qu, context=context)

    # stop monitor
    await resources_monitor_manager.stop()


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
    await resources_monitor_manager.start()
    response_waiter = WaiterSubscriptionObserver()
    response_waiter.add_subscription_source('/tasks/')
    resources_monitor_manager.subscribe(response_waiter)

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

    def _check_if_vm_created(json_message):
        try:
            obj = json_message['object']
            if current_vm_task_id == obj['parent'] and obj['status'] == 'SUCCESS':
                return True
        except KeyError:
            pass
        return False

    await response_waiter.wait_for_message(_check_if_vm_created, VEIL_WS_MAX_TIME_TO_WAIT)
    resources_monitor_manager.unsubscribe(response_waiter)
    await resources_monitor_manager.stop()
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
    vm_http_client = await VmHttpClient.create(controller_ip, domain_info['id'])
    await vm_http_client.remove_vm()


@pytest.fixture
def fixt_group(request, event_loop):
    group_name = 'test_group_1'

    async def setup():
        await Group.create(verbose_name=group_name, id="10913d5d-ba7a-4049-88c5-769267a6cbe4")

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Group.delete.where(Group.id == "10913d5d-ba7a-4049-88c5-769267a6cbe4").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user(request, event_loop):
    """Фикстура учитывает данные фикстуры пула."""
    user_name = 'test_user'
    user_id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    user_password = 'veil'

    async def setup():
        await User.soft_create(username=user_name, id=user_id, password=user_password)

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

    async def setup():
        await User.soft_create(username=user_name, id=user_id, password=user_password, is_superuser=True)

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

    async def setup():
        await User.soft_create(username=user_name, id=user_id, password=user_password, is_superuser=True)

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
        await User.soft_create(username='test_user_locked', id=user_id, is_active=False, password="qwe")

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

    async def setup():
        await AuthenticationDirectory.soft_create(id=id, verbose_name=verbose_name, directory_url=directory_url,
                                                  domain_name=domain_name)
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
        await auth_dir.add_mapping(mapping=mapping_dict, groups=groups)
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
        await group.add_role(Role.READ_ONLY)
    event_loop.run_until_complete(setup())
    return True


@pytest.fixture
def fixt_controller(request, event_loop):

    id = '10913d5d-ba7a-4049-88c5-769267a6cbe4'
    verbose_name = 'test controller'
    username = 'test_vdi_user'
    password = 'test_vdi_user'
    address = '192.168.11.102'

    async def setup():
        controller_client = ControllerClient(address)
        auth_info = dict(username=username, password=password, ldap=False)
        token, expires_on = await controller_client.auth(auth_info=auth_info)
        await Controller.create(id=id,
                                verbose_name=verbose_name,
                                address=address,
                                status=Status.ACTIVE,
                                username=username,
                                password=crypto.encrypt(password),
                                ldap_connection=False,
                                token=token,
                                expires_on=expires_on
                                )
    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Controller.delete.where(Controller.id == id).gino.status()

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
