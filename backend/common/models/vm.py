# -*- coding: utf-8 -*-
import uuid
import asyncio
from enum import IntEnum

from sqlalchemy.dialects.postgresql import UUID
from asyncpg.exceptions import UniqueViolationError
from veil_api_client import DomainConfiguration

from common.database import db
from common.veil.veil_gino import get_list_of_values_from_db, EntityType, VeilModel
from common.veil.veil_errors import VmCreationError, SimpleError
from common.languages import lang_init
from common.log.journal import system_logger

from common.models.auth import Entity as EntityModel, EntityRoleOwner as EntityRoleOwnerModel, User as UserModel


_ = lang_init()


class VmPowerState(IntEnum):
    """Veil domain power states."""

    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class Vm(VeilModel):
    """
    ACTIONS = ('start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot')
    POWER_STATES = ('unknown', 'power off', 'power on and suspended', 'power on')
    """
    # TODO: положить в таблицу данные о удаленном подключении из ECP
    # TODO: ip address of domain?
    # TODO: port of domain?

    __tablename__ = 'vm'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), nullable=False)
    pool_id = db.Column(UUID(), db.ForeignKey('pool.id', ondelete="CASCADE"), unique=False)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    created_by_vdi = db.Column(db.Boolean(), nullable=False, default=False)
    broken = db.Column(db.Boolean(), nullable=False, default=False)

    @property
    def id_str(self):
        return str(self.id)

    @property
    def entity_type(self):
        return EntityType.VM

    @property
    async def entity_obj(self):
        return await EntityModel.query.where(
            (EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id)).gino.first()

    @property
    def controller_query(self):
        from common.models.controller import Controller as ControllerModel
        from common.models.pool import Pool as PoolModel
        return db.select([ControllerModel.address]).select_from(
            ControllerModel.join(PoolModel.query.where(PoolModel.id == self.pool_id).alias()).alias())

    @property
    async def controller_address(self):
        return await self.controller_query.gino.scalar()

    @property
    async def username(self):
        entity_query = EntityModel.select('id').where((EntityModel.entity_type == EntityType.VM) & (EntityModel.entity_uuid == self.id))
        ero_query = EntityRoleOwnerModel.select('user_id').where(EntityRoleOwnerModel.entity_id == entity_query)
        user_id = await ero_query.gino.scalar()
        user = await UserModel.get(user_id) if user_id else None
        return user.username if user else None

    @property
    async def pool(self):
        """Возвращает объект модели пула."""
        from common.models.pool import Pool as PoolModel
        return await PoolModel.get(self.pool_id)

    @property
    async def controller(self):
        """Возвращает объект модели контроллера."""
        from common.models.controller import Controller as ControllerModel
        vm_pool = await self.pool
        return await ControllerModel.get(vm_pool.controller)

    # ----- ----- ----- ----- ----- ----- -----

    @classmethod
    async def create(cls, pool_id, template_id, verbose_name, id=None,
                     created_by_vdi=False, broken=False):
        await system_logger.debug(_('Create VM {} on VDI DB.').format(verbose_name))
        try:
            vm = await super().create(id=id,
                                      pool_id=pool_id,
                                      template_id=template_id,
                                      verbose_name=verbose_name,
                                      created_by_vdi=created_by_vdi,
                                      broken=broken)
        except Exception as E:
            raise VmCreationError(str(E))

        await system_logger.info(_('VM {} is created').format(verbose_name), entity=vm.entity)

        return vm

    async def soft_delete(self, creator, remove_on_controller=True):
        if remove_on_controller and self.created_by_vdi:
            domain_client = await self.vm_client
            await domain_client.remove(full=True)

            await system_logger.debug(_('Vm {} removed from ECP.').format(self.verbose_name))
        status = await super().soft_delete(creator=creator)
        return status

    # TODO: очевидное дублирование однотипного кода. Переселить это все в универсальный метод
    async def add_user(self, user_id, creator):
        entity = await self.entity_obj
        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityRoleOwnerModel.create(entity_id=entity.id, user_id=user_id)
                user = await UserModel.get(user_id)
                await system_logger.info(
                    _('User {} has been included to VM {}').format(user.username, self.verbose_name),
                    user=creator, entity=self.entity)
        except UniqueViolationError:
            raise SimpleError(_('{} already has permission.').format(type(self).__name__), user=creator)
        return ero

    async def remove_users(self, creator, users_list: list):
        entity = EntityModel.select('id').where((EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))
        # TODO: временное решение. Скорее всего потом права отзываться будут на конкретные сущности
        await system_logger.info(_('VM {} is clear from users').format(self.verbose_name), user=creator, entity=self.entity)
        if not users_list:
            return await EntityRoleOwnerModel.delete.where(EntityRoleOwnerModel.entity_id == entity).gino.status()
        return await EntityRoleOwnerModel.delete.where(
            (EntityRoleOwnerModel.user_id.in_(users_list)) & (EntityRoleOwnerModel.entity_id == entity)).gino.status()

    # @staticmethod
    # async def get_vm_id(pool_id, user_id):
    #     # TODO: deprecated
    #     entity_query = EntityModel.select('entity_uuid').where(
    #         (EntityModel.entity_type == EntityType.VM) & (
    #             EntityModel.id.in_(EntityRoleOwnerModel.select('entity_id').where(EntityRoleOwnerModel.user_id == user_id))))
    #     vm_query = Vm.select('id').where((Vm.id.in_(entity_query)) & (Vm.pool_id == pool_id))
    #     return await vm_query.gino.scalar()

    # @staticmethod
    # async def get_vm(pool_id, user_id):
    #     entity_query = EntityModel.select('entity_uuid').where(
    #         (EntityModel.entity_type == EntityType.VM) & (
    #             EntityModel.id.in_(EntityRoleOwnerModel.select('entity_id').where(EntityRoleOwnerModel.user_id == user_id))))
    #     vm_query = Vm.query.where((Vm.id.in_(entity_query)) & (Vm.pool_id == pool_id))
    #     return await vm_query.gino.first()

    @staticmethod
    async def get_all_vms_ids():
        # TODO: какой-то бесполезный метод
        return await get_list_of_values_from_db(Vm, Vm.id)

    @staticmethod
    async def get_vms_ids_in_pool(pool_id):
        """Get all vm_ids as list of strings"""
        vm_ids_data = await Vm.select('id').where((Vm.pool_id == pool_id)).gino.all()
        vm_ids = [str(vm_id) for (vm_id,) in vm_ids_data]
        return vm_ids

    @staticmethod
    def ready_to_connect(**info) -> bool:
        """Checks parameters indicating availability for connection."""
        # TODO: сейчас не используется?
        power_state = info.get('user_power_state', 0)
        remote_access = info.get('remote_access', False)
        return power_state != 3 or not remote_access

    @staticmethod
    async def copy(verbose_name: str, domain_id: str, datapool_id: str, controller_id,
                   node_id: str, create_thin_clones: bool):
        """Copy existing VM template for new VM create."""
        from common.models.controller import Controller as ControllerModel

        vm_controller = await ControllerModel.get(controller_id)
        vm_client = vm_controller.veil_client.domain()
        inner_retry_count = 0
        while True:
            inner_retry_count += 1
            await system_logger.debug(_('Trying to create VM on ECP with verbose_name={}').format(verbose_name))

            # Send request to create vm
            vm_configuration = DomainConfiguration(verbose_name=verbose_name, node=node_id, datapool=datapool_id,
                                                   parent=domain_id, thin=create_thin_clones)
            response = await vm_client.create(domain_configuration=vm_configuration)

            # Check response
            await system_logger.debug('is vm success {}'.format(response.success))
            if response.success:
                await system_logger.debug(_('Request to create VM sent without surprise. Leaving while.'))
                break
            else:
                ecp_errors_list = response.data.get('errors')
                first_error_dict = ecp_errors_list[0] if (isinstance(ecp_errors_list, list) and len(ecp_errors_list)) \
                    else None
                ecp_detail = first_error_dict.get('detail') if first_error_dict else None
                await system_logger.warning(_('ECP error: {}').format(ecp_detail))

                if ecp_detail and ('Недостаточно свободного места в пуле данных' in ecp_detail or 'not enough free space on data pool' in ecp_detail):
                    await system_logger.warning(_('Controller has not free space for creating new VM.'))
                    raise VmCreationError(_('Not enough free space on data pool'))

                elif ecp_detail and ('passed node is not valid' in ecp_detail or 'Переданный узел не действителен' in ecp_detail):
                    await system_logger.warning(_('Unknown node {}').format(node_id))
                    raise VmCreationError(_('Controller can\t create VM. Unknown node.'))

                elif ecp_detail and inner_retry_count < 10:
                    # Тут мы предполагаем, что контроллер заблокирован выполнением задачи. Это может быть и не так,
                    # но сейчас нам это не понятно.
                    await system_logger.debug(_('Possibly blocked by active task on ECP. Wait before next try.'))
                    await asyncio.sleep(10)
                else:
                    await system_logger.debug(_('Something went wrong. Interrupt while.'))
                    raise VmCreationError('Cant create vm')

                await system_logger.debug(_('Wait one more try'))
                await asyncio.sleep(1)

        response = response.data

        copy_result = dict(id=response['entity'],
                           task_id=response['_task']['id'],
                           verbose_name=verbose_name)

        return copy_result

    @staticmethod
    async def remove_vms(vm_ids, creator, remove_vms_on_controller=False):
        """Remove given vms"""

        if not vm_ids:
            return False

        # Удаляем на контроллере
        if remove_vms_on_controller:
            vm_obj = await Vm.get(vm_ids[0])
            http_veil_client = await vm_obj.vm_client
            await http_veil_client.multi_remove(vm_ids)

        # Решили оставить удаление по одной вм из бд. (ради логирования?)
        status = None
        for vm_id in vm_ids:
            vm = await Vm.get(vm_id)
            status = await vm.soft_delete(creator=creator, remove_on_controller=False)
            await system_logger.info(_('Vm {} removed from pool').format(vm.verbose_name), entity=vm.entity)
        return status

    @staticmethod
    async def enable_remote_accesses(controller_address, vm_ids):
        # Функционал внутри prepare
        raise DeprecationWarning()

    # @staticmethod
    # async def get_template_os_type(controller_address, template_id):
    #     vm_http_client = await VmHttpClient.create(controller_address, template_id)
    #     domain_info = await vm_http_client.info()
    #     return domain_info['os_type'] if domain_info else None

    # Удаленные действия над ВМ - новый код
    async def action(self, action_name: str, force: bool = False):
        """Пересылает команду управления ВМ на ECP VeiL."""
        # TODO: проверить есть ли вообще такое действие в допустимых?
        vm_controller = await self.controller
        veil_domain = vm_controller.veil_client.domain(domain_id=self.id_str)
        domain_action = getattr(veil_domain, action_name)
        return await domain_action(force=force)

    @property
    async def vm_client(self):
        """Клиент с сущностью domain на ECP VeiL."""
        vm_controller = await self.controller
        return vm_controller.veil_client.domain(domain_id=self.id_str)

    async def start(self):
        """Пересылает start для ВМ на ECP VeiL."""
        return await self.action('start')

    # TODO: reboot
    # TODO: suspend
    # TODO: reset
    # TODO: shutdown
    # TODO: resume

    async def prepare(self, rdp: bool = False):
        """Check that domain remote-access is enabled and domain is powered on.

        Вся процедура должна продолжаться не более 10 минут для 1 ВМ.
        """
        # TODO: вся задача должна крутиться в таске, чтобы ее можно было отменить
        # TODO: там где для списка ВМ вызывакется задача нужно использовать asyncio.gather()
        # TODO: обработка ошибок ответов VeiL

        domain_client = await self.vm_client
        # Получаем состояние параметров ВМ
        domain_response = await domain_client.info()
        if not domain_response.success:
            # Вернуть исключение?
            raise NotImplementedError()
        # Получаем сущность ВМ из ответа
        domain_entity = domain_response.response[0]
        # Проверяем настройки удаленного доступа
        if not domain_entity.remote_access:
            # Удаленный доступ выключен, нужно включить и ждать
            action_response = await domain_client.enable_remote_access()
            if not action_response.success:
                # Вернуть исключение?
                raise NotImplementedError()
            if action_response.status_code == 200:
                # Задача не встала в очередь, а выполнилась немедленно. Такого не должно быть.
                raise NotImplementedError('Task has`t been created.')
            if action_response.status_code == 202:
                # Была установлена задача. Необходимо дождаться ее выполнения.
                action_task = action_response.task
                task_completed = False
                while not task_completed:
                    await asyncio.sleep(5)
                    task_completed = await action_task.completed
                    await system_logger.debug(
                        'Domain {} remote access enabling task is not completed. Waiting.'.format(self.verbose_name))
                # Обновляем параметры ВМ
                await domain_entity.info()
        # Проверяем состояние виртуальной машины
        if not domain_entity.power_state == VmPowerState.ON:
            # ВМ выключена. Необходимо включить и подождать
            action_response = await domain_entity.start()
            action_task = action_response.task
            task_completed = False
            while not task_completed:
                await asyncio.sleep(5)
                task_completed = await action_task.completed
                await system_logger.debug(
                    'Domain {} start task is not completed. Waiting.'.format(self.verbose_name))
        # Ждем активацию гостевого агента и появления ip (если это rdp)
        while not domain_entity.guest_agent.qemu_state:
            await asyncio.sleep(5)
            await domain_entity.info()
            await system_logger.debug(
                'Domain {} guest agent not available. Waiting.'.format(self.verbose_name))

        # Для подключения по rdp ВМ нужен как минимум 1 ip-адрес
        while rdp and not domain_entity.guest_agent.first_ipv4_ip:
            await asyncio.sleep(10)
            await domain_entity.info()

        # Задание hostname
        action_response = await domain_entity.set_hostname()
        action_task = action_response.task
        task_completed = False
        while not task_completed:
            await asyncio.sleep(5)
            task_completed = await action_task.completed
            await system_logger.debug(
                'Domain {} hostname setting task is not completed. Waiting.'.format(self.verbose_name))

        # TODO: 5. Заведение в домен - только для windows?
        # raise NotImplementedError()
        return
