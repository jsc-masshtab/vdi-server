import pytest
import uuid

from subprocess import Popen, TimeoutExpired
import sys
import os

from graphene import Context

from common.database import start_gino, stop_gino
from common.veil.veil_gino import Role
from common.veil.auth.veil_jwt import encode_jwt
from common.veil.veil_api import get_veil_client_singleton, stop_veil_client
from common.veil.veil_redis import redis_get_client, wait_for_task_result

from common.models.controller import Controller
from common.models.pool import Pool
from common.models.vm import Vm
from common.models.vm_connection_data import VmConnectionData
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import Group, User
from common.models.authentication_directory import AuthenticationDirectory, Mapping
from common.models.license import License
from common.models.task import Task, TaskStatus

from common.veil.veil_redis import redis_init, redis_deinit

from web_app.controller.schema import controller_schema
from web_app.pool.schema import pool_schema
from web_app.tests.utils import execute_scheme


async def get_resources_for_pool_test():

    # controller
    controllers = await Controller.get_objects()
    if not controllers:
        raise RuntimeError("Нет контроллеров")

    controller = await Controller.get(controllers[0].id)

    # ids are random
    return {
        "controller_id": controller.id,
        "resource_pool_id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
        "cluster_id": "6dd44376-0bf5-46b8-8a23-5a1e6fcfe376",
        "node_id": "236d318f-d57e-4f1b-9097-93d69f8782dd",
        "template_id": "a04ed49b-ea26-4660-8112-833a6b51d0e1",
        "datapool_id": "37df3326-55b9-4af1-91b3-e54df12f24e7",
    }


def get_test_pool_name():
    """Generate a test pool name."""
    return "test-pool-{}".format(str(uuid.uuid4())[:7])


@pytest.fixture
async def fixt_redis_client():
    redis_init()
    yield
    await redis_deinit()


@pytest.fixture
async def fixt_db(fixt_redis_client):
    """Actual fixture for requests working with db."""
    await start_gino()
    yield
    await stop_gino()


@pytest.fixture
async def fixt_init_license():

    license_data = {
        "verbose_name": "Fake license",
        "thin_clients_limit": 10,
        "uuid": str(uuid.uuid4()),
        "expiration_date": License.convert_date("2030-05-01", "%Y-%m-%d"),
        "support_expiration_date": License.convert_date("2030-05-01", "%Y-%m-%d")
    }
    await License.save_license_data_to_db(license_data)
    yield


async def get_auth_token():
    """Return JWT token for Admin user.

    Грязный хак в том, что пользователь и пароль при авторизации проверяется раньше.
    Тут напрямую вызывается уже генерация токена.
    """
    access_token = "jwt " + encode_jwt("vdiadmin").get("access_token")
    return access_token


async def get_auth_context():
    """Return auth headers in Context for Graphene query execution of protected methods."""
    auth_token = await get_auth_token()
    context = Context()
    context.headers = {
        "Authorization": auth_token,
        "Client-Type": "PyTest",
        "Content-Type": "application/json",
    }
    context.remote_ip = "127.0.0.1"
    return context


@pytest.fixture
async def fixt_auth_context():
    """Auth context fixture."""
    return await get_auth_context()


@pytest.fixture  # prepare_vms: false,
async def fixt_create_automated_pool(fixt_controller):
    """Create an automated pool, yield, remove this pool."""
    # start resources_monitor to receive info  from controller. autopool creation doesn`t work without it

    resources = await get_resources_for_pool_test()
    if not resources:
        print("resources not found!")

    qu = """
            mutation {
                      addDynamicPool(
                        connection_types: [SPICE, RDP],
                        verbose_name: "%s",
                        controller_id: "%s",
                        resource_pool_id: "%s",
                        datapool_id: "%s",
                        template_id: "%s",
                        initial_size: 1,
                        reserve_size: 1,
                        increase_step: 1,
                        total_size: 2,
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
                    }""" % (
        get_test_pool_name(),
        resources["controller_id"],
        resources["resource_pool_id"],
        resources["datapool_id"],
        resources["template_id"],
    )
    context = await get_auth_context()
    executed = await execute_scheme(pool_schema, qu, context=context)

    pool_id = executed["addDynamicPool"]["pool"]["pool_id"]
    tasks = await Task.get_tasks_associated_with_entity(pool_id)

    # при подготовке ВМ  несколько раз используются таймауты по 10 секунд,
    # из-за чего даже с тестовым вейлом создание пула длится долго
    status = await wait_for_task_result(tasks[0].id, 60)
    is_pool_successfully_created = (status is not None) and (
        status == TaskStatus.FINISHED.name
    )

    yield {"id": pool_id, "is_pool_successfully_created": is_pool_successfully_created}

    # remove pool
    qu = (
        """
    mutation {
      removePool(pool_id: "%s", full: true) {
        ok
      }
    }
    """
        % pool_id
    )
    await execute_scheme(pool_schema, qu, context=context)


@pytest.fixture
async def fixt_create_static_pool(fixt_controller):
    """Создается пул, пул удаляется."""
    pool_main_resources = await get_resources_for_pool_test()
    controller_id = pool_main_resources["controller_id"]
    resource_pool_id = pool_main_resources["resource_pool_id"]
    vm_id = uuid.uuid4()  # random

    # --- create pool ---
    qu = """
            mutation{addStaticPool(
              verbose_name: "%s",
              controller_id: "%s",
              resource_pool_id: "%s",
              vms:[
                {id: "%s",
                  verbose_name: "test_2"}
              ],
              connection_types: [SPICE, RDP],
            ){
              pool {
                pool_id
              }
              ok
            }
            }""" % (
        get_test_pool_name(),
        controller_id,
        resource_pool_id,
        vm_id,
    )

    context = await get_auth_context()
    pool_create_res = await execute_scheme(pool_schema, qu, context=context)
    pool_id = pool_create_res["addStaticPool"]["pool"]["pool_id"]
    yield {"ok": pool_create_res["addStaticPool"]["ok"], "id": pool_id}

    # --- remove pool ---
    qu = (
        """
    mutation {
      removePool(pool_id: "%s", full: true) {
        ok
      }
    }
    """
        % pool_id
    )
    await execute_scheme(pool_schema, qu, context=context)


@pytest.fixture
async def several_static_pools(fixt_controller, count: int = 5):
    """Создать несколько статических пулов."""
    pool_main_resources = await get_resources_for_pool_test()
    controller_id = pool_main_resources["controller_id"]
    resource_pool_id = pool_main_resources["resource_pool_id"]
    context = await get_auth_context()
    pools_list = list()
    # Создаем пулы
    for _ in range(count + 1):
        vm_id = uuid.uuid4()
        qu = """
            mutation{addStaticPool(
              verbose_name: "%s",
              controller_id: "%s",
              resource_pool_id: "%s",
              vms:[
                {id: "%s",
                  verbose_name: "test_2"}
              ],
              connection_types: [SPICE, RDP],
            ){
              pool {
                pool_id
              }
              ok
            }
            }""" % (
            get_test_pool_name(),
            controller_id,
            resource_pool_id,
            vm_id,
        )
        # id созданного пула
        pool_create_res = await execute_scheme(pool_schema, qu, context=context)
        pools_list.append(pool_create_res["addStaticPool"]["pool"]["pool_id"])
    # Пулы созданы
    yield {"pools": pools_list}
    # Удаляем созданные пулы
    for pool_id in pools_list:
        qu = (
            """
        mutation {
          removePool(pool_id: "%s", full: true) {
            ok
          }
        }
        """
            % pool_id
        )
        await execute_scheme(pool_schema, qu, context=context)


@pytest.fixture
async def several_static_pools_with_user(fixt_controller,
                                         several_static_pools,
                                         fixt_user):
    temporary_user_id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    # Закрепляем 1 из пулов за пользователем
    pool = await Pool.query.gino.first()
    await pool.add_user(temporary_user_id, "system")
    yield {"pool_with_user": pool.id_str}
    # Открепляем пользователя от пула
    await pool.remove_users(creator="system", users_list=[temporary_user_id])


@pytest.fixture
async def fixt_create_rds_pool(fixt_controller):
    """Создается пул, пул удаляется."""
    pool_main_resources = await get_resources_for_pool_test()
    controller_id = pool_main_resources["controller_id"]
    resource_pool_id = pool_main_resources["resource_pool_id"]
    vm_id = uuid.uuid4()  # random

    # --- create pool ---
    qu = """
    mutation {
              addRdsPool(verbose_name: "%s",
              controller_id: "%s",
              resource_pool_id:"%s",
              rds_vms:[{id: "%s", verbose_name: "rds_server"}],
              connection_types:[NATIVE_RDP, RDP]){
         ok
         pool{pool_id}
     }
     }""" % (
        get_test_pool_name(),
        controller_id,
        resource_pool_id,
        vm_id,
    )

    context = await get_auth_context()
    pool_create_res = await execute_scheme(pool_schema, qu, context=context)
    pool_id = pool_create_res["addRdsPool"]["pool"]["pool_id"]
    yield {"ok": pool_create_res["addRdsPool"]["ok"], "id": pool_id}

    # --- remove pool ---
    qu = (
        """
    mutation {
      removePool(pool_id: "%s", full: true) {
        ok
      }
    }
    """
        % pool_id
    )
    await execute_scheme(pool_schema, qu, context=context)


@pytest.fixture
async def fixt_veil_client():

    get_veil_client_singleton()
    yield
    await stop_veil_client()


@pytest.fixture
def fixt_group(request, event_loop):
    group_name = "test_group_1"

    async def setup():
        await Group.create(
            verbose_name=group_name,
            id="10913d5d-ba7a-4049-88c5-769267a6cbe4",
            ad_guid="10913d5d-ba7a-4049-88c5-769267a6cbe5",
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Group.delete.where(
                Group.id == "10913d5d-ba7a-4049-88c5-769267a6cbe4"
            ).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_local_group(request, event_loop):
    group_name = "test_group_2"

    async def setup():
        await Group.create(
            verbose_name=group_name, id="10913d5d-ba7a-4049-88c5-769267a6cbe3"
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Group.delete.where(
                Group.id == "10913d5d-ba7a-4049-88c5-769267a6cbe3"
            ).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user(request, event_loop):
    """Фикстура учитывает данные фикстуры пула."""
    user_name = "test_user"
    user_id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    user_password = "veil"
    creator = "system"

    async def setup():
        await User.soft_create(
            username=user_name, id=user_id, password=user_password, creator=creator
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user_admin(request, event_loop):
    user_name = "test_user_admin"
    user_id = "10913d5d-ba7a-4049-88c5-769267a6cbe3"
    user_password = "veil"
    email = "vdi.mashtab@yandex.ru"
    creator = "vdiadmin"

    async def setup():
        await User.soft_create(
            username=user_name,
            id=user_id,
            password=user_password,
            email=email,
            is_superuser=True,
            creator=creator,
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user_another_admin(request, event_loop):
    user_name = "test_user_admin2"
    user_id = "10913d5d-ba7a-4149-88c5-769267a6cbe3"
    user_password = "veil"
    creator = "system"

    async def setup():
        await User.soft_create(
            username=user_name,
            id=user_id,
            password=user_password,
            is_superuser=True,
            creator=creator,
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_user_locked(request, event_loop):
    user_id = "10913d5d-ba7a-4049-88c5-769267a6cbe6"

    async def setup():
        await User.soft_create(
            username="test_user_locked",
            id=user_id,
            is_active=False,
            password="qwe",
            creator="system",
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await User.delete.where(User.id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir(request, event_loop):
    id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    verbose_name = "test_auth_dir"
    directory_url = "ldap://192.168.14.167"
    domain_name = "BAZALT"
    creator = "system"
    dc_str = "bazalt.local"

    async def setup():
        await AuthenticationDirectory.soft_create(
            id=id,
            verbose_name=verbose_name,
            directory_url=directory_url,
            domain_name=domain_name,
            creator=creator,
            dc_str=dc_str,
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(
                AuthenticationDirectory.id == id
            ).gino.status()
            # опасное место
            await User.delete.where(User.username == "ad120").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir_with_pass(request, event_loop):
    id = "10913d5d-ba7a-4049-88c5-769267a6cbe5"
    verbose_name = "test_auth_dir"
    directory_url = "ldap://192.168.14.167"
    domain_name = "BAZALT"
    dc_str = "bazalt.local"
    encoded_service_password = "Bazalt1!"

    async def setup():
        await AuthenticationDirectory.soft_create(
            id=id,
            verbose_name=verbose_name,
            directory_url=directory_url,
            domain_name=domain_name,
            service_password=encoded_service_password,
            service_username="ad120",
            dc_str=dc_str,
            creator="system",
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(
                AuthenticationDirectory.id == id
            ).gino.status()
            # опасное место
            await User.delete.where(User.username == "ad120").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir_for_referral_with_pass(request, event_loop):
    id = "10913d5d-ba7a-4049-88c5-769267a6cbe8"
    verbose_name = "test_msk_auth_dir"
    directory_url = "ldap://192.168.14.251"
    domain_name = "MSK"
    dc_str = "msk.lan"
    encoded_service_password = "Bazalt1!"

    async def setup():
        await AuthenticationDirectory.soft_create(
            id=id,
            verbose_name=verbose_name,
            directory_url=directory_url,
            domain_name=domain_name,
            service_password=encoded_service_password,
            service_username="Администратор",
            dc_str=dc_str,
            creator="system",
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(
                AuthenticationDirectory.id == id
            ).gino.status()
            await User.delete.where(User.username == "spb01@spb.lan").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_ipa_with_pass(request, event_loop):
    id = "10923d5d-ba7a-4049-88c5-769267a6cbe5"
    verbose_name = "test_ipa"
    directory_url = "ldap://192.168.14.83"
    domain_name = "BAZALT"
    dc_str = "bazalt.auth"
    encoded_service_password = "Bazalt1!"

    async def setup():
        await AuthenticationDirectory.soft_create(
            id=id,
            verbose_name=verbose_name,
            directory_url=directory_url,
            directory_type='FreeIPA',
            domain_name=domain_name,
            service_password=encoded_service_password,
            service_username="admin",
            dc_str=dc_str,
            creator="system",
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(
                AuthenticationDirectory.id == id
            ).gino.status()
            # опасное место
            await User.delete.where(User.username == "admin").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_openldap_with_pass(request, event_loop):
    id = "10923d5d-ba7a-4049-88c5-769267a6cbe7"
    verbose_name = "test_openldap"
    directory_url = "ldap://192.168.14.79"
    domain_name = "BAZALT"
    dc_str = "bazalt.team"
    encoded_service_password = "Bazalt1!"

    async def setup():
        await AuthenticationDirectory.soft_create(
            id=id,
            verbose_name=verbose_name,
            directory_url=directory_url,
            directory_type='OpenLDAP',
            domain_name=domain_name,
            service_password=encoded_service_password,
            service_username="ad120",
            dc_str=dc_str,
            creator="system",
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(
                AuthenticationDirectory.id == id
            ).gino.status()
            # опасное место
            await User.delete.where(User.username == "ad120").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir_with_pass_bad(request, event_loop):
    id = "10913d5d-ba7a-4049-88c5-769267a6cbe6"
    verbose_name = "test_auth_dir"
    directory_url = "ldap://192.168.14.167"
    domain_name = "BAZALT"
    dc_str = "bazalt.local"
    encoded_service_password = "bad"

    async def setup():
        await AuthenticationDirectory.soft_create(
            id=id,
            verbose_name=verbose_name,
            directory_url=directory_url,
            domain_name=domain_name,
            service_password=encoded_service_password,
            service_username="bad",
            dc_str=dc_str,
            creator="system",
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(
                AuthenticationDirectory.id == id
            ).gino.status()
            # опасное место
            await User.delete.where(User.username == "ad120").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_auth_dir_with_sync_users(request, event_loop):
    id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    verbose_name = "test_auth_dir"
    directory_url = "ldap://192.168.14.167"
    domain_name = "BAZALT"
    dc_str = "bazalt.local"
    encoded_service_password = "Bazalt1!"

    async def setup():
        auth_dir = await AuthenticationDirectory.soft_create(
            id=id,
            verbose_name=verbose_name,
            directory_url=directory_url,
            domain_name=domain_name,
            service_password=encoded_service_password,
            service_username="ad120",
            dc_str=dc_str,
            creator="system",
        )
        data = {"group_ad_guid": "ec0efca9-5878-4ab4-bb8f-149af659e115",
                "group_verbose_name": "veil-ad-users",
                "group_ad_cn": "CN=veil-ad-users,CN=Users,DC=bazalt,DC=local"}
        await auth_dir.synchronize(data)

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await AuthenticationDirectory.delete.where(
                AuthenticationDirectory.id == id
            ).gino.status()
            # опасное место
            await User.delete.where(User.username.ilike("ad%")).gino.status()
            await Group.delete.where(Group.verbose_name == "veil-ad-users").gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_mapping(request, event_loop):
    """Фикстура завязана на фикстуру AD и Групп."""
    auth_dir_id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    group_id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    groups = [group_id]
    mapping_dict = {
        "id": "10913d5d-ba7a-4049-88c5-769267a6cbe4",
        "verbose_name": "test_mapping_fixt",
        "value_type": Mapping.ValueTypes.GROUP,
        "values": ["veil-ad-users"],
    }

    async def setup():
        auth_dir = await AuthenticationDirectory.get(auth_dir_id)
        await auth_dir.add_mapping(
            mapping=mapping_dict, groups=groups, creator="system"
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Mapping.delete.where(Mapping.id == mapping_dict["id"]).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_group_role(request, event_loop):
    """Фикстура завязана на фикстуру Групп."""
    group_id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"

    async def setup():
        """Подчищать не надо, группа будет удалена и эти записи удалятся каскадом."""
        group = await Group.get(group_id)
        await group.add_role(Role.SECURITY_ADMINISTRATOR, creator="system")

    event_loop.run_until_complete(setup())
    return True


@pytest.fixture
async def fixt_controller(fixt_veil_client):

    controller_ip = "0.0.0.0"

    # add controller
    qu = (
        """
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
    """
        % controller_ip
    )

    context = await get_auth_context()
    executed = await execute_scheme(controller_schema, qu, context=context)
    controller_id = executed["addController"]["controller"]["id"]
    yield {"controller_id": controller_id}

    # remove controller
    qu = (
        """
    mutation {
        removeController(id_: "%s") {
            ok
        }
    }
    """
        % controller_id
    )

    executed = await execute_scheme(controller_schema, qu, context=context)
    assert executed["removeController"]["ok"]


@pytest.fixture
def fixt_vm(request, event_loop, fixt_create_static_pool):

    id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    verbose_name = "test_vm"

    async def setup():
        pool_obj = await Pool.query.gino.first()
        await Vm.create(
            pool_id=pool_obj.id,
            template_id=None,
            created_by_vdi=True,
            verbose_name=verbose_name,
            id=id,
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await Vm.delete.where(Vm.id == id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_vm_connection_data(request, event_loop):
    vm_id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    connection_type = "RDP"
    address = "192.168.88.99"
    port = 3389
    active = True

    async def setup():
        await VmConnectionData.soft_create(
            vm_id=vm_id,
            connection_type=connection_type,
            address=address,
            port=port,
            active=active,
            creator="system"
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await VmConnectionData.delete.where(vm_id == vm_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True


@pytest.fixture
def fixt_active_tk_connection(request, event_loop):
    user_id = "10913d5d-ba7a-4049-88c5-769267a6cbe4"
    veil_connect_version = "1.14.6"
    tk_ip = "127.0.0.1"
    tk_os = "Linux"
    hostname = "PC"
    mac_address = "84:4b:f5:9f:a2:51"

    async def setup():
        await ActiveTkConnection.create(
            user_id=user_id,
            veil_connect_version=veil_connect_version,
            tk_ip=tk_ip,
            tk_os=tk_os,
            mac_address=mac_address,
            hostname=hostname
        )

    event_loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            await ActiveTkConnection.delete.where(user_id == user_id).gino.status()

        event_loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True
