import pytest
import asyncio
import uuid
from async_generator import async_generator, yield_
from graphene import Context

from database import db
from settings import DB_PASS, DB_USER, DB_PORT, DB_HOST, DB_NAME, TESTS_ADMIN_USERNAME
from auth.utils.veil_jwt import encode_jwt

from controller.models import Controller
from controller_resources.veil_client import ResourcesHttpClient

from vm.veil_client import VmHttpClient
from vm.models import Vm

from pool.schema import pool_schema

from tests.utils import execute_scheme

from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from resources_monitoring.internal_event_monitor import internal_event_monitor
from resources_monitoring.handlers import WaiterSubscriptionObserver
from resources_monitoring.resources_monitoring_data import VDI_TASKS_SUBSCRIPTION


async def get_resources_pool_test():
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
                print('active node found')
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


def get_test_pool_name():
    return 'test_pool_{}'.format(str(uuid.uuid4())[:7])


def check_if_pool_created(json_message):
    #print('check_if_pool_created: json_message', json_message)
    try:
        if json_message['event'] == 'pool_creation_completed':
            return True
    except KeyError:
        pass

    return False


@pytest.fixture
@async_generator
async def fixt_db():
    """Actual fixture for requests working with db."""
    await db.set_bind(
        'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'.format(DB_USER=DB_USER, DB_PASS=DB_PASS,
                                                                                DB_HOST=DB_HOST, DB_PORT=DB_PORT,
                                                                                DB_NAME=DB_NAME))
    await yield_()

    await db.pop_bind().close()


async def get_auth_token():
    """Return JWT token for Admin user.
    Грязный хак в том, что пользователь и пароль при авторизации проверяется раньше.
    Тут напрямую вызывается уже генерация токена."""
    access_token = 'jwt ' + encode_jwt(TESTS_ADMIN_USERNAME).get('access_token')
    return access_token


async def get_auth_context():
    """Return auth headers in Context for Graphene query execution of protected methods."""
    auth_token = await get_auth_token()
    context = Context()
    context.headers = {'Authorization': auth_token, 'Client-Type': 'PyTest', 'Content-Type': 'application/json'}
    context.remote_ip = '127.0.0.1'
    return context


@pytest.fixture
async def auth_context_fixture():
    """Auth context fixture."""
    return await get_auth_context()


@pytest.fixture
@async_generator
async def fixt_create_automated_pool():

    # start resources_monitor to receive info  from controller. autopool creation doesnt work without it
    await resources_monitor_manager.start()

    resources = await get_resources_pool_test()

    qu = '''
        mutation {
            addDynamicPool(verbose_name: "%s", controller_ip: "%s", 
                           cluster_id: "%s", node_id: "%s", datapool_id: "%s", template_id: "%s",
                           initial_size: 1, total_size: 2, max_amount_of_create_attempts: 10,
                           create_thin_clones: false){
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

    POOL_CREATION_TIMEOUT = 20
    is_pool_successfully_created = await pool_creation_waiter.wait_for_message(
        check_if_pool_created, POOL_CREATION_TIMEOUT)
    internal_event_monitor.unsubscribe(pool_creation_waiter)
    print('is_pool_successfully_created', is_pool_successfully_created)

    await yield_({
        'id': pool_id,
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
    print('create_static_pool')
    pool_main_resources = await get_resources_pool_test()
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
            'name_template': '',
            'domain_id': template_id,
            'datapool_id': datapool_id,
            'controller_ip':controller_ip,
            'node_id': node_id,
            'create_thin_clones': False
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

    await response_waiter.wait_for_message(_check_if_vm_created, 15)
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
    # print('pool_create_res', pool_create_res)

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
@async_generator
async def fixt_entitle_user_to_pool(fixt_create_static_pool):
    context = await get_auth_context()
    pool_id = fixt_create_static_pool['id']

    # entitle user to pool
    user_name = "admin"
    qu = '''
    mutation {
      entitleUsersToPool(pool_id: "%s", users: ["%s"]) {
        ok
      }
    }
    ''' % (pool_id, user_name)
    res = await execute_scheme(pool_schema, qu, context=context)
    # print('test_res', res)

    await yield_({
        'id': pool_id,
        'ok': res['entitleUsersToPool']['ok']
    })

    # remove entitlement
    qu = '''
    mutation {
    removeUserEntitlementsFromPool(pool_id: "%s", users: ["%s"]) {
        ok
    }
    }
    ''' % (pool_id, user_name)
    res = await execute_scheme(pool_schema, qu, context=context)
