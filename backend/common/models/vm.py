# -*- coding: utf-8 -*-
import uuid
import asyncio

from sqlalchemy import desc
from enum import IntEnum

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as AlchemyEnum
from asyncpg.exceptions import UniqueViolationError
from veil_api_client import DomainConfiguration

from common.database import db
from common.settings import VEIL_OPERATION_WAITING, VEIL_VM_PREPARE_TIMEOUT
from common.veil.veil_gino import get_list_of_values_from_db, EntityType, VeilModel, Status
from common.veil.veil_errors import VmCreationError, SimpleError
from common.languages import lang_init
from common.log.journal import system_logger

from common.models.auth import Entity as EntityModel, EntityRoleOwner as EntityRoleOwnerModel, User as UserModel
from common.models.authentication_directory import AuthenticationDirectory
from common.models.event import Event, EventReadByUser

_ = lang_init()


class VmPowerState(IntEnum):
    """Veil domain power states."""

    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class Vm(VeilModel):
    """Vm однажды включенные в пулы.

    assigned_to_user: Не позволяет автоматически выдавать ВМ пользователю, если эта ВМ уже была однажды выдана.
    """

    __tablename__ = 'vm'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), nullable=False)
    pool_id = db.Column(UUID(), db.ForeignKey('pool.id', ondelete="CASCADE"), unique=False)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    created_by_vdi = db.Column(db.Boolean(), nullable=False, default=False)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    assigned_to_user = db.Column(db.Boolean(), nullable=False, default=False)

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
                     created_by_vdi=False, status=Status.ACTIVE, assigned_to_user=False):
        await system_logger.debug(_('Create VM {} on VDI DB.').format(verbose_name))
        try:
            vm = await super().create(id=id,
                                      pool_id=pool_id,
                                      template_id=template_id,
                                      verbose_name=verbose_name,
                                      created_by_vdi=created_by_vdi,
                                      status=status,
                                      assigned_to_user=assigned_to_user)
        except Exception as E:
            raise VmCreationError(str(E))
        return vm

    async def soft_delete(self, creator, remove_on_controller=True):
        if remove_on_controller and self.created_by_vdi:
            try:
                domain_entity = await self.vm_client
                if not domain_entity:
                    raise AssertionError(_('VM has no api client.'))
                await domain_entity.info()
                # Если машина уже заведена в АД - пытаемся ее вывести
                active_directory_object = await AuthenticationDirectory.query.where(
                    AuthenticationDirectory.status == Status.ACTIVE).gino.first()
                already_in_domain = await domain_entity.in_ad if domain_entity.os_windows else False
                if domain_entity.os_windows and already_in_domain:
                    await system_logger.info(_('Removing {} from domain.').format(self.verbose_name),
                                             entity=self.entity)
                    action_response = await domain_entity.rm_from_ad(login=active_directory_object.service_username,
                                                                     password=active_directory_object.password,
                                                                     restart=False)
                    action_task = action_response.task
                    task_completed = False
                    while not task_completed:
                        await asyncio.sleep(VEIL_OPERATION_WAITING)
                        task_completed = await action_task.finished
                # Отправляем задачу удаления ВМ на ECP.
                delete_response = await domain_entity.remove(full=True)
                delete_task = delete_response.task
                task_completed = False
                while not task_completed:
                    await asyncio.sleep(VEIL_OPERATION_WAITING)
                    task_completed = await delete_task.finished
                # Если задача выполнена с ошибкой прокидываем исключение выше
                task_success = await delete_task.success
                if not task_success:
                    raise AssertionError(
                        _('VM deletion task {} finished with error.').format(delete_task.api_object_id))
                await system_logger.debug(_('VM {} removed from ECP.').format(self.verbose_name), entity=self.entity)
            except Exception as e:  # noqa
                # Сейчас нас не заботит что пошло не так при удалении на ECP.
                msg = _('VM {} deletion task finished with error.').format(self.verbose_name)
                description = str(e)
                await system_logger.warning(message=msg, description=description, entity=self.entity, user=creator)
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
                await self.soft_update(id=self.id, creator=creator, assigned_to_user=True)
                await system_logger.info(
                    _('User {} has been included to VM {}.').format(user.username, self.verbose_name),
                    user=creator, entity=self.entity)
        except UniqueViolationError:
            raise SimpleError(_('{} already has permission.').format(type(self).__name__), user=creator)
        return ero

    async def remove_users(self, creator: str, users_list: list):
        entity = EntityModel.select('id').where(
            (EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))
        # TODO: временное решение. Скорее всего потом права отзываться будут на конкретные сущности
        await system_logger.info(_('VM {} is clear from users.').format(self.verbose_name), user=creator,
                                 entity=self.entity)
        if not users_list:
            return await EntityRoleOwnerModel.delete.where(EntityRoleOwnerModel.entity_id == entity).gino.status()
        return await EntityRoleOwnerModel.delete.where(
            (EntityRoleOwnerModel.user_id.in_(users_list)) & (EntityRoleOwnerModel.entity_id == entity)).gino.status()

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
        # Прерываем выполнение при отсутствии клиента
        if not vm_controller.veil_client:
            raise AssertionError(_('There is no client for controller {}.').format(vm_controller.verbose_name))
        vm_client = vm_controller.veil_client.domain()
        inner_retry_count = 0
        while True:
            inner_retry_count += 1
            await system_logger.debug('Trying to create VM on ECP with verbose_name={}'.format(verbose_name))

            # Send request to create vm
            vm_configuration = DomainConfiguration(verbose_name=verbose_name, node=node_id, datapool=datapool_id,
                                                   parent=domain_id, thin=create_thin_clones)
            create_response = await vm_client.create(domain_configuration=vm_configuration)

            if create_response.success:
                await system_logger.debug('Request to create VM sent without surprise. Leaving while.')
                break

            ecp_errors_list = create_response.data.get('errors')
            if isinstance(ecp_errors_list, list) and len(ecp_errors_list):
                first_error_dict = ecp_errors_list[0]
            else:
                first_error_dict = dict()

            ecp_detail = first_error_dict.get('detail')
            msg = _('ECP VeiL controller {} error.').format(vm_controller.verbose_name)
            entity = {'entity_type': EntityType.CONTROLLER, 'entity_uuid': None}
            await system_logger.debug(message=msg, description=ecp_detail, entity=entity)

            # TODO: задействовать новые коды ошибок VeiL
            # Сейчас только англ, т.к. veil-api-client хардкодит английский язык при обмене
            if ecp_detail and 'not enough free space on data pool' in ecp_detail:
                await system_logger.debug(_('Controller has not free space for creating new VM.'))
                raise VmCreationError(_('Not enough free space on data pool.'))

            elif ecp_detail and 'passed node is not valid' in ecp_detail:
                await system_logger.debug(_('Unknown node {}.').format(node_id))
                raise VmCreationError(_('Controller can`t create VM. Unknown node.'))

            elif ecp_detail and inner_retry_count < 10:
                # Тут мы предполагаем, что контроллер заблокирован выполнением задачи. Это может быть и не так,
                # но сейчас нам это не понятно.
                await system_logger.debug(_('Possibly blocked by active task on ECP. Wait before next try.'))
                await asyncio.sleep(10)
            else:
                await system_logger.debug(_('Something went wrong. Interrupt while.'))
                raise VmCreationError('Can`t create VM')

            await system_logger.debug('One more try')
            await asyncio.sleep(1)

        response_data = create_response.data
        copy_result = dict(id=response_data.get('entity'),
                           task_id=response_data.get('_task', dict()).get('id'),
                           verbose_name=verbose_name)
        return copy_result

    @staticmethod
    async def remove_vm(vm_id, creator, remove_vms_on_controller):
        vm = await Vm.get(vm_id)
        await vm.soft_delete(creator=creator, remove_on_controller=remove_vms_on_controller)
        await system_logger.info(_('VM {} has been removed from the pool.').format(vm.verbose_name), entity=vm.entity)

    @staticmethod
    async def remove_vm_with_timeout(vm_id, creator, remove_vms_on_controller):
        try:
            await asyncio.wait_for(Vm.remove_vm(vm_id, creator, remove_vms_on_controller), VEIL_VM_PREPARE_TIMEOUT)
        except asyncio.TimeoutError:
            vm = await Vm.get(vm_id)
            await system_logger.error(message=_('VM {} deleting cancelled by timeout.').format(vm.verbose_name))
        except ValueError as err_msg:
            await system_logger.error(message=str(err_msg))

    @staticmethod
    async def remove_vms(vm_ids, creator, remove_vms_on_controller=False):
        """Remove given vms"""
        if not vm_ids:
            return False
        # Ради логгирования и вывода из домена удаление делается по 1 ВМ.
        await asyncio.gather(*[Vm.remove_vm_with_timeout(vm_id, creator, remove_vms_on_controller) for vm_id in vm_ids])
        return True

    @staticmethod
    async def event(event_id):
        query = Event.outerjoin(EventReadByUser).outerjoin(UserModel).outerjoin(EntityModel).select().where(
            Event.id == event_id)

        event = await query.gino.load(
            Event.distinct(Event.id).load(add_read_by=UserModel.distinct(UserModel.id), add_entity=EntityModel)).first()

        if not event:
            raise SimpleError(_('No such event.'))

        return event

    async def events(self, limit, offset):
        entity_query = EntityModel.select('id').where(
            (EntityModel.entity_type == EntityType.VM) & (EntityModel.entity_uuid == self.id))

        query = Event.outerjoin(EventReadByUser).outerjoin(UserModel).outerjoin(EntityModel).select().where(
            Event.entity_id.in_(entity_query))

        events = await query.order_by(desc(Event.created)).limit(limit).offset(offset).gino.load(
            Event.distinct(Event.id).load(add_read_by=UserModel.distinct(UserModel.id), add_entity=EntityModel)).all()

        return events

    async def events_count(self):
        entity_query = EntityModel.select('id').where(
            (EntityModel.entity_type == EntityType.VM) & (EntityModel.entity_uuid == self.id))

        query = Event.outerjoin(EventReadByUser).outerjoin(UserModel).outerjoin(EntityModel).select().where(
            Event.entity_id.in_(entity_query))

        events_count = await db.select([db.func.count()]).select_from(query.alias()).gino.scalar()
        return events_count

    # Удаленные действия над ВМ - новый код
    async def action(self, action_name: str, force: bool = False):
        """Пересылает команду управления ВМ на ECP VeiL."""
        # TODO: проверить есть ли вообще такое действие в допустимых?
        vm_controller = await self.controller
        # Прерываем выполнение при отсутствии клиента
        if not vm_controller.veil_client:
            raise AssertionError(_('There is no client for controller {}.').format(vm_controller.verbose_name))
        veil_domain = vm_controller.veil_client.domain(domain_id=self.id_str)
        domain_action = getattr(veil_domain, action_name)
        action_response = await domain_action(force=force)
        if not action_response.success:
            raise ValueError(_('VeiL domain request error.'))
        # TODO: метод ожидания задачи
        action_task = action_response.task
        task_completed = False
        while not task_completed:
            await asyncio.sleep(VEIL_OPERATION_WAITING)
            task_completed = await action_task.finished
        task_success = await action_task.success
        return task_success

    @property
    async def vm_client(self):
        """Клиент с сущностью domain на ECP VeiL."""
        vm_controller = await self.controller
        if not vm_controller.veil_client:
            return
        return vm_controller.veil_client.domain(domain_id=self.id_str)

    # TODO: reset
    # TODO: resume

    async def start(self, creator='system'):
        """Включает ВМ - Пересылает start для ВМ на ECP VeiL."""
        domain_entity = await self.vm_client
        if not domain_entity:
            return
        domain_response = await domain_entity.info()
        if not domain_response.success:
            raise ValueError(_('VeiL domain request error.'))

        if not domain_entity.powered:
            # await system_logger.info(_('Powering on {}').format(self.verbose_name), entity=self.entity)
            task_success = await self.action('start')
            await system_logger.info(_('VM {} is powered.').format(self.verbose_name), user=creator, entity=self.entity)
            return task_success

    async def shutdown(self, creator='system', force=False):
        """Выключает ВМ - Пересылает shutdown для ВМ на ECP VeiL."""
        domain_entity = await self.vm_client
        if not domain_entity:
            return
        domain_response = await domain_entity.info()
        if not domain_response.success:
            raise ValueError(_('VeiL domain request error.'))

        if domain_entity.power_state == VmPowerState.OFF:
            await system_logger.info(_('VM {} already shutdown.').format(self.verbose_name), user=creator,
                                     entity=self.entity)
        else:
            # await system_logger.info(_('Powering off {}').format(self.verbose_name), entity=self.entity)
            task_success = await self.action('shutdown', force=force)

            if force:
                await system_logger.info(_('VM {} is force shutdown.').format(self.verbose_name), user=creator,
                                         entity=self.entity)
            else:
                await system_logger.info(_('VM {} is shutdown.').format(self.verbose_name), user=creator,
                                         entity=self.entity)
            return task_success

    async def reboot(self, creator='system', force=False):
        """Перезагружает ВМ - Пересылает reboot для ВМ на ECP VeiL."""
        domain_entity = await self.vm_client
        if not domain_entity:
            return
        domain_response = await domain_entity.info()
        if not domain_response.success:
            raise ValueError(_('VeiL domain request error.'))

        if domain_entity.power_state == VmPowerState.OFF:
            raise SimpleError(_('VM {} is shutdown. Please power this.').format(self.verbose_name), user=creator,
                              entity=self.entity)
        else:
            # await system_logger.info(_('Rebooting {}').format(self.verbose_name), entity=self.entity)
            task_success = await self.action('reboot', force=force)

            if force:
                await system_logger.info(_('VM {} was force reboot.').format(self.verbose_name), user=creator,
                                         entity=self.entity)
            else:
                await system_logger.info(_('VM {} was reboot.').format(self.verbose_name), user=creator,
                                         entity=self.entity)
            return task_success

    async def suspend(self, creator='system'):
        """Ставит на паузу ВМ - Пересылает suspend для ВМ на ECP VeiL."""
        domain_entity = await self.vm_client
        if not domain_entity:
            return
        domain_response = await domain_entity.info()
        if not domain_response.success:
            raise ValueError(_('VeiL domain request error.'))

        if domain_entity.powered:
            # await system_logger.info(_('Suspending {}').format(self.verbose_name), entity=self.entity)
            task_success = await self.action('suspend')
            await system_logger.info(_('VM {} is suspended.').format(self.verbose_name), user=creator,
                                     entity=self.entity)
            return task_success
        else:
            raise SimpleError(_('VM {} is shutdown. Please power this.').format(self.verbose_name), user=creator,
                              entity=self.entity)

    async def prepare(self, active_directory_obj: AuthenticationDirectory = None, ad_cn_pattern: str = None):
        """Check that domain remote-access is enabled and domain is powered on.

        Вся процедура должна продолжаться не более 10 минут для 1 ВМ.
        """
        # TODO: обработка ошибок ответов VeiL
        # TODO: задача может завершиться с ошибкой
        # TODO: записать назначенный hostname в БД, если он успешно назначен?
        # По ходу выполнения операций в список будут дописываться значения из которых соберется итоговый комментарий
        description_list = list()
        domain_entity = await self.vm_client
        if not domain_entity:
            return
        # Получаем состояние параметров ВМ
        domain_response = await domain_entity.info()
        if not domain_response.success:
            raise ValueError(_('VeiL domain request error.'))

        # Проверяем настройки удаленного доступа
        if not domain_entity.remote_access:
            # Удаленный доступ выключен, нужно включить и ждать
            action_response = await domain_entity.enable_remote_access()
            await system_logger.debug(_('Enabling remote access for {}.').format(self.verbose_name), entity=self.entity)
            if not action_response.success:
                # Вернуть исключение?
                raise ValueError(_('VeiL domain request error.'))
            if action_response.status_code == 200:
                # Задача не встала в очередь, а выполнилась немедленно. Такого не должно быть.
                raise ValueError(_('Task has`t been created.'))
            if action_response.status_code == 202:
                # Была установлена задача. Необходимо дождаться ее выполнения.
                # TODO: метод ожидания задачи
                action_task = action_response.task
                task_completed = False
                while not task_completed:
                    await asyncio.sleep(VEIL_OPERATION_WAITING)
                    task_completed = await action_task.finished

                # Если задача выполнена с ошибкой - прерываем выполнение
                task_success = await action_task.success
                if not task_success:
                    raise ValueError(
                        _('VM remote access task {} finished with error.').format(action_task.api_object_id))

                # Обновляем параметры ВМ
                await domain_entity.info()
            description_list.append(_('Remote access enabled.'))

        # Включаем виртуальную машину. Если машина не включится - не активируется гостевой агент
        await self.start()
        await domain_entity.info()

        # TODO: метод ожидания задачи
        # Ждем активацию гостевого агента
        while not domain_entity.guest_agent.qemu_state:
            await system_logger.debug(_('Waiting guest agent activation for {}.').format(self.verbose_name),
                                      entity=self.entity)
            await asyncio.sleep(VEIL_OPERATION_WAITING)
            # Обновляем параметры ВМ
            await domain_entity.info()

        await system_logger.debug('\n\nhostname: {}, verbose_name: {}\n\n'.format(domain_entity.hostname, self.verbose_name))
        # Задание hostname
        if domain_entity.hostname != self.verbose_name:
            await system_logger.debug(_('Setting hostname for {}.').format(self.verbose_name), entity=self.entity)
            action_response = await domain_entity.set_hostname(hostname=self.verbose_name)
            # TODO: метод ожидания задачи
            action_task = action_response.task
            task_completed = False
            while not task_completed:
                await asyncio.sleep(VEIL_OPERATION_WAITING)
                task_completed = await action_task.finished

            # Если задача выполнена с ошибкой - прерываем выполнение
            task_success = await action_task.success
            if not task_success:
                raise ValueError(
                    _('VM hostname setting task {} finished with error.').format(action_task.api_object_id))

            # Обновляем параметры ВМ
            await domain_entity.info()
            description_list.append(_('Hostname {} has been set.').format(self.verbose_name))

        # Ждем активацию гостевого агента
        while not domain_entity.guest_agent.qemu_state:
            await system_logger.debug(_('Waiting guest agent activation for {}.').format(self.verbose_name),
                                      entity=self.entity)
            await asyncio.sleep(VEIL_OPERATION_WAITING)
            # Обновляем параметры ВМ
            await domain_entity.info()

        # Заведение в домен
        already_in_domain = await domain_entity.in_ad if domain_entity.os_windows else False
        if active_directory_obj and domain_entity.os_windows and not already_in_domain:
            await system_logger.debug(_('Adding {} to domain.').format(self.verbose_name), entity=self.entity)
            action_response = await domain_entity.add_to_ad(domain_name=active_directory_obj.domain_name,
                                                            login=active_directory_obj.service_username,
                                                            password=active_directory_obj.password)
            # TODO: метод ожидания задачи
            action_task = action_response.task
            task_completed = False
            while not task_completed:
                await asyncio.sleep(VEIL_OPERATION_WAITING)
                task_completed = await action_task.finished

            # Если задача выполнена с ошибкой - прерываем выполнение
            task_success = await action_task.success
            if not task_success:
                # TODO: возможно первая ошибка нас не интересует
                await system_logger.error(_('VM {} domain including task failed.').format(self.verbose_name),
                                          description=action_task.error_message)
                raise ValueError(
                    _('VM domain include task {} finished with error.').format(action_task.api_object_id))

            await domain_entity.info()

            # Ждем активацию гостевого агента
            while not domain_entity.guest_agent.qemu_state:
                await asyncio.sleep(VEIL_OPERATION_WAITING)
                await domain_entity.info()

            description_list.append(
                _('VM has been added to Windows domain {}.').format(active_directory_obj.domain_name))

            # Заводим в контейнер в Active Directory
            if ad_cn_pattern:
                action_response = await domain_entity.add_to_ad_group(self.verbose_name,
                                                                      active_directory_obj.service_username,
                                                                      active_directory_obj.password,
                                                                      ad_cn_pattern)
                # Ожидаем выполнения задачи
                action_task = action_response.task
                task_completed = False
                while not task_completed:
                    await asyncio.sleep(VEIL_OPERATION_WAITING)
                    task_completed = await action_task.finished

                # Если задача выполнена с ошибкой - прерываем выполнение
                task_success = await action_task.success
                if not task_success:
                    raise ValueError(
                        _('VM domain container adding task {} finished with error.').format(action_task.api_object_id))
                # Добавляем в список отработанных действий
                description_list.append(
                    _('VM has been added to Windows domain container(s) {}.').format(ad_cn_pattern))
        # Протоколируем успех
        msg = _('VM {} has been prepared.').format(self.verbose_name)
        description = ', '.join(description_list)
        await system_logger.info(message=msg, entity=self.entity, description=description)

    async def prepare_with_timeout(self, active_directory_obj: AuthenticationDirectory = None, ad_cn_pattern: str = None):
        """Подготовка ВМ с ограничением по времени."""
        try:
            await asyncio.wait_for(self.prepare(active_directory_obj, ad_cn_pattern), VEIL_VM_PREPARE_TIMEOUT)
        except asyncio.TimeoutError:
            await system_logger.error(message=_('{} preparation cancelled by timeout.').format(self.verbose_name),
                                      entity=self.entity)
        except ValueError as err_msg:
            await system_logger.error(message=str(err_msg))
