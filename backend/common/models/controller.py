# -*- coding: utf-8 -*-
import uuid
from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from veil_api_client import VeilClient

from common.database import db
from common.veil.veil_api import get_veil_client
from common.veil.veil_redis import send_cmd_to_ws_monitor, WsMonitorCmd
from common.veil.veil_gino import Status, EntityType, VeilModel, AbstractSortableStatusModel
from common.veil.veil_errors import ValidationError

from common.languages import lang_init
from common.log.journal import system_logger

from common.models.pool import Pool as PoolModel

# TODO: переименовать _ в _localization_
_ = lang_init()


# TODO: Сейчас при деактивации контроллера задачи создания пула не прекращаются - уточнить у Соломина,
#  возможно уже готово.
#  Нужно сделать, чтобы деактивация контроллера останавливала создание пула и скидывала задачу в очередь.
#  При активации контроллера нужно брать задачи в очереди.

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
    __tablename__ = 'controller'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    address = db.Column(db.Unicode(length=15), nullable=False, unique=True, index=True)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))
    token = db.Column(db.Unicode(length=1024), nullable=False)

    @property
    def id_str(self):
        """Convert UUID(id) to str."""
        return str(self.id)

    @property
    def veil_client(self) -> 'VeilClient':
        """Возвращает инстанс сущности Контроллер у veil api client.

        На данный отсутствует вменяемый способ выяснить id контроллера на VeiL и нет
        ни 1 причины по которой он может потребоваться для VDI.
        """
        veil_client = get_veil_client()
        return veil_client.add_client(server_address=self.address, token=self.token)

    @property
    def controller_client(self):
        """Возвращает инстанс сущности Контроллер у veil api client.

        На данный отсутствует вменяемый способ выяснить id контроллера на VeiL и нет
        ни 1 причины по которой он может потребоваться для VDI.
        """
        return self.veil_client.controller()

    async def remove_client(self):
        """Удаляет клиент из синглтона."""
        veil_api_singleton = get_veil_client()
        return await veil_api_singleton.remove_client(self.address)

    @property
    def active(self):
        return self.status == Status.ACTIVE

    @property
    def failed(self):
        return self.status == Status.FAILED

    @property
    def entity_type(self):
        return EntityType.CONTROLLER

    @property
    async def pools(self):
        """Зависимые объекты модели Pool."""
        query = PoolModel.query.where(PoolModel.controller == self.id)
        return await query.gino.all()

    @property
    async def ok(self):
        """Проверяем доступность контроллера и его статус."""
        client = self.controller_client
        return await client.ok

    async def check_task_status(self, task_id: str):
        """Проверяем выполнилась ли задача на ECP VeiL."""
        client = self.veil_client
        task_client = client.task(task_id)
        return await task_client.completed()

    async def check_controller(self):
        """Проверяем доступность контроллера и меняем его статус."""
        send_cmd_to_ws_monitor(self.id, WsMonitorCmd.REMOVE_CONTROLLER)
        connection_is_ok = await self.ok
        if connection_is_ok:
            await self.activate()
            send_cmd_to_ws_monitor(self.id, WsMonitorCmd.ADD_CONTROLLER)
            return True
        await self.deactivate()
        return False

    @staticmethod
    async def get_addresses(status=Status.ACTIVE):
        """Возвращает ip-контроллеров находящихся в переданном статусе"""
        # TODO: выпилить?
        query = Controller.select('address').where(Controller.status == status)
        addresses = await query.gino.all()
        return [address[0] for address in addresses]

    @staticmethod
    async def get_controller_id_by_ip(ip_address):
        # TODO: remove
        return await Controller.select('id').where(Controller.address == ip_address).gino.scalar()

    async def get_version(self):
        """Проверяем допустимость версии контроллера."""
        # Получаем инстанс клиента
        controller_client = self.controller_client
        # Получаем версию контроллера
        await controller_client.base_version()
        version = controller_client.version
        if not version:
            msg = _('Veil ECP version could not be obtained. Check your token.')
            await self.remove_client()
            raise ValidationError(msg)
        major_version, minor_version, patch_version = version.split('.')
        await self.update(version=version).apply()
        # Проверяем версию контроллера в пределах допустимой.
        if major_version != '4' or minor_version != '3':
            msg = _('Veil ECP version should be 4.3. Current version is incompatible.')
            await self.remove_client()
            raise ValidationError(msg)

    @classmethod
    async def soft_create(cls, verbose_name, address, token: str, description=None, creator='system'):
        """Создание сущности Controller."""
        async with db.transaction():
            # Создаем запись
            controller = await cls.create(verbose_name=verbose_name,
                                          address=address,
                                          description=description,
                                          status=Status.CREATING,
                                          token=token)
            # Получаем, сохраняем и проверяем допустимость версии
            await controller.get_version()
            # Проверяем состояние контроллера, меняем статус, добавляем в монитор
            controller_is_ok = await controller.check_controller()
            # Логгируем результат операции
            msg = _('Adding controller {}: {}.').format(verbose_name, controller_is_ok)
            await system_logger.info(msg, user=creator, entity=controller.entity)
            # Возвращаем инстанс созданного контроллера
            return controller

    async def soft_update(self, creator, verbose_name=None, address=None, description=None, token=None):
        """Редактирование сущности Controller.

        1. Собираются параметры для редактирования
        2. Редактируются параметры контроллера
        3. Проверяется доступность
        Удаление и добавление в монитор ресурсов происходит в check_controller.
        """
        # Параметры, которые нужно записать в контроллер
        controller_kwargs = dict()
        if verbose_name:
            controller_kwargs['verbose_name'] = verbose_name
        if address:
            controller_kwargs['address'] = address
        if description:
            controller_kwargs['description'] = description
        if token:
            controller_kwargs['token'] = token
        # Если параметров нет - прерываем редактирование
        if not controller_kwargs:
            return False
        # Редактируем параметры записи в БД
        async with db.transaction():
            await Controller.update.values(**controller_kwargs).where(
                Controller.id == self.id).gino.status()
            updated_controller = await Controller.get(self.id)
            # Получаем, сохраняем и проверяем допустимость версии
            await updated_controller.get_version()
        controller_is_ok = await updated_controller.check_controller()
        # Мы не хотим видеть токен в логе
        if controller_kwargs.get('token'):
            controller_kwargs.pop('token')
        # Протоколируем результат операции
        msg = _('Update controller {}: {}.').format(
            updated_controller.verbose_name,
            controller_is_ok)
        await system_logger.info(msg, description=str(controller_kwargs), user=creator, entity=self.entity)
        return updated_controller

    async def full_delete_pools(self, creator):
        """Полное удаление пулов контроллера"""
        pools = await self.pools

        # async_tasks = []
        #
        # for pool in pools:
        #     # Удаляем пулы в зависимости от типа
        #     pool_type = await pool.pool_type
        #     # Авто пул
        #     if pool_type == Pool.PoolTypes.AUTOMATED:
        #         async_tasks.append(AutomatedPool.delete_pool(pool, True, True, 15))
        #     else:
        #         async_tasks.append(Pool.delete_pool(pool, creator, True))
        # # Паралельно удаляем пулы
        # await tornado.gen.multi(async_tasks)

        for pool_obj in pools:
            await pool_obj.full_delete(commit=True, creator=creator)

    async def full_delete(self, creator):
        """Удаление сущности с удалением зависимых сущностей."""
        # soft_delete явно не вызывается
        # Удаляем контроллер из монитора
        send_cmd_to_ws_monitor(self.id, WsMonitorCmd.REMOVE_CONTROLLER)
        # Переключаем статус
        await self.update(status=Status.DELETING).apply()
        # Удаляем зависимые пулы
        await self.full_delete_pools(creator=creator)
        # Удаляем запись
        status = await super().soft_delete(creator=creator)
        return status

    async def activate(self):
        """Активируем не активный контроллер и его пулы."""
        if not self.active:
            # Активируем контроллер
            await self.update(status=Status.ACTIVE).apply()
            await system_logger.info(_('Controller {} has been activated.').format(self.verbose_name), entity=self.entity)
            # Активируем пулы
            # TODO: переработать активацию пулов - нужен метод в пулах, который бы активировал ВМ.
            pools = await self.pools
            for pool_obj in pools:
                await pool_obj.enable(pool_obj.id)
            # Активация ВМ происходит внутри пулов.
            return True
        return False

    async def deactivate(self):
        """Деактивируем контроллер и его пулы."""
        if not self.failed:
            # Деактивируем контроллер
            await self.update(status=Status.FAILED).apply()
            await system_logger.info(_('Controller {} has been deactivated.').format(self.verbose_name), entity=self.entity)
            # Деактивируем пулы
            # TODO: переработать деактивацию пулов - нужен метод в пулах, который бы деактивировал ВМ.
            pools = await self.pools
            for pool_obj in pools:
                await pool_obj.disable(pool_obj.id)
                # Деактивация ВМ происходит внутри пулов.
            return True
        return False
