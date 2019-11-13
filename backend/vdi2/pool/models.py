# -*- coding: utf-8 -*-
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy import case, literal_column

from settings import VEIL_WS_MAX_TIME_TO_WAIT
from database import db, Status
from controller.models import Controller
from vm.models import Vm
from common.veil_errors import VmCreationError, BadRequest

from resources_monitoring.handlers import WaiterSubscriptionObserver
from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from resources_monitoring.resources_monitoring_data import VDI_TASKS_SUBSCRIPTION


class Pool(db.Model):
    """На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах)."""
    __tablename__ = 'pool'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    cluster_id = db.Column(UUID(), nullable=False)
    node_id = db.Column(UUID(), nullable=False)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    controller = db.Column(UUID(), db.ForeignKey('controller.id'), nullable=False)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @staticmethod
    def get_pools_query():
        """Содержит только логику запроса
           Обьединяет таблицы Статического и Динамического пула и проставляет им поле POOL_TYPE
        """
        # TODO: сортировка
        xpr = case([(StaticPool.static_pool_id == None, literal_column("'AUTOMATED'"))],
                   else_=literal_column("'STATIC'")).label('POOL_TYPE')

        query = db.select([Pool,
                           AutomatedPool,
                           StaticPool,
                           xpr]).select_from(Pool.join(AutomatedPool,
                                                       isouter=True).join(StaticPool,
                                                                          isouter=True)).where(
            Pool.status != Status.DELETING)
        return query

    @staticmethod
    async def get_pool(pool_id):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        query = Pool.get_pools_query()
        query = query.where(Pool.id == pool_id)
        return await query.gino.first()

    @staticmethod
    async def get_pools():
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        query = Pool.get_pools_query()
        return await query.gino.all()

    @staticmethod
    async def get_desktop_type(pool_id):
        # TODO: rewrite
        return await Pool.select('desktop_pool_type').where(Pool.id == pool_id).gino.scalar()

    @staticmethod
    async def get_controller_ip(pool_id):
        query = db.select([Controller.address]).select_from(Controller.join(Pool)).where(
            Pool.id == pool_id)
        return await query.gino.scalar()

    async def get_vm_amount(self, only_free=False):
        """ == None because alchemy can't work with is None"""
        # TODO: rewrite
        if only_free:
            return await db.select([db.func.count()]).where(
                (Vm.pool_id == self.id) & (Vm.username == None)).gino.scalar()  # noqa
        else:
            return await db.select([db.func.count()]).where(Vm.pool_id == self.id).gino.scalar()

    @staticmethod
    async def get_user_pools(user='admin'):
        # TODO: rewrite?
        # TODO: rewrite normally
        # TODO: добавить вывод типа OS у VM
        # TODO: добавить вывод состояния пула
        # TODO: ограничение по списку пулов для пользователя
        pools = await Pool.select('id', 'verbose_name').gino.all()
        ans = list()
        for pool in pools:
            ans_d = dict()
            ans_d['id'] = str(pool.id)
            ans_d['name'] = pool.verbose_name
            ans.append(ans_d)
        return ans

    @staticmethod
    async def get_user_pool(pool_id: int, username=None):
        """Return first hit"""
        # TODO: rewrite?
        query = db.select(
            [
                Controller.address,
                Pool.desktop_pool_type,
                Vm.id,
            ]
        ).select_from(Pool.join(Controller).join(Vm, (Vm.username == username) & (Vm.pool_id == Pool.id), isouter=True)
                      ).where(
            (Pool.id == pool_id))
        return await query.gino.first()

    @staticmethod
    async def get_node_id(pool_id):
        return await Pool.select('node_id').where(Pool.id == pool_id).gino.scalar()

    @staticmethod
    async def get_name(pool_id):
        return await Pool.select('verbose_name').where(Pool.id == pool_id).gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    @classmethod
    async def create(cls, verbose_name, cluster_id, node_id, controller_ip):
        controller_id = await Controller.get_controller_id_by_ip(controller_ip)
        if not controller_id:
            raise AssertionError('Controller {} not found.'.format(controller_ip))

        pool = await super().create(verbose_name=verbose_name, cluster_id=cluster_id, node_id=node_id,
                                    controller=controller_id,
                                    status=Status.CREATING)
        return pool

    @classmethod
    async def activate(cls, pool_id):
        return await Pool.update.values(status=Status.ACTIVE).where(
            Pool.id == pool_id).gino.status()

    @classmethod
    async def deactivate(cls, pool_id):
        return await Pool.update.values(status=Status.FAILED).where(
            Pool.id == pool_id).gino.status()

    async def expand_pool_if_requred(self):
        """
        Check and expand pool if required
        :return:
        """
        # TODO: rewrite
        # TODO: код перенесен, чтобы работал. Принципиально не перерабатывался.
        # Check that total_size is not reached
        vm_amount_in_pool = await self.get_vm_amount()

        # If reached then do nothing
        if vm_amount_in_pool >= self.total_size:
            return

        # Число машин в пуле, неимеющих пользователя
        free_vm_amount = await self.get_vm_amount(only_free=True)

        # Если подогретых машин слишком мало, то пробуем добавить еще
        if self.reserve_size > free_vm_amount:
            # Max possible amount of VMs which we can add to the pool
            max_possible_amount_to_add = self.total_size - vm_amount_in_pool
            # Real amount that we can add to the pool
            real_amount_to_add = min(max_possible_amount_to_add, self.vm_step)
            # add VMs.
            try:
                # TODO: очень странная логика. Может есть смысл создавать как-то диапазоном на стороне ECP?
                for i in range(1, real_amount_to_add):
                    domain_index = vm_amount_in_pool + i
                    await self.add_vm(domain_index)
            except VmCreationError:
                # TODO: log that we cant expand the pool.  Mark pool as broken?
                pass

    @classmethod
    async def soft_delete(cls, pool_id):
        return await Pool.update.values(status=Status.DELETING).where(
            Pool.id == pool_id).gino.status()


class StaticPool(db.Model):
    """На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах)."""
    __tablename__ = 'static_pool'
    static_pool_id = db.Column(UUID(), db.ForeignKey('pool.id'), primary_key=True)

    @classmethod
    async def get_info(cls, pool_id: str):
        if not pool_id:
            raise AssertionError('Empty uid.')
        pool_data = AutomatedPool.join(Pool).select().where(
            Pool.id == pool_id)
        return await pool_data.gino.first()

    @classmethod
    async def create(cls, verbose_name, controller_ip, cluster_id, node_id):
        """Nested transactions are atomic."""

        async with db.transaction() as tx:
            # Create pool first
            pool = await Pool.create(verbose_name=verbose_name,
                                     cluster_id=cluster_id,
                                     node_id=node_id,
                                     controller_ip=controller_ip)
            # Create static pool
            return await super().create(static_pool_id=pool.id)

    async def activate(self):
        return await Pool.activate(self.static_pool_id)

    async def deactivate(self):
        return await Pool.deactivate(self.static_pool_id)


class AutomatedPool(db.Model):
    """
    reserve_size - желаемое минимальное количество подогретых машин (добавленных в пул, но не имеющих пользователя)
    На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах).
    """
    __tablename__ = 'automated_pool'

    automated_pool_id = db.Column(UUID(), db.ForeignKey('pool.id'), primary_key=True)
    datapool_id = db.Column(UUID(), nullable=False)
    template_id = db.Column(UUID(), nullable=False)

    # Pool size settings
    min_size = db.Column(db.Integer(), nullable=False, default=1)
    max_size = db.Column(db.Integer(), nullable=False, default=200)
    max_vm_amount = db.Column(db.Integer(), nullable=False, default=1000)
    increase_step = db.Column(db.Integer(), nullable=False, default=3)
    max_amount_of_create_attempts = db.Column(db.Integer(), nullable=False, default=2)

    initial_size = db.Column(db.Integer(), nullable=False, default=1)
    reserve_size = db.Column(db.Integer(), nullable=False, default=0)
    total_size = db.Column(db.Integer(), nullable=False, default=1)
    vm_name_template = db.Column(db.Unicode(length=100), nullable=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    async def node_id(self):
        return await Pool.get_node_id(self.automated_pool_id)

    @property
    async def verbose_name(self):
        return await Pool.get_name(self.automated_pool_id)

    @property
    async def controller_ip(self):
        return await Pool.get_controller_ip(self.automated_pool_id)

    @classmethod
    async def get_info(cls, pool_id: str):
        if not pool_id:
            raise AssertionError('Empty uid.')
        pool_data = AutomatedPool.join(Pool).select().where(
            Pool.id == pool_id)
        return await pool_data.gino.first()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    @classmethod
    async def create(cls, verbose_name, controller_ip, cluster_id, node_id,
                     template_id, datapool_id, min_size, max_size, max_vm_amount, increase_step,
                     max_amount_of_create_attempts, initial_size, reserve_size, total_size, vm_name_template):
        """Nested transactions are atomic."""
        async with db.transaction() as tx:
            # Create pool first
            pool = await Pool.create(verbose_name=verbose_name,
                                     cluster_id=cluster_id,
                                     node_id=node_id,
                                     controller_ip=controller_ip)
            # Create automated pool
            return await super().create(automated_pool_id=pool.id,
                                        template_id=template_id,
                                        datapool_id=datapool_id,
                                        min_size=min_size,
                                        max_size=max_size,
                                        max_vm_amount=max_vm_amount,
                                        increase_step=increase_step,
                                        max_amount_of_create_attempts=max_amount_of_create_attempts,
                                        initial_size=initial_size,
                                        reserve_size=reserve_size,
                                        total_size=total_size,
                                        vm_name_template=vm_name_template)

    @classmethod
    async def soft_update(cls, id, verbose_name, reserve_size, total_size, vm_name_template):
        async with db.transaction() as tx:
            if verbose_name:
                await Pool.update.values(verbose_name=verbose_name).where(
                    Pool.id == id).gino.status()
            auto_pool_kwargs = dict()
            if reserve_size:
                auto_pool_kwargs['reserve_size'] = reserve_size
            if total_size:
                auto_pool_kwargs['total_size'] = total_size
            if vm_name_template:
                auto_pool_kwargs['vm_name_template'] = vm_name_template
            if auto_pool_kwargs:
                await AutomatedPool.update.values(**auto_pool_kwargs).where(
                    AutomatedPool.automated_pool_id == id).gino.status()
        return True

    async def activate(self):
        return await Pool.activate(self.automated_pool_id)

    async def deactivate(self):
        return await Pool.deactivate(self.automated_pool_id)

    async def add_vm(self, domain_index):
        """
        Try to add VM to pool
        :param domain_index:
        :return:
        """
        # TODO: Получить инстанс пула, чтобы не дергать кадлый параметр отдельно
        # TODO: rewrite
        # TODO: beautify
        vm_name_template = self.vm_name_template or await self.verbose_name

        # uid = str(uuid.uuid4())[:7]

        params = {
            'verbose_name': "{}-{}-{}".format(vm_name_template, domain_index, str(uuid.uuid4())[:7]),
            'name_template': vm_name_template,
            'domain_id': str(self.template_id),
            'datapool_id': str(self.datapool_id),  # because of UUID
            'controller_ip': await self.controller_ip,
            'node_id': str(await self.node_id),
        }

        # try to create vm
        for i in range(self.max_amount_of_create_attempts):
            print('add_domain № {}, attempt № {}'.format(domain_index, i))
            # send request to create vm
            try:
                vm_info = await Vm.copy(**params)
                current_vm_task_id = vm_info['task_id']
            except BadRequest as E:
                print(E)
                continue

            # TODO: не переписывал. Уточнить у Александра какой план насчет подписки на WS
            # subscribe to ws messages
            response_waiter = WaiterSubscriptionObserver()
            response_waiter.add_subscription_source('/tasks/')

            resources_monitor_manager.subscribe(response_waiter)
            # wait for result

            def _is_vm_creation_task(name):
                """
                Determine domain creation task by name
                """
                if name.startswith('Создание виртуальной машины'):
                    return True
                if all(word in name.lower() for word in ['creating', 'virtual', 'machine']):
                    return True
                return False

            def _check_if_vm_created(json_message):
                obj = json_message['object']

                if _is_vm_creation_task(obj['name']) and current_vm_task_id == obj['parent']:
                    if obj['status'] == 'SUCCESS':
                        return True
                return False

            is_vm_successfully_created = await response_waiter.wait_for_message(
                _check_if_vm_created, VEIL_WS_MAX_TIME_TO_WAIT)
            resources_monitor_manager.unsubscribe(response_waiter)

            if is_vm_successfully_created:
                await Vm.create(id=vm_info['id'], pool_id=str(self.automated_pool_id),
                                template_id=str(self.template_id),
                                username='admin')
                return vm_info
            else:
                continue  # go to try again

        raise VmCreationError('Can\'t create VM')

    async def add_initial_vms(self):
        """Create required initial amount of VMs for auto pool"""
        # Основная логика сохранена со старой схемы. На рефакторинг внутреннего кода пока нет времени.
        # TODO: главное, что бы хотелось тут и в других местах создания виртуалок - отправлять диапазоны виртуалок

        print('Add initial vms:')
        # # fetch_template_info was commented on previous version
        # template_info = await GetDomainInfo(controller_ip=pool_args_dict['controller_ip'],
        #                                     domain_id=pool_args_dict['template_id'])

        vm_list = list()
        try:
            for i in range(self.initial_size):
                vm_index = 1 + i
                vm = await self.add_vm(vm_index)
                vm_list.append(vm)

                # notify VDI front about progress(WS)
                msg_dict = dict(msg='Automated pool creation. Created {} VMs from {}'.format(vm_index,
                                                                                             self.initial_size),
                                mgs_type='data',
                                event='pool_creation_progress',
                                pool_id=str(self.automated_pool_id),
                                domain_index=vm_index,
                                initial_size=self.initial_size,
                                resource=VDI_TASKS_SUBSCRIPTION)
                resources_monitor_manager.signal_internal_event(msg_dict)
        except VmCreationError as E:
            # log that we cant create required initial amount of VMs
            print('Cant create VM')
            print(E)

        # notify VDI front about pool creation result (WS)
        is_creation_successful = (len(vm_list) == self.initial_size)
        print('is creation successful: {}'.format(is_creation_successful))
        if is_creation_successful:
            msg = 'Automated pool successfully created. Initial VM amount {}'.format(len(vm_list))
        else:
            msg = 'Automated pool created with errors. VMs created: {}. Required: {}'.format(len(vm_list),
                                                                                             self.initial_size)

        # Prepare new msg to resource monitor
        msg_dict = dict(msg=msg,
                        msg_type='data',
                        event='pool_creation_completed',
                        pool_id=str(self.automated_pool_id),
                        amount_of_created_vms=len(vm_list),
                        initial_size=self.initial_size,
                        is_successful=is_creation_successful,
                        resource=VDI_TASKS_SUBSCRIPTION)
        resources_monitor_manager.signal_internal_event(msg_dict)


class PoolUsers(db.Model):
    __tablename__ = 'pools_users'
    pool_id = db.Column(UUID(), db.ForeignKey('pool.id'))
    user_id = db.Column(UUID(), db.ForeignKey('user.id'))

    # TODO: rewrite
    @staticmethod  # todo: not checked
    async def check_row_exists(pool_id, username):
        row = await PoolUsers.select().where((PoolUsers.username == username) and
                                             (PoolUsers.pool_id == pool_id)).gino.all()
        return row
