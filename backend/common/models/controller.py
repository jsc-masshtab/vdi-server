# -*- coding: utf-8 -*-
import uuid

import jwt

from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID

from veil_api_client import VeilClient, VeilRetryConfiguration

from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.models.pool import Pool as PoolModel
from common.subscription_sources import CONTROLLERS_SUBSCRIPTION
from common.veil.auth.fernet_crypto import decrypt, encrypt
from common.veil.veil_api import get_veil_client
from common.veil.veil_errors import SimpleError, ValidationError
from common.veil.veil_gino import (
    AbstractSortableStatusModel,
    EntityType,
    Status,
    VeilModel,
)
from common.veil.veil_redis import (
    WsMonitorCmd, publish_data_in_internal_channel,
    send_cmd_to_cancel_tasks_associated_with_controller,
    send_cmd_to_resume_tasks_associated_with_controller,
    send_cmd_to_ws_monitor
)


class Controller(AbstractSortableStatusModel, VeilModel):
    """Сущность VeiL контроллера на ECP VeiL.

    Уникальные поля:
        id: автогенерируемый UUID записи.
        verbose_name: текстовое наименование контроллера.
        address: url-адрес контроллера (без протокола).

    Возможные статусы:
        Status.ACTIVE
        Status.FAILED
        Status.CREATING
        Status.DELETING
    """

    __tablename__ = "controller"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    address = db.Column(db.Unicode(length=15), nullable=False, unique=True, index=True)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))
    token = db.Column(db.Unicode(length=1024), nullable=False)

    @property
    async def check_jwt_token(self):
        if self.token[0:4] == "jwt ":
            token = encrypt(self.token)
            await self.update(token=token).apply()
            return self.token
        else:
            return self.token

    @property
    def veil_client(self) -> "VeilClient":
        """Клиент не сломанного контроллера."""
        if self.stopped:
            return
        veil_client = get_veil_client()
        token = decrypt(self.token)
        return veil_client.add_client(server_address=self.address, token=token)

    @property
    def controller_client(self):
        """Возвращает инстанс сущности Контроллер у veil api client.

        На данный отсутствует вменяемый способ выяснить id контроллера на VeiL и нет
        ни 1 причины по которой он может потребоваться для VDI.
        """
        if self.veil_client:
            return self.veil_client.controller()

    async def remove_client(self):
        """Удаляет клиент из синглтона."""
        veil_api_singleton = get_veil_client()
        await veil_api_singleton.remove_client(self.address)

    @property
    def entity_type(self):
        return EntityType.CONTROLLER

    @property
    async def pools(self):
        """Зависимые объекты модели Pool."""
        query = PoolModel.query.where(PoolModel.controller == self.id)
        return await query.gino.all()

    @property
    async def get_veil_user(self):
        """Возвращает имя пользователя на ECP VeiL относительно используемого токена."""
        token = decrypt(self.token)
        data = jwt.decode(token[4:], verify=False)
        return data["username"]

    async def is_ok(self):
        """Проверяем доступность контроллера независимо от его статуса."""
        try:
            await self.remove_client()
            veil_client = get_veil_client()
            token = decrypt(self.token)
            client = veil_client.add_client(
                server_address=self.address, token=token
            )
            is_ok = await client.controller(
                self.id, retry_opts=VeilRetryConfiguration(num_of_attempts=0)
            ).is_ok()
        except Exception:
            await self.remove_client()
            is_ok = False
        return is_ok

    async def check_controller(self):
        """Проверяем доступность контроллера и меняем его статус."""
        connection_is_ok = await self.is_ok()
        if connection_is_ok and self.status != Status.SERVICE:
            await self.activate()
        elif not self.stopped:
            await self.activate()
        else:
            await self.deactivate()
        return connection_is_ok

    async def get_version(self):
        """Проверяем допустимость версии контроллера."""
        # Получаем инстанс клиента
        controller_client = self.controller_client
        if not controller_client:
            raise ValidationError(
                _local_("Controller {} has no api client.").format(self.verbose_name)
            )
        # Получаем версию контроллера
        await controller_client.base_version()
        version = controller_client.version
        if not version:
            msg = _local_("ECP VeiL version could not be obtained. Check your token.")
            await self.remove_client()
            raise SimpleError(msg)
        major_version, minor_version, patch_version = version.split(".")
        await self.update(version=version).apply()
        # Проверяем версию контроллера в пределах допустимой.
        if major_version != "4" or int(minor_version) < 3:
            msg = _local_(
                "ECP VeiL version should be 4.3 or higher. Current version is incompatible."
            )
            await self.remove_client()
            raise ValidationError(msg)

    @classmethod
    async def soft_create(
        cls, verbose_name, address, token: str, description=None, creator="system"
    ):
        """Создание сущности Controller."""
        async with db.transaction():
            # Создаем запись
            controller = await cls.create(
                verbose_name=verbose_name,
                address=address,
                description=description,
                status=Status.CREATING,
                token=encrypt(token),
            )
            # Получаем, сохраняем и проверяем допустимость версии
            await controller.get_version()

            connection_is_ok = await controller.is_ok()
            if connection_is_ok:
                await controller.activate()

        # Отправляем команду на добавляление контроллера в монитор (После завершения транзакции
        # чтоб запись точно была в бд)
        if connection_is_ok:
            await send_cmd_to_ws_monitor(controller.id, WsMonitorCmd.ADD_CONTROLLER)

        # Логгируем результат операции
        msg = _local_("Controller {} added.").format(verbose_name)
        await system_logger.info(msg, user=creator, entity=controller.entity)

        # Ws сообщение о создание
        await publish_data_in_internal_channel(controller.get_resource_type(),
                                               "CREATED", controller)

        # Возвращаем инстанс созданного контроллера
        return controller

    async def soft_update(
        self, creator, verbose_name=None, address=None, description=None, token=None
    ):
        """Редактирование сущности Controller.

        1. Собираются параметры для редактирования
        2. Редактируются параметры контроллера
        3. Проверяется доступность
        """
        # Параметры, которые нужно записать в контроллер
        controller_kwargs = dict()
        if verbose_name:
            controller_kwargs["verbose_name"] = verbose_name
        if address:
            controller_kwargs["address"] = address
        if description:
            controller_kwargs["description"] = description
        if token:
            controller_kwargs["token"] = encrypt(token)
        # Если параметров нет - прерываем редактирование
        if not controller_kwargs:
            return False
        # Если передан токен - деактивируем подключение
        if token or address:
            await self.deactivate()
        # Редактируем параметры записи в БД
        async with db.transaction():
            await Controller.update.values(**controller_kwargs).where(
                Controller.id == self.id
            ).gino.status()
            updated_controller = await Controller.get(self.id)
        controller_is_ok = await updated_controller.check_controller()
        # На случай смены токена или адреса
        await send_cmd_to_ws_monitor(self.id, WsMonitorCmd.RESTART_MONITOR)
        if controller_is_ok:
            await updated_controller.activate()
            # Получаем, сохраняем и проверяем допустимость версии
            await updated_controller.get_version()
        # Мы не хотим видеть токен в логе
        if controller_kwargs.get("token"):
            controller_kwargs["token"] = "*" * 12
        # Протоколируем результат операции
        if controller_is_ok:
            await publish_data_in_internal_channel(self.get_resource_type(), "UPDATED",
                                                   self)

            msg = _local_("Controller {} has been successfully updated.").format(
                self.verbose_name
            )
        else:
            msg = _local_("Controller {} update failed.").format(self.verbose_name)
        await system_logger.info(
            msg, description=str(controller_kwargs), user=creator, entity=self.entity
        )
        return updated_controller

    async def full_delete_pools(self, creator):
        """Полное удаление пулов контроллера."""
        pools = await self.pools
        for pool_obj in pools:
            await pool_obj.full_delete(creator=creator)

    async def full_delete(self, creator):
        """Удаление сущности с удалением зависимых сущностей."""
        # Останавлием задачи связанные с контроллером
        await send_cmd_to_cancel_tasks_associated_with_controller(
            controller_id=self.id, wait_for_result=True
        )
        # Удаляем контроллер из монитора
        await send_cmd_to_ws_monitor(self.id, WsMonitorCmd.REMOVE_CONTROLLER)
        # Переключаем статус
        await self.set_status(Status.DELETING)
        # Удаляем зависимые пулы
        await self.full_delete_pools(creator=creator)
        # Удаляем клиент по контроллеру
        await self.remove_client()
        # Удаляем запись
        status = await super().soft_delete(creator=creator)
        await system_logger.info(
            message=_local_("Controller {} has been removed.").format(
                self.verbose_name),
            user=creator,
            entity=self.entity,
        )
        # Оповещаем об удалении контоллера
        await publish_data_in_internal_channel(self.get_resource_type(), "DELETED",
                                               self)

        return status

    async def enable(self, creator="system"):
        connection_is_ok = await self.is_ok()
        if connection_is_ok:
            return await self.activate(creator=creator)
        return False

    async def activate(self, creator="system"):
        """Активируем не активный контроллер и его пулы."""
        if self.active:
            return False
        # Активируем контроллер
        await self.set_status(Status.ACTIVE)
        # Активируем пулы
        pools = await self.pools
        for pool_obj in pools:
            await pool_obj.enable(pool_obj.id)
        # Активация ВМ происходит внутри пулов.

        # Возобновляем задачи связанные с контроллером
        await send_cmd_to_resume_tasks_associated_with_controller(self.id)
        await system_logger.info(
            _local_("Controller {} has been activated.").format(self.verbose_name),
            entity=self.entity,
            user=creator,
        )
        return True

    async def deactivate(self, status=Status.FAILED):
        """Деактивируем активный контроллер и его пулы."""
        if self.stopped and status != Status.BAD_AUTH:
            return False
        # Деактивируем контроллер
        await self.set_status(status)
        # Останавливаем задачи связанные с контроллером
        await send_cmd_to_cancel_tasks_associated_with_controller(
            controller_id=self.id, wait_for_result=True
        )
        # отключаем клиент
        await self.remove_client()
        # Деактивируем пулы
        pools = await self.pools
        for pool_obj in pools:
            await pool_obj.deactivate(pool_obj.id)
        await system_logger.warning(
            _local_("Controller {} status has been switched to {}.").format(
                self.verbose_name, status.name
            ),
            entity=self.entity,
        )
        return True

    async def service(self, status=Status.SERVICE, creator="system"):
        """Переводим контроллер и его пулы в статус SERVICE."""
        # Переводим контроллер в статус сервис
        await self.set_status(status)
        # Останавлием задачи связанные с контроллером
        await send_cmd_to_cancel_tasks_associated_with_controller(
            controller_id=self.id, wait_for_result=True
        )
        # отключаем клиент
        await self.remove_client()
        # Переводим пулы в статус сервис
        pools = await self.pools
        for pool_obj in pools:
            await pool_obj.set_status(Status.SERVICE)
            # Перевод ВМ в статус сервис. Добавлено 08.02.2021 - не факт, что нужно.
            vms = await pool_obj.get_vms()
            for vm in vms:
                if vm.status != Status.RESERVED:
                    await vm.update(status=Status.SERVICE).apply()
        await system_logger.info(
            _local_("Controller {} status has been switched to {}.").format(
                self.verbose_name, status.name
            ),
            entity=self.entity,
            user=creator,
        )
        return True

    def get_resource_type(self):
        return CONTROLLERS_SUBSCRIPTION
