# -*- coding: utf-8 -*-
import uuid
import asyncio

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy import case, literal_column, desc, text

from event.models import Event
from settings import VEIL_WS_MAX_TIME_TO_WAIT
from database import db, Status
from controller.models import Controller
from vm.models import Vm
from user.models import User
from common.veil_errors import VmCreationError, HttpError, SimpleError

from resources_monitoring.handlers import WaiterSubscriptionObserver
from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from resources_monitoring.resources_monitoring_data import VDI_TASKS_SUBSCRIPTION

from pool.pool_task_manager import pool_task_manager


class Pool(db.Model):
    """На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах)."""

    class PoolTypes:
        """
        Класс, описывающий доступные типы подключения служб каталогов.
        """

        AUTOMATED = 'AUTOMATED'
        STATIC = 'STATIC'

    __tablename__ = 'pool'

    pool_id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)  # TODO: try with id
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    cluster_id = db.Column(UUID(), nullable=False)
    node_id = db.Column(UUID(), nullable=False)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    controller = db.Column(UUID(), db.ForeignKey('controller.id', ondelete="CASCADE"), nullable=False)

    keep_vms_on = db.Column(db.Boolean(), nullable=False, default=False)

    # ----- ----- ----- ----- ----- ----- -----
    # Constants:
    POOL_TYPE_LABEL = 'pool_type'
    EXTRA_ORDER_FIELDS = ['controller_address', 'users_count', 'vms_count', 'pool_type']

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    async def has_vms(self):
        """Проверяем наличие виртуальных машин"""

        vm_count = await db.select([db.func.count(Vm.id)]).where(
            Vm.pool_id == self.pool_id).gino.scalar()
        if vm_count == 0:
            return False
        return True

    @property
    async def pool_type(self):
        """Возвращает тип пула виртуальных машин"""
        is_automated = await db.scalar(db.exists().where(AutomatedPool.automated_pool_id == self.pool_id).select())
        return Pool.PoolTypes.AUTOMATED if is_automated else Pool.PoolTypes.STATIC

    @property
    async def template_id(self):
        """Возвращает tenplate_id для автоматического пула, либо null"""
        template_id = await AutomatedPool.select('template_id').where(
            AutomatedPool.automated_pool_id == self.pool_id).gino.scalar()
        print('template_id is {}'.format(template_id))
        return template_id

    @staticmethod
    def build_ordering(query, ordering=None):
        """Построение порядка сортировки"""

        if not ordering or not isinstance(ordering, str):
            return query

        # Определяем порядок сортировки по наличию "-" вначале строки
        if ordering.find('-', 0, 1) == 0:
            reversed_order = True
            ordering = ordering[1:]
        else:
            reversed_order = False

        # TODO: если сделать валидацию переданных полей на сортировку - try не нужен
        try:
            if ordering in Pool.EXTRA_ORDER_FIELDS:
                if ordering == 'controller_address':
                    query = query.order_by(desc(Controller.address)) if reversed_order else query.order_by(
                        Controller.address)
                elif ordering == 'users_count':
                    users_count = db.func.count(PoolUsers.user_id)
                    query = query.order_by(desc(users_count)) if reversed_order else query.order_by(users_count)
                elif ordering == 'vms_count':
                    vms_count = db.func.count(Vm.id)
                    query = query.order_by(desc(vms_count)) if reversed_order else query.order_by(vms_count)
                elif ordering == 'pool_type':
                    query.order_by(text(Pool.POOL_TYPE_LABEL))
            else:
                # Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order
                query = query.order_by(desc(getattr(Pool, ordering))) if reversed_order else query.order_by(
                    getattr(Pool, ordering))
        except AttributeError:
            raise SimpleError('Неверный параметр сортировки {}'.format(ordering))
        return query

    @staticmethod
    def get_pools_query(ordering=None):
        """Содержит только логику запроса
           Обьединяет таблицы Статического и Динамического пула и проставляет им поле pool_type
           SimpePoolsQuery:
            db.select([Pool,
                           AutomatedPool,
                           StaticPool,
                           pool_type]).select_from(Pool.join(AutomatedPool,
                                                             isouter=True).join(StaticPool,
                                                                          isouter=True)

        """

        # Добавление в итоговый НД данных о признаке пула
        pool_type = case([(StaticPool.static_pool_id == None, literal_column("'{}'".format(Pool.PoolTypes.AUTOMATED)))],
                         else_=literal_column("'{}'".format(Pool.PoolTypes.STATIC))).label(Pool.POOL_TYPE_LABEL)

        # Формирование общего селекта из таблиц пулов с добавлением принадлежности пула.
        query = db.select([
                           Pool.pool_id.label('master_id'),
                           Pool,
                           AutomatedPool,
                           StaticPool,
                           pool_type])

        if ordering:
            # Добавляем пересечение с дополнительными внешними таблицами для возможности сортировки
            query = query.select_from(Pool.join(AutomatedPool,
                                                             isouter=True).join(StaticPool,
                                                                                isouter=True).join(Controller,
                                                                                                   isouter=True).join(
            PoolUsers, isouter=True).join(Vm, isouter=True)).group_by(Pool.pool_id, AutomatedPool.automated_pool_id,
                                                                      StaticPool.static_pool_id, Controller.address)
        else:
            # Делаем пересечение только с основными таблицами
            query = query.select_from(Pool.join(AutomatedPool, isouter=True).join(StaticPool, isouter=True))

        # Сортировка
        if ordering:
            query = Pool.build_ordering(query, ordering)
        return query

    @staticmethod
    async def get_pool(pool_id, ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        query = Pool.get_pools_query(ordering=ordering)
        query = query.where(Pool.pool_id == pool_id)
        return await query.gino.first()

    @staticmethod
    async def get_pools(ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        query = Pool.get_pools_query(ordering=ordering)
        return await query.gino.all()

    @staticmethod
    async def get_desktop_type(pool_id):
        # TODO: rewrite
        return await Pool.select('desktop_pool_type').where(Pool.pool_id == pool_id).gino.scalar()

    @staticmethod
    async def get_controller_ip(pool_id):
        query = db.select([Controller.address]).select_from(Controller.join(Pool)).where(
            Pool.pool_id == pool_id)
        return await query.gino.scalar()

    async def get_vm_amount(self, only_free=False):
        """ == None because alchemy can't work with is None"""
        if only_free:
            return await db.select([db.func.count()]).where(
                (Vm.pool_id == self.pool_id) & (Vm.username == None)).gino.scalar()  # noqa
        else:
            return await db.select([db.func.count()]).where(Vm.pool_id == self.pool_id).gino.scalar()

    @staticmethod
    async def get_user_pools(username):
        # TODO: добавить вывод типа OS у VM
        # TODO: добавить вывод состояния пула

        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        pools = Pool.get_pools_query()
        if not user.is_superuser:
            # Можно было бы сразу в Join сделать, но быстро не разобрался как.
            pools = pools.alias().join(PoolUsers).select().where(PoolUsers.user_id == user.id)

        pools_list = await pools.gino.all()

        ans = list()
        for pool in pools_list:
            ans_d = dict()
            ans_d['id'] = str(pool.master_id)
            ans_d['name'] = pool.verbose_name

            # Hardcoded example. Change to model fields.
            ans_d['os_type'] = 'Lin'
            ans_d['status'] = pool.status.value
            ans.append(ans_d)
        return ans

    @staticmethod
    async def get_user_pool(pool_id: str, username=None):
        """Return first hit"""
        # TODO: заменить хардкод поля на нормальное обращение к подзапросу
        query = Pool.get_pools_query()
        query = db.select([
            Controller.address,
            text('anon_1.pool_type'),  # не нашел пока как обратиться корректно к полю из подзапроса
            Vm.id,
        ]).select_from(query.alias().join(Vm, (Vm.username == username) & (Vm.pool_id == text('anon_1.pool_id')),
                                          isouter=True)).where(
            Pool.pool_id == pool_id).order_by(Vm.id)

        return await query.gino.first()

    @staticmethod
    async def get_node_id(pool_id):
        return await Pool.select('node_id').where(Pool.pool_id == pool_id).gino.scalar()

    @staticmethod
    async def get_name(pool_id):
        return await Pool.select('verbose_name').where(Pool.pool_id == pool_id).gino.scalar()

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

    async def soft_delete(self, commit=True):
        """Удаление сущности в статусе ACTIVE у которой нет зависимых сущностей"""

        if self.status != Status.ACTIVE:
            error_msg = 'Удаление не может быть выполнено из-за блокирующего статуса. Выполните форсированное удаление.'
            raise SimpleError(error_msg)

        pool_has_vms = await self.has_vms
        if pool_has_vms:
            raise SimpleError('У пула виртуальных машин есть виртуальные машины. Выполните полное удаление.')

        if commit:
            msg = 'Выполнено удаление пула рабочих столов {id}.'.format(id=self.pool_id)
            await self.delete()
            await Event.create_info(msg)
        return True

    async def force_delete(self, commit=True):
        """Удаление сущности независимо от статуса у которой нет зависимых сущностей"""

        pool_has_vms = await self.has_vms
        if pool_has_vms:
            raise SimpleError('У пула виртуальных машин есть виртуальные машины. Выполните полное удаление.')

        if commit:
            msg = 'Выполнено форсированное удаление пула рабочих столов {id}.'.format(id=self.pool_id)
            await self.delete()
            await Event.create_info(msg)
        return True

    async def full_delete(self, commit=True):
        """Удаление сущности в статусе ACTIVE с удалением зависимых сущностей"""

        if self.status != Status.ACTIVE:
            error_msg = 'Удаление не может быть выполнено из-за блокирующего статуса. Выполните форсированное удаление.'
            raise SimpleError(error_msg)

        if commit:
            pool_type = await self.pool_type
            if pool_type == Pool.PoolTypes.AUTOMATED:
                await AutomatedPool.remove_vms(self.pool_id)
            await self.delete()
            msg = 'Выполнено полное удаление пула рабочих столов {id}.'.format(id=self.pool_id)
            await Event.create_info(msg)
        return True

    @classmethod
    async def activate(cls, pool_id):
        return await Pool.update.values(status=Status.ACTIVE).where(
            Pool.pool_id == pool_id).gino.status()

    @classmethod
    async def deactivate(cls, pool_id):
        return await Pool.update.values(status=Status.FAILED).where(
            Pool.pool_id == pool_id).gino.status()


class StaticPool(db.Model):
    """На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах)."""
    __tablename__ = 'static_pool'
    static_pool_id = db.Column(UUID(), db.ForeignKey('pool.pool_id', ondelete="CASCADE"), primary_key=True)  # TODO: try with id

    @classmethod
    async def get_info(cls, pool_id: str):
        if not pool_id:
            raise AssertionError('Empty uid.')
        pool_data = AutomatedPool.join(Pool).select().where(
            Pool.pool_id == pool_id)
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
            return await super().create(static_pool_id=pool.pool_id)

    @classmethod
    async def soft_update(cls, pool_id, verbose_name, keep_vms_on):
        async with db.transaction() as tx:
            if verbose_name:
                await Pool.update.values(verbose_name=verbose_name).where(Pool.pool_id == pool_id).gino.status()
            if keep_vms_on is not None:
                await Pool.update.values(keep_vms_on=keep_vms_on).where(Pool.pool_id == pool_id).gino.status()
        return True

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

    automated_pool_id = db.Column(UUID(), db.ForeignKey('pool.pool_id', ondelete="CASCADE"), primary_key=True)  # TODO: try with id
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

    create_thin_clones = db.Column(db.Boolean(), nullable=False, default=True)

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
            Pool.pool_id == pool_id)
        return await pool_data.gino.first()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    @classmethod
    async def create(cls, verbose_name, controller_ip, cluster_id, node_id,
                     template_id, datapool_id, min_size, max_size, max_vm_amount, increase_step,
                     max_amount_of_create_attempts, initial_size, reserve_size, total_size, vm_name_template,
                     create_thin_clones):
        """Nested transactions are atomic."""
        async with db.transaction() as tx:
            # Create pool first
            pool = await Pool.create(verbose_name=verbose_name,
                                     cluster_id=cluster_id,
                                     node_id=node_id,
                                     controller_ip=controller_ip)
            # Create automated pool
            return await super().create(automated_pool_id=pool.pool_id,
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
                                        vm_name_template=vm_name_template,
                                        create_thin_clones=create_thin_clones)

    @classmethod
    async def soft_update(cls, pool_id, verbose_name, reserve_size, total_size, vm_name_template, keep_vms_on,
                          create_thin_clones):
        async with db.transaction() as tx:
            if verbose_name:
                await Pool.update.values(verbose_name=verbose_name).where(
                    Pool.pool_id == pool_id).gino.status()
            auto_pool_kwargs = dict()
            if reserve_size:
                auto_pool_kwargs['reserve_size'] = reserve_size
            if total_size:
                auto_pool_kwargs['total_size'] = total_size
            if vm_name_template:
                auto_pool_kwargs['vm_name_template'] = vm_name_template
            if auto_pool_kwargs:
                await AutomatedPool.update.values(**auto_pool_kwargs).where(
                    AutomatedPool.automated_pool_id == pool_id).gino.status()
            if keep_vms_on is not None:
                await Pool.update.values(keep_vms_on=keep_vms_on).where(Pool.pool_id == pool_id).gino.status()
            if create_thin_clones is not None:
                await AutomatedPool.update.values(create_thin_clones=create_thin_clones).where(
                    AutomatedPool.automated_pool_id == pool_id).gino.status()
        return True

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

        # uid = str(uuid.uuid4())[:7]учзфтв
        # TODO: отказатся от UUID
        params = {
            'verbose_name': "{}-{}-{}".format(vm_name_template, domain_index, str(uuid.uuid4())[:7]),
            'name_template': vm_name_template,
            'domain_id': str(self.template_id),
            'datapool_id': str(self.datapool_id),  # because of UUID
            'controller_ip': await self.controller_ip,
            'node_id': str(await self.node_id),
            'create_thin_clones': self.create_thin_clones
        }

        # try to create vm
        for i in range(self.max_amount_of_create_attempts):
            print('add_domain № {}, attempt № {}'.format(domain_index, i))
            # send request to create vm
            try:
                vm_info = await Vm.copy(**params)
                current_vm_task_id = vm_info['task_id']
            except HttpError as E:
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
            print('is_vm_successfully_created', is_vm_successfully_created)
            if is_vm_successfully_created:
                await Vm.create(id=vm_info['id'], pool_id=str(self.automated_pool_id),
                                template_id=str(self.template_id))
                return vm_info
            else:
                await asyncio.sleep(0.1)  # Пожалеем контроллер и подождем чуть-чуть
                continue  # go to try again

        raise VmCreationError('Can\'t create VM')

    @classmethod
    async def remove_vms(cls, pool_id):
        """Интерфейс для запуска команды HttpClient на удаление виртуалки"""
        # TODO: была мысль обернуть в транзакции, но команда уходит на ECP, поэтому если команда
        #  отработает для одной виртуалки, то ее уже не вернуть.

        query = db.select([Vm.id, Controller.address]).select_from(Vm.join(Pool).join(Controller)).where(
            Vm.pool_id == pool_id)

        vms_list = await query.gino.all()
        for row in vms_list:
            await Vm.remove_vm(controller_ip=row[1], vm_id=row[0])
            msg = 'Запущено удаление виртуальной машины {id} на ECP.'.format(id=row[0])
            await Event.create_info(msg)
        return True

    async def add_initial_vms(self):
        """Create required initial amount of VMs for auto pool"""
        # Основная логика сохранена со старой схемы. На рефакторинг внутреннего кода пока нет времени.
        # TODO: главное, что бы хотелось тут и в других местах создания виртуалок - отправлять диапазоны виртуалок

        print('Add initial vms:')
        # # fetch_template_info was commented on previous version
        # template_info = await GetDomainInfo(controller_ip=pool_args_dict['controller_ip'],
        #                                     domain_id=pool_args_dict['template_id'])

        await Event.create_info('Automated pool creation started')

        vm_list = list()
        try:
            for i in range(self.initial_size):
                vm_index = 1 + i
                vm = await self.add_vm(vm_index)
                vm_list.append(vm)

                # notify VDI front about progress(WS)
                msg = 'Automated pool creation. Created {} VMs from {}'.format(vm_index, self.initial_size)
                await Event.create_info(msg)

                msg_dict = dict(msg=msg,
                                mgs_type='data',
                                event='pool_creation_progress',
                                pool_id=str(self.automated_pool_id),
                                domain_index=vm_index,
                                domain_verbose_name=vm['verbose_name'],
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
            await Event.create_info(msg)
        else:
            msg = 'Automated pool created with errors. VMs created: {}. Required: {}'.format(len(vm_list),
                                                                                             self.initial_size)
            await Event.create_error(msg)

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
        # Пробросить исключение, если споткнулись на создании машин
        if not is_creation_successful:
            raise VmCreationError('Не удалось создать необходимое число машин.')

    async def create_pool(self):
        """Корутина создания автом. пула"""
        # locks
        async with pool_task_manager.get_pool_lock(str(self.automated_pool_id)).lock:
            async with pool_task_manager.get_template_lock(str(self.template_id)).lock:
                try:
                    await self.add_initial_vms()
                    await self.activate()

                    msg = 'Automated pool {id} created.'.format(id=self.automated_pool_id)
                    await Event.create_info(msg)
                except VmCreationError as E:
                    print('exp__', E.__class__.__name__)
                    await self.deactivate()

    async def expand_pool_if_requred(self):
        """
        Корутина расширения автом. пула
        Check and expand pool if required
        :return:
        """
        async with pool_task_manager.get_pool_lock(str(self.automated_pool_id)).lock:
            async with pool_task_manager.get_template_lock(str(self.template_id)).lock:
                # TODO: rewrite
                # TODO: код перенесен, чтобы работал. Принципиально не перерабатывался.
                # Check that total_size is not reached
                pool = await Pool.get(self.automated_pool_id)
                vm_amount_in_pool = await pool.get_vm_amount()

                # If reached then do nothing
                if vm_amount_in_pool >= self.total_size:
                    return

                # Число машин в пуле, неимеющих пользователя
                free_vm_amount = await pool.get_vm_amount(only_free=True)

                # Если подогретых машин слишком мало, то пробуем добавить еще
                if self.reserve_size > free_vm_amount:
                    # Max possible amount of VMs which we can add to the pool
                    max_possible_amount_to_add = self.total_size - vm_amount_in_pool
                    # Real amount that we can add to the pool
                    real_amount_to_add = min(max_possible_amount_to_add, self.increase_step)
                    # add VMs.
                    try:
                        # TODO: очень странная логика. Может есть смысл создавать как-то диапазоном на стороне ECP?
                        for i in range(0, real_amount_to_add):
                            domain_index = vm_amount_in_pool + i
                            await self.add_vm(domain_index)
                    except VmCreationError:
                        print('Vm creating error')
                        # TODO: log that we cant expand the pool.  Mark pool as broken?
                        pass

    async def activate(self):
        return await Pool.activate(self.automated_pool_id)

    async def deactivate(self):
        return await Pool.deactivate(self.automated_pool_id)


class PoolUsers(db.Model):
    __tablename__ = 'pools_users'
    pool_id = db.Column(UUID(), db.ForeignKey('pool.pool_id', ondelete="CASCADE"))
    user_id = db.Column(UUID(), db.ForeignKey('user.id', ondelete="CASCADE"))

    @staticmethod
    async def check_row_exists(pool_id, user_id):
        row = await PoolUsers.select().where((PoolUsers.user_id == user_id) and
                                             (PoolUsers.pool_id == pool_id)).gino.all()
        return row
