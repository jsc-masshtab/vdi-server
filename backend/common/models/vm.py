# -*- coding: utf-8 -*-
import asyncio
import uuid
from enum import IntEnum

from asyncpg.exceptions import UniqueViolationError

from sqlalchemy import Enum as AlchemyEnum, desc
from sqlalchemy.dialects.postgresql import UUID

from veil_api_client import (DomainBackupConfiguration,
                             DomainCloneConfiguration,
                             DomainConfiguration)

from common.database import db
from common.languages import lang_init
from common.log.journal import system_logger
from common.models.auth import (
    Entity as EntityModel,
    EntityOwner as EntityOwnerModel,
    User as UserModel,
)
from common.models.authentication_directory import AuthenticationDirectory
from common.models.event import Event, EventReadByUser
from common.settings import (
    DOMAIN_CREATION_MAX_STEP,
    VEIL_GUEST_AGENT_EXTRA_WAITING,
    VEIL_MAX_VM_CREATE_ATTEMPTS,
    VEIL_OPERATION_WAITING,
    VEIL_VM_PREPARE_TIMEOUT,
    VEIL_VM_REMOVE_TIMEOUT
)
from common.veil.veil_api import compare_error_detail
from common.veil.veil_errors import SimpleError, VmCreationError
from common.veil.veil_gino import (
    EntityType,
    Status,
    VeilModel,
    get_list_of_values_from_db,
)
from common.veil.veil_redis import send_cmd_to_cancel_tasks_associated_with_entity

_ = lang_init()


class VmPowerState(IntEnum):
    """Veil domain power states."""

    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class Vm(VeilModel):
    """Vm однажды включенные в пулы."""

    __tablename__ = "vm"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), nullable=False)
    pool_id = db.Column(
        UUID(), db.ForeignKey("pool.id", ondelete="CASCADE"), unique=False
    )
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    created_by_vdi = db.Column(db.Boolean(), nullable=False, default=False)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)

    @property
    def id_str(self):
        return str(self.id)

    @property
    def entity_type(self):
        return EntityType.VM

    @property
    async def entity_obj(self):
        return await EntityModel.query.where(
            (EntityModel.entity_type == self.entity_type)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        ).gino.first()

    @property
    def controller_query(self):
        from common.models.controller import Controller as ControllerModel
        from common.models.pool import Pool as PoolModel

        return db.select([ControllerModel.address]).select_from(
            ControllerModel.join(
                PoolModel.query.where(PoolModel.id == self.pool_id).alias()
            ).alias()
        )

    @property
    async def controller_address(self):
        return await self.controller_query.gino.scalar()

    @property
    async def username(self):
        entity_query = EntityModel.select("id").where(
            (EntityModel.entity_type == EntityType.VM)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )
        ero_query = EntityOwnerModel.select("user_id").where(
            EntityOwnerModel.entity_id == entity_query
        )
        user_id = await ero_query.gino.scalar()
        user = await UserModel.get(user_id) if user_id else None
        return user.username if user else None

    @property
    async def user_id(self):
        entity_query = EntityModel.select("id").where(
            (EntityModel.entity_type == EntityType.VM)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )
        ero_query = EntityOwnerModel.select("user_id").where(
            EntityOwnerModel.entity_id == entity_query
        )
        user_id = await ero_query.gino.scalar()
        return user_id if user_id else None

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

    @property
    async def vm_client(self):
        """Клиент с сущностью domain на ECP VeiL."""
        vm_controller = await self.controller
        if not vm_controller.veil_client:
            return
        return vm_controller.veil_client.domain(domain_id=self.id_str)

    # ----- ----- ----- ----- ----- ----- -----

    @classmethod
    async def create(
        cls,
        pool_id,
        template_id,
        verbose_name,
        id=None,
        created_by_vdi=False,
        status=Status.ACTIVE,
    ):
        await system_logger.debug(_("Create VM {} on VDI DB.").format(verbose_name))
        try:
            vm = await super().create(
                id=id,
                pool_id=pool_id,
                template_id=template_id,
                verbose_name=verbose_name,
                created_by_vdi=created_by_vdi,
                status=status,
            )
        except Exception as E:
            raise VmCreationError(str(E))

        await EntityModel.create(entity_uuid=id, entity_type=EntityType.VM)

        return vm

    @classmethod
    async def multi_soft_delete(cls,
                                controller_client,
                                vms_ids: list,
                                creator: str = "system",
                                remove_from_ecp: bool = False):
        """Групповое удаление ВМ."""
        # Прерываем, если нечего удалять
        if not controller_client:
            raise AssertionError(_("VM has no api client."))
        if not vms_ids:
            return False
        vms_to_delete_on_ecp = None

        # Определяем ВМ, которые нужно удалить на контроллере
        if remove_from_ecp:
            query = cls.select("id").where(
                (cls.id.in_(vms_ids)) & (cls.created_by_vdi == True))  # noqa: E712
            vms_to_delete_on_ecp = await query.gino.all()

        # Удаляем ВМ на ECP, если нашлись
        if remove_from_ecp and vms_to_delete_on_ecp:
            try:
                # Преобразуем UUID в строки
                vms_ids_str = [str(vm_row[0]) for vm_row in vms_to_delete_on_ecp]
                # Формируем запрос на удаление
                domain_client = controller_client.domain()
                multi_delete_response = await domain_client.multi_remove(
                    entity_ids=vms_ids_str, full=True)
                # Если задачу поставить не удалось - прерываемся
                if not multi_delete_response.success:
                    raise AssertionError(_("Failed to create multi-delete task."))

                # Ждем выполнения задачи удаления на ECP VeiL
                multi_delete_task = multi_delete_response.task
                task_completed = False
                while multi_delete_task and not task_completed:
                    await asyncio.sleep(VEIL_OPERATION_WAITING)
                    task_completed = await multi_delete_task.is_finished()

                # Если задача выполнена с ошибкой прокидываем исключение выше
                if multi_delete_task:
                    task_success = await multi_delete_task.is_success()
                    task_id = multi_delete_task.api_object_id
                else:
                    task_success = False
                    task_id = ""

                if not task_success:
                    raise AssertionError(
                        _("VM deletion task {} finished with error.").format(
                            task_id
                        )
                    )

            except asyncio.CancelledError:
                # TODO: отменить задачу удаления вм на ECP VeiL
                # TODO: не до конца понимаю зачем тут это исключение, отмена должна
                # TODO: произойти выше на уровне cls.remove_vms_with_timeout
                raise
            except Exception as e:  # noqa
                # Сейчас нас не заботит, что именно пошло не так при удалении на ECP.
                msg = _(
                    "VM multi-deletion task finished with error. Please see task details on VeiL ECP.")  # noqa: E501
                description = _("VMs: {}.").format(vms_ids)
                await system_logger.warning(
                    message=msg,
                    description=description,
                    entity={"entity_type": EntityType.VM, "entity_uuid": None},
                    user=creator,
                )

        # Удаляем атрибуты владения
        await EntityOwnerModel.multi_remove(ids=vms_ids,
                                            entity_type=EntityType.VM)
        # Удаляем ВМ на брокере.
        # На текущий момент creator не используется в родительском soft_delete,
        # поэтому тут он игнорируется
        return await cls.delete.where(cls.id.in_(vms_ids)).gino.status()

    async def soft_delete(self, creator, remove_on_controller=True):
        # Добавлено 02.06.2021
        await EntityOwnerModel.multi_remove(ids=[self.id],
                                            entity_type=self.entity_type)
        # Отключено 02.06.2021
        # entity = EntityModel.select("id").where(
        #     (EntityModel.entity_type == self.entity_type)
        #     & (EntityModel.entity_uuid == self.id)  # noqa: W503
        # )
        # entity_id = await entity.gino.all()
        # if entity_id:
        #     await EntityOwnerModel.delete.where(
        #         EntityOwnerModel.entity_id == entity
        #     ).gino.status()

        if remove_on_controller and self.created_by_vdi:
            try:
                domain_entity = await self.vm_client
                if not domain_entity:
                    raise AssertionError(_("VM has no api client."))
                delete_response = await domain_entity.remove(full=True)
                delete_task = delete_response.task
                task_completed = False
                while delete_task and not task_completed:
                    await asyncio.sleep(VEIL_OPERATION_WAITING)
                    task_completed = await delete_task.is_finished()
                # Если задача выполнена с ошибкой прокидываем исключение выше
                if delete_task:
                    task_success = await delete_task.is_success()
                    api_object_id = delete_task.api_object_id
                else:
                    task_success = False
                    api_object_id = ""
                if not task_success:
                    raise AssertionError(
                        _("VM deletion task {} finished with error.").format(
                            api_object_id
                        )
                    )
                await system_logger.debug(
                    _("VM {} removed from ECP.").format(self.verbose_name),
                    entity=self.entity,
                )
            except asyncio.CancelledError:
                # Здесь бы в идеале отменять задачу удаления вм на вейле
                raise
            except Exception as e:  # noqa
                # Сейчас нас не заботит что пошло не так при удалении на ECP.
                msg = _("VM {} deletion task finished with error.").format(
                    self.verbose_name
                )
                description = str(e)
                await system_logger.warning(
                    message=msg,
                    description=description,
                    entity=self.entity,
                    user=creator,
                )
        status = await super().soft_delete(creator=creator)
        return status

    async def add_user(self, user_id, creator):
        entity = await self.entity_obj
        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityOwnerModel.create(
                    entity_id=entity.id, user_id=user_id
                )
                user = await UserModel.get(user_id)
                await self.soft_update(
                    id=self.id, status=Status.ACTIVE, creator=creator
                )
                await system_logger.info(
                    _("User {} has been included to VM {}.").format(
                        user.username, self.verbose_name
                    ),
                    user=creator,
                    entity=self.entity,
                )
        except UniqueViolationError:
            raise SimpleError(
                _("{} already has permission.").format(type(self).__name__),
                user=creator,
            )
        return ero

    async def remove_users(self, creator: str, users_list: list):
        entity = EntityModel.select("id").where(
            (EntityModel.entity_type == self.entity_type)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )
        # TODO: временное решение. Скорее всего потом права отзываться будут
        #  на конкретные сущности
        await self.soft_update(id=self.id, status=Status.RESERVED, creator=creator)
        await system_logger.info(
            _("VM {} is clear from users.").format(self.verbose_name),
            user=creator,
            entity=self.entity,
        )
        if not users_list:
            return await EntityOwnerModel.delete.where(
                EntityOwnerModel.entity_id == entity
            ).gino.status()
        return await EntityOwnerModel.delete.where(
            (EntityOwnerModel.user_id.in_(users_list))
            & (EntityOwnerModel.entity_id == entity)  # noqa: W503
        ).gino.status()

    @classmethod
    def get_free_vms_ids_query(cls, pool_id: uuid.UUID, status=Status.ACTIVE):
        """Формирует запрос свободных ВМ.

        Свободная == не занятая за кем-то конкретным.
        """
        occupied_vms_query = EntityOwnerModel.get_occupied_vms()
        query = cls.select("id").where(cls.pool_id == pool_id).where(
            (cls.status == status)  # noqa" W503
            & (cls.id.notin_(occupied_vms_query))  # noqa: W503
        ).order_by(cls.verbose_name)
        return query

    @classmethod
    async def get_free_vms_ids(cls, pool_id: uuid.UUID, status=Status.ACTIVE) -> list:
        """Список id свободных ВМ."""
        query = cls.get_free_vms_ids_query(pool_id=pool_id, status=status)
        ids_qs = await query.gino.all()
        return [str(vm_id) for (vm_id,) in ids_qs]

    @classmethod
    async def get_vms_ids_in_pool(cls, pool_id):
        """Get all vm_ids as list of strings."""
        query = cls.select("id").where(cls.pool_id == pool_id)
        vm_ids_data = await query.gino.all()
        vm_ids = [str(vm_id) for (vm_id,) in vm_ids_data]
        return vm_ids

    @staticmethod
    async def get_all_vms_ids():
        # TODO: какой-то бесполезный метод
        return await get_list_of_values_from_db(Vm, Vm.id)

    async def get_users_query(self):
        """Формирует запрос пользователей ВМ.

        Для случаев когда ожидается больше одного пользователя.
        """
        entity_query = EntityModel.select("id").where(
            (EntityModel.entity_type == EntityType.VM)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )

        query = (
            db.select(UserModel)
            .select_from(UserModel.outerjoin(EntityOwnerModel))
            .where(EntityOwnerModel.entity_id == entity_query)
        )
        return query

    @staticmethod
    async def copy(
        verbose_name: str,
        domain_id: str,
        resource_pool_id: str,
        controller_id,
        create_thin_clones: bool,
        count: int = 1,
    ):
        """Copy existing VM template for new VM create."""
        from common.models.controller import Controller as ControllerModel

        vm_controller = await ControllerModel.get(controller_id)
        # Прерываем выполнение при отсутствии клиента
        if not vm_controller.veil_client:
            raise AssertionError(
                _("There is no client for controller {}.").format(
                    vm_controller.verbose_name
                )
            )
        # Получаем сущность Domain для запросов к VeiL ECP
        vm_client = vm_controller.veil_client.domain(domain_id)
        # Параметры создания ВМ
        if create_thin_clones:
            vm_configuration = DomainConfiguration(
                verbose_name=verbose_name,
                resource_pool=resource_pool_id,
                parent=domain_id,
                count=count,
            )
        else:
            vm_configuration = DomainCloneConfiguration(
                verbose_name=verbose_name,
                resource_pool=resource_pool_id,
                count=count
            )
        # попытка создать ВМ
        inner_retry_count = 0
        while inner_retry_count < VEIL_MAX_VM_CREATE_ATTEMPTS:
            # Send request to create vm
            if create_thin_clones:
                create_response = await vm_client.create(vm_configuration)
            else:
                create_response = await vm_client.clone(vm_configuration)
            # Если задача поставлена - досрочно прерываем попытки
            if create_response.success:
                copy_result = dict(
                    ids=vm_configuration.domains_ids,
                    task_id=create_response.task.api_object_id,
                    verbose_name=verbose_name,
                )
                return copy_result

            # if response status not in (200, 201, 202, 204)
            # TODO: задействовать новые коды ошибок VeiL, когда их доделают

            no_space = compare_error_detail(create_response, "free space")
            if no_space:
                raise VmCreationError(_("Not enough free space on data pool."))

            # Предполагаем, что контроллер заблокирован выполнением задачи.
            # Это может быть и не так, но сейчас нам это не понятно.
            await system_logger.warning(
                _("Possibly blocked by active task on ECP. Wait before next try.")
            )
            await asyncio.sleep(VEIL_OPERATION_WAITING)
            inner_retry_count += 1

        # Попытки создать ВМ не увенчались успехом
        raise VmCreationError("Can`t create VM")

    @staticmethod
    async def remove_vm(vm_id, creator, remove_vms_on_controller):
        # Stop tasks associated with entity
        await send_cmd_to_cancel_tasks_associated_with_entity(vm_id)

        vm = await Vm.get(vm_id)
        await vm.soft_delete(
            creator=creator, remove_on_controller=remove_vms_on_controller
        )

    @staticmethod
    async def remove_vm_with_timeout(vm_id, creator, remove_vms_on_controller):
        try:
            await asyncio.wait_for(
                Vm.remove_vm(vm_id, creator, remove_vms_on_controller),
                VEIL_VM_PREPARE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            vm = await Vm.get(vm_id)
            await system_logger.error(
                message=_("VM {} deleting cancelled by timeout.").format(
                    vm.verbose_name
                )
            )
        except ValueError as err_msg:
            await system_logger.error(message=str(err_msg))

    @classmethod
    async def remove_vms_with_timeout(cls,
                                      controller_client,
                                      vms_ids: list,
                                      creator: str = "system",
                                      remove_from_ecp: bool = False):
        """Групповое удаление ВМ с таймаутом."""
        try:
            await asyncio.wait_for(
                cls.multi_soft_delete(controller_client=controller_client,
                                      vms_ids=vms_ids,
                                      creator=creator,
                                      remove_from_ecp=remove_from_ecp),
                VEIL_VM_REMOVE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            await system_logger.error(
                message=_(
                    "VM multi-deletion task cancelled by timeout. Please see task details on VeiL ECP.")  # noqa: E501
            )
        except ValueError as err_msg:
            await system_logger.error(message=str(err_msg))

    # TODO: отказаться в пользу группового удаления
    @staticmethod
    async def remove_vms(vm_ids, creator="system", remove_vms_on_controller=False):
        """Remove given vms."""
        if not vm_ids:
            return False
        # Ради логирования и вывода из домена удаление делается по 1 ВМ.
        await asyncio.gather(
            *[
                Vm.remove_vm_with_timeout(vm_id, creator, remove_vms_on_controller)
                for vm_id in vm_ids
            ]
        )
        return True

    @classmethod
    async def step_by_step_removing(cls,
                                    controller_client,
                                    vms_ids: list,
                                    creator: str = "system",
                                    remove_from_ecp: bool = False) -> bool:
        """Групповое удаление ВМ блоками."""
        # Нечего удалять
        if not vms_ids:
            return False
        # Разделяем список на блоки
        slice_start = 0
        for i in range(0, len(vms_ids), DOMAIN_CREATION_MAX_STEP):
            slice_end = i + DOMAIN_CREATION_MAX_STEP
            vms_group = vms_ids[slice_start:slice_end]
            # Снимаем действующие блокировки для ВМ
            for vm_id in vms_group:
                await send_cmd_to_cancel_tasks_associated_with_entity(vm_id)
            # Запускаем удаление блока
            await cls.remove_vms_with_timeout(controller_client=controller_client,
                                              vms_ids=vms_group,
                                              creator=creator,
                                              remove_from_ecp=remove_from_ecp)
            slice_start = i + DOMAIN_CREATION_MAX_STEP
        return True

    @staticmethod
    async def event(event_id):
        query = (
            Event.outerjoin(EventReadByUser)
            .outerjoin(UserModel)
            .outerjoin(EntityModel)
            .select()
            .where(Event.id == event_id)
        )

        event = await query.gino.load(
            Event.distinct(Event.id).load(
                add_read_by=UserModel.distinct(UserModel.id), add_entity=EntityModel
            )
        ).first()

        if not event:
            raise SimpleError(_("No such event."))

        return event

    async def events(self, limit, offset):
        entity_query = EntityModel.select("id").where(
            (EntityModel.entity_type == EntityType.VM)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )

        query = (
            Event.outerjoin(EventReadByUser)
            .outerjoin(UserModel)
            .outerjoin(EntityModel)
            .select()
            .where(Event.entity_id.in_(entity_query))
        )

        events = (
            await query.order_by(desc(Event.created))
            .limit(limit)
            .offset(offset)
            .gino.load(
                Event.distinct(Event.id).load(
                    add_read_by=UserModel.distinct(UserModel.id), add_entity=EntityModel
                )
            )
            .all()
        )

        return events

    async def events_count(self):
        entity_query = EntityModel.select("id").where(
            (EntityModel.entity_type == EntityType.VM)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )

        query = (
            Event.outerjoin(EventReadByUser)
            .outerjoin(UserModel)
            .outerjoin(EntityModel)
            .select()
            .where(Event.entity_id.in_(entity_query))
        )

        events_count = (
            await db.select([db.func.count()]).select_from(query.alias()).gino.scalar()
        )
        return events_count

    # Удаленные действия над ВМ - новый код

    async def get_veil_entity(self):
        """Возвращает сущность подключения на VeiL ECP."""
        domain_entity = await self.vm_client
        # Отсутствующий клиент == проблемы с подключением к ECP VeiL
        if not domain_entity:
            raise AssertionError("No active veil client.")
        await domain_entity.info()
        return domain_entity

    async def action(self, action_name: str, force: bool = False):
        """Пересылает команду управления ВМ на ECP VeiL."""
        # TODO: проверить есть ли вообще такое действие в допустимых?
        vm_controller = await self.controller
        # Прерываем выполнение при отсутствии клиента
        if not vm_controller.veil_client:
            raise AssertionError(
                _("There is no client for controller {}.").format(
                    vm_controller.verbose_name
                )
            )
        veil_domain = vm_controller.veil_client.domain(domain_id=self.id_str)
        domain_action = getattr(veil_domain, action_name)
        action_response = await domain_action(force=force)
        # Была установлена задача. Необходимо дождаться ее выполнения.
        if action_response.task:
            await self.task_waiting(action_response.task)
        # Если задача выполнена с ошибкой - прерываем выполнение
        if action_response.task:
            task_success = await action_response.task.is_success()
        else:
            task_success = False
        if not task_success:
            raise ValueError("Remote task finished with error.")
        return task_success

    async def start(self, creator="system"):
        """Включает ВМ - Пересылает start для ВМ на ECP VeiL."""
        domain_entity = await self.get_veil_entity()
        if not domain_entity.powered:
            # При старте ВМ если есть по какой-либо причине tcp usb каналы в режиме connect, то вм не запуститься, если
            # нет соответствующего сервера раздающего usb (а его не будет с большей вероятностью). Так что detach all
            await domain_entity.detach_usb(
                action_type="tcp_usb_device", remove_all=True,
                no_task=True
            )
            task_success = await self.action("start")
            await system_logger.info(
                _("VM {} is powered.").format(self.verbose_name),
                user=creator,
                entity=self.entity,
            )
            return task_success

    async def start_and_reboot(self, creator="system"):
        """Включает и перезапускает ВМ."""
        start_is_success = await self.start(creator=creator)
        if start_is_success:
            await self.reboot
        else:
            await system_logger.warning(_("VM can`t be powered on or already powered."))

    async def shutdown(self, creator="system", force=False):
        """Выключает ВМ - Пересылает shutdown для ВМ на ECP VeiL."""
        domain_entity = await self.get_veil_entity()
        if domain_entity.power_state == VmPowerState.OFF:
            await system_logger.info(
                _("VM {} already shutdown.").format(self.verbose_name),
                user=creator,
                entity=self.entity,
            )
        else:
            task_success = await self.action("shutdown", force=force)

            if force:
                await system_logger.info(
                    _("VM {} is force shutdown.").format(self.verbose_name),
                    user=creator,
                    entity=self.entity,
                )
            else:
                await system_logger.info(
                    _("VM {} is shutdown.").format(self.verbose_name),
                    user=creator,
                    entity=self.entity,
                )
            return task_success

    async def reboot(self, creator="system", force=False):
        """Перезагружает ВМ - Пересылает reboot для ВМ на ECP VeiL."""
        domain_entity = await self.get_veil_entity()
        if domain_entity.power_state == VmPowerState.OFF:
            raise SimpleError(
                _("VM {} is shutdown. Please power this.").format(self.verbose_name),
                user=creator,
                entity=self.entity,
            )
        else:
            # await system_logger.info(_('Rebooting {}').format(self.verbose_name), entity=self.entity)
            task_success = await self.action("reboot", force=force)

            if force:
                await system_logger.info(
                    _("VM {} was force reboot.").format(self.verbose_name),
                    user=creator,
                    entity=self.entity,
                )
            else:
                await system_logger.info(
                    _("VM {} was reboot.").format(self.verbose_name),
                    user=creator,
                    entity=self.entity,
                )
            return task_success

    async def suspend(self, creator="system"):
        """Ставит на паузу ВМ - Пересылает suspend для ВМ на ECP VeiL."""
        domain_entity = await self.get_veil_entity()
        if domain_entity.powered:
            task_success = await self.action("suspend")
            await system_logger.info(
                _("VM {} is suspended.").format(self.verbose_name),
                user=creator,
                entity=self.entity,
            )
            return task_success
        else:
            raise SimpleError(
                _("VM {} is shutdown. Please power this.").format(self.verbose_name),
                user=creator,
                entity=self.entity,
            )

    async def backup(self, creator="system"):
        """Создает бэкап ВМ на Veil."""
        domain_entity = await self.get_veil_entity()
        backup_configuration = DomainBackupConfiguration()
        response = await domain_entity.backup(backup_configuration)
        if not response.success and response.error_code == 50010:
            raise ValueError(
                _("Forbid create backup from a thin clone: {}.").format(
                    self.verbose_name
                )
            )
        elif not response.success:
            raise ValueError(response.error_detail)

        if response.task:
            await self.task_waiting(response.task)
            task_success = await response.task.success
            if not task_success:
                await system_logger.error(_("Creating backup finished with error."))
            else:
                await system_logger.info(
                    _("Backup for VM {} is created.").format(self.verbose_name),
                    user=creator,
                    entity=self.entity,
                )
            return task_success

    async def restore_backup(
        self, file_id, node_id, datapool_id: None, creator="system"
    ):
        """Восстанавливает бэкап ВМ на Veil и помещает в пул."""
        from common.models.pool import AutomatedPool, Pool

        domain_entity = await self.get_veil_entity()
        if datapool_id:
            datapool_id = str(datapool_id)
        response = await domain_entity.automated_restore(
            file_id=str(file_id), node_id=str(node_id), datapool_id=datapool_id
        )
        if not response.success:
            raise ValueError(response.error_detail)

        if response.task:
            await self.task_waiting(response.task)
            task_success = await response.task.success
            response_data = response.data
            restored_vm_id = response_data.get("entity")
            vm_controller = await self.controller
            veil_domain = vm_controller.veil_client.domain(domain_id=restored_vm_id)
            await veil_domain.info()
            # создаем запись в БД для восстановленной ВМ
            pool = await Pool.get(self.pool_id)
            automated_pool = await AutomatedPool.get(self.pool_id)
            if automated_pool:
                vm_count = await pool.get_vm_amount()
                if vm_count == automated_pool.total_size:
                    # увеличиваем общий размер пула, если восстанавливаемая ВМ становится крайней
                    vm_count += 1
                    await automated_pool.soft_update(
                        verbose_name=pool.verbose_name,
                        reserve_size=automated_pool.reserve_size,
                        total_size=vm_count,
                        increase_step=automated_pool.increase_step,
                        vm_name_template=automated_pool.vm_name_template,
                        keep_vms_on=pool.keep_vms_on,
                        create_thin_clones=automated_pool.create_thin_clones,
                        prepare_vms=automated_pool.prepare_vms,
                        ad_cn_pattern=automated_pool.ad_cn_pattern,
                        connection_types=pool.connection_types,
                        creator=creator,
                    )
                    await system_logger.warning(
                        _("Total size of pool {} increased.").format(pool.verbose_name),
                        description=vm_count,
                    )
            restored_vm = await self.create(
                id=restored_vm_id,
                pool_id=str(self.pool_id),
                template_id=str(self.template_id),
                created_by_vdi=True,
                verbose_name=veil_domain.verbose_name,
            )
            await pool.tag_add_entity(tag=pool.tag, entity_id=restored_vm.id, verbose_name=restored_vm.verbose_name)
            await system_logger.info(
                _("VM {} has been added to the pool {}.").format(
                    veil_domain.verbose_name, pool.verbose_name
                ),
                user=creator,
                entity=pool.entity,
            )

            # Переназначение пользователя
            entity = EntityModel.select("id").where(
                (EntityModel.entity_type == self.entity_type)
                & (EntityModel.entity_uuid == self.id)  # noqa: W503
            )
            user = (
                await EntityOwnerModel.select("user_id")
                .where(EntityOwnerModel.entity_id == entity)
                .gino.first()
            )
            if user:
                await EntityOwnerModel.delete.where(
                    EntityOwnerModel.entity_id == entity
                ).gino.status()
                await system_logger.info(
                    _("VM {} is clear from users.").format(self.verbose_name),
                    user=creator,
                    entity=self.entity,
                )
                await self.soft_update(
                    id=self.id, status=Status.SERVICE, creator=creator
                )
                await restored_vm.add_user(user[0], creator=creator)

            if not task_success:
                await system_logger.error(_("Backup restore finished with error."))
            else:
                await system_logger.info(
                    _("Backup from VM {} restored to pool {} as {}.").format(
                        self.verbose_name, pool.verbose_name, restored_vm.verbose_name
                    ),
                    user=creator,
                    entity=self.entity,
                )
            return task_success

    async def enable_remote_access(self):
        """Включает удаленный доступ на VM при необходимости."""
        domain_entity = await self.get_veil_entity()
        if domain_entity.remote_access:
            return True
        # Удаленный доступ выключен, нужно включить и ждать
        action_response = await domain_entity.enable_remote_access()
        # Ожидаем выполнения задачи на VeiL
        if action_response.status_code == 202 and action_response.task:
            # Была установлена задача. Необходимо дождаться ее выполнения.
            await self.task_waiting(action_response.task)
            # Если задача выполнена с ошибкой - прерываем выполнение
            if action_response.task:
                task_success = await action_response.task.is_success()
            else:
                task_success = False
            if not task_success:
                raise ValueError("Remote access enabling task finished with error.")
        await system_logger.info(
            message=_("VM {} remote access enabled.").format(self.verbose_name),
            entity=self.entity,
        )
        return True

    async def qemu_guest_agent_waiting(self):
        """Ожидает активации гостевого агента."""
        domain_entity = await self.get_veil_entity()
        while not domain_entity.qemu_state:
            await asyncio.sleep(VEIL_OPERATION_WAITING)
            await domain_entity.info()
        # Added 16112020
        # Не верим, что все так просто. Ждем еще.
        await asyncio.sleep(VEIL_GUEST_AGENT_EXTRA_WAITING)
        return True

    async def set_verbose_name(self, verbose_name):
        """Обновить имя и хостнейм."""
        # Update on Veil
        vm_controller = await self.controller
        veil_domain = vm_controller.veil_client.domain(domain_id=self.id_str)
        result = await veil_domain.update_verbose_name(verbose_name=verbose_name)
        if not result.success:
            await system_logger.error(
                message=_("Can`t set verbose name."),
                description=str(result.error_detail),
            )
            return

        # Update in db. Имя, которое по факту было назначено
        domain = result.response[0]
        await self.update(verbose_name=domain.verbose_name).apply()

        # Update host_name
        await asyncio.wait_for(self.set_hostname(), VEIL_OPERATION_WAITING * 2)

    async def set_hostname(self):
        """Попытка задать hostname.

        Note:
            Определение hostname гостевым агентом работает нестабильно - игнорируем результат.
        """
        # Прежде чем проверять hostname нужно дождаться активации гостевого агента
        await self.qemu_guest_agent_waiting()
        # Если гостевой агент активировался - задаем имя
        domain_entity = await self.get_veil_entity()
        if str(domain_entity.hostname).upper() != str(self.verbose_name).upper():
            action_response = await domain_entity.set_hostname(
                hostname=self.verbose_name
            )
            # Ожидаем выполнения задачи на VeiL
            if action_response.status_code == 202 and action_response.task:
                await self.task_waiting(action_response.task)
            # Если задача выполнена с ошибкой - логируем
            if action_response.task:
                task_success = await action_response.task.is_success()
            else:
                task_success = False
            if not task_success:
                await system_logger.warning(
                    _("VM {} hostname setting task failed.").format(self.verbose_name),
                    entity=self.entity,
                )
            else:
                msg = _("VM {} hostname setting success.").format(self.verbose_name)
                await system_logger.info(message=msg, entity=self.entity)
        return True

    async def set_hostname_and_reboot(self):
        """Задание hostname и перезагрузка ВМ."""
        hostname_is_success = await self.set_hostname()
        # TODO: когда hostname начнет гарантировано задаваться в этой проверке будет смысл
        if hostname_is_success:
            await self.reboot()

    async def include_in_ad(self,
                            active_directory_obj: AuthenticationDirectory,
                            ad_cn_pattern: str = None):
        """Вводит в домен.

        Т.к. гостевой агент некорректно показывает hostname ВМ, то одновременное назначение и заведение не отработает.
        """
        if not active_directory_obj:
            return False
        # Прежде чем заводить в домен мы должны дождаться активации гостевого агента
        await self.qemu_guest_agent_waiting()
        # Если дождались - можно заводить
        domain_entity = await self.get_veil_entity()
        # APIPA == Automatic Private IP Addressing
        if domain_entity.first_ipv4 and domain_entity.apipa_problem:
            raise ValueError(
                _("VM {} failed to receive DHCP ip address ({}).").format(
                    self.verbose_name, domain_entity.guest_agent.ipv4
                )
            )

        already_in_domain = (
            await domain_entity.is_in_ad() if domain_entity.os_windows else True
        )
        if active_directory_obj and domain_entity.os_windows and not already_in_domain:
            ad_params_dict = {"domain_name": active_directory_obj.domain_name,
                              "login": active_directory_obj.service_username,
                              "password": active_directory_obj.password}
            # Если передан параметр группы AD - добавляем
            if ad_cn_pattern and isinstance(ad_cn_pattern, str):
                ad_params_dict["oupath"] = ad_cn_pattern
            # Вызываем команду на ECP VeiL
            action_response = await domain_entity.add_to_ad(
                **ad_params_dict
            )
            if action_response.task:
                await self.task_waiting(action_response.task)
            # Если задача выполнена с ошибкой - прерываем выполнение
            if action_response.task:
                task_success = await action_response.task.is_success()
            else:
                task_success = False
            if not task_success:
                raise ValueError(
                    _("VM {} domain including task failed.").format(self.verbose_name)
                )
            msg = _("VM {} AD inclusion success.").format(self.verbose_name)
            await system_logger.info(message=msg, entity=self.entity)
            return True
        msg = _("VM {} AD inclusion skipped.").format(self.verbose_name)
        await system_logger.warning(message=msg, entity=self.entity)
        return False

    async def prepare(
        self,
        active_directory_obj: AuthenticationDirectory = None,
        ad_cn_pattern: str = None,
    ):
        """Check that domain remote-access is enabled and domain is powered on.

        Вся процедура должна продолжаться не более 10 минут для 1 ВМ.
        """
        await self.enable_remote_access()
        await self.start_and_reboot()
        await self.set_hostname_and_reboot()

        if active_directory_obj:
            await self.include_in_ad(active_directory_obj,
                                     ad_cn_pattern=ad_cn_pattern)

        # Протоколируем успех
        msg = _("VM {} has been prepared.").format(self.verbose_name)
        await system_logger.info(message=msg, entity=self.entity)
        return True

    async def prepare_with_timeout(
        self,
        active_directory_obj: AuthenticationDirectory = None,
        ad_cn_pattern: str = None,
    ):
        """Подготовка ВМ с ограничением по времени."""
        try:
            await asyncio.wait_for(
                self.prepare(active_directory_obj, ad_cn_pattern),
                VEIL_VM_PREPARE_TIMEOUT,
            )
        except asyncio.TimeoutError as err_msg:
            await system_logger.error(
                message=_("{} preparation cancelled by timeout.").format(
                    self.verbose_name
                ),
                entity=self.entity,
                description=str(err_msg),
            )
            raise
        except ValueError as err_msg:
            err_str = str(err_msg)
            if err_str:
                await system_logger.error(
                    message=_("VM {} preparation error.").format(self.verbose_name),
                    description=err_str,
                    entity=self.entity,
                )
            raise
