# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from socket import error as socket_error

from asyncpg.exceptions import DataError
from sqlalchemy import Enum as AlchemyEnum

from sqlalchemy.dialects.postgresql import UUID

from auth.utils import crypto
from controller.client import ControllerClient
from database import db, Status, EntityType, AbstractClass
from common.veil_errors import SimpleError, BadRequest, ValidationError

from redis_broker import send_cmd_to_ws_monitor, WsMonitorCmd

from languages import lang_init
from journal.journal import Log as log

_ = lang_init()


# TODO: validate token by expires_on parameter
# TODO: validate status

# TODO: Сейчас при деактивации контроллера задачи создания пула не прекращаются.
#  Нужно сделать, чтобы деактивация контроллера останавливала создание пула и скидывала задачу в очередь.
#  При активации контроллера нужно брать задачи в очереди.


class Controller(AbstractClass):
    # TODO: indexes
    __tablename__ = 'controller'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    address = db.Column(db.Unicode(length=15), nullable=False, unique=True)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))

    username = db.Column(db.Unicode(length=128), nullable=False)
    password = db.Column(db.Unicode(length=128), nullable=False)
    ldap_connection = db.Column(db.Boolean(), nullable=False, default=False)
    token = db.Column(db.Unicode(length=1024))
    expires_on = db.Column(db.DateTime(timezone=True))  # Срок истечения токена.

    @property
    def active(self):
        return self.status == Status.ACTIVE

    @property
    def entity_type(self):
        return EntityType.CONTROLLER

    @property
    def pools_query(self):
        from pool.models import Pool  # Такой импорт из-за импорта в Pool модели Controller.
        pools_query = Controller.join(Pool).select().where(Controller.id == self.id)
        return pools_query

    @property
    async def has_pools(self):
        """Проверяем наличие пулов"""
        pools = await self.pools_query.gino.all()
        return True if pools else False

    @property
    async def pools(self):
        # Либо размещать staticmethod в пулах, либо импорт тут, либо хардкодить названия полей.
        from pool.models import Pool
        query = Pool.join(Controller.query.where(Controller.id == self.id).alias()).alias().select()
        return await query.gino.load(Pool).all()

    @staticmethod
    async def get_addresses(status=Status.ACTIVE):
        """Возвращает ip-контроллеров находящихся в переданном статусе"""

        query = Controller.select('address').where(Controller.status == status)
        addresses = await query.gino.all()
        addresses_list = [address[0] for address in addresses]
        return addresses_list

    @staticmethod
    async def get_controller_id_by_ip(ip_address):
        # controller = await Controller.query.where(Controller.address == ip_address).gino.first()
        return await Controller.select('id').where(Controller.address == ip_address).gino.scalar()

    @staticmethod
    async def get_token(ip_address: str):
        query = Controller.select('token', 'expires_on').where(Controller.address == ip_address)
        token_info = await query.gino.first()
        if token_info:
            token, expires_on = token_info
            if not token or not expires_on:
                token = await Controller.refresh_token(ip_address)
            elif expires_on < datetime.now(expires_on.tzinfo):
                token = await Controller.refresh_token(ip_address)
            return token
        else:
            raise ValidationError(_('No such controller'))

    @staticmethod
    async def invalidate_auth(ip_address: str):
        return await Controller.update.values(
            token=None,
            expires_on=datetime.utcfromtimestamp(0)
        ).where(Controller.address == ip_address).gino.status()

    @staticmethod
    async def refresh_token(ip_address: str):
        # TODO: error handling
        # TODO: set controller status to BAD_AUTH

        query = Controller.select(
            'address',
            'username',
            'password',
            'ldap_connection'
        ).where(Controller.address == ip_address)

        controller = await query.gino.first()
        if controller:
            address, username, encrypted_password, ldap_connection = controller
            password = crypto.decrypt(encrypted_password)
            auth_info = dict(username=username, password=password, ldap=ldap_connection)
            controller_client = ControllerClient(address)
            token, expires_on = await controller_client.auth(auth_info=auth_info)
            await Controller.update.values(
                token=token,
                expires_on=expires_on
            ).where(Controller.address == ip_address).gino.status()
            return token
        else:
            raise ValidationError(_('No such controller'))

    async def check_credentials(self):
        try:
            encrypted_password = crypto.decrypt(self.password)
            log.debug(_(
                'Checking controller credentials: address: {}, username: {}, ldap_connection: {}').format(
                self.address, self.username, self.ldap_connection))
            controller_client = ControllerClient(self.address)
            auth_info = dict(username=self.username, password=encrypted_password, ldap=self.ldap_connection)
            await controller_client.auth(auth_info=auth_info)
        except Exception as ex:
            await log.warning(_('Controller {} check failed.').format(self.verbose_name))
            log.debug(_('Controller check: {}').format(ex))
            return False
        return True

    @classmethod
    async def get_credentials(cls, address, username, password, ldap_connection):
        try:
            controller_client = ControllerClient(address)
            auth_info = dict(username=username, password=password, ldap=ldap_connection)
            token, expires_on = await controller_client.auth(auth_info=auth_info)
            version = await controller_client.fetch_version()
            return {'token': token, 'expires_on': expires_on, 'version': version}
        except BadRequest:
            await log.error(_('Can\'t login to controller {}').format(address))
            return dict()

    @classmethod
    async def soft_create(cls, verbose_name, address, username, password, ldap_connection, description=None, creator='system'):
        controller_client = ControllerClient(address)
        auth_info = dict(username=username, password=password, ldap=ldap_connection)
        token, expires_on = await controller_client.auth(auth_info=auth_info)
        version = await controller_client.fetch_version()
        major_version, minor_version, patch_version = version.split('.')

        # Проверяем версию контроллера в пределах допустимой. Предыдущие версии тоже совместимы, но не стабильны.
        # В версии 4.3 появились изменения в api
        # if major_version != '4' or minor_version != '3':
        #     msg = _('Veil ECP version should be 4.3. Current version is incompatible.')
        #     raise ValidationError(msg)

        controller_dict = {'verbose_name': verbose_name,
                           'address': address,
                           'description': description,
                           'version': version,
                           'status': 'ACTIVE',  # TODO: special class for all statuses
                           'username': username,
                           'password': crypto.encrypt(password),
                           'ldap_connection': ldap_connection,
                           'token': token,
                           'expires_on': expires_on
                           }

        controller = await cls.create(**controller_dict)

        msg = _('Successfully added new controller {} with address {}.').format(controller.verbose_name, address)
        await log.info(msg, user=creator)
        return controller

    async def soft_update(self, verbose_name, address, description, creator, username=None, password=None, ldap_connection=None):

        # Словарь в котором хранятся параметры, которые нужно записать в контроллер
        controller_kwargs = dict()

        # TODO: возможно нужно явно удалять контроллер из монитора ресурсов в каком бы статусе он ни был
        if self.status == Status.ACTIVE:
            # Удаляем существующий контроллер из монитора ресурсов
            log.debug(_('Remove existing controller from resource monitor'))
            send_cmd_to_ws_monitor(self.address, WsMonitorCmd.REMOVE_CONTROLLER)

        # TODO: разнести на несколько методов, если логика останется после рефакторинга
        # Если при редактировании пришли данные авторизации на контроллере проверим их до редактирования
        if username or password or address or ldap_connection:
            # Данные для проверки авторизации и редактирования контроллера
            if address:
                controller_address = address
                controller_kwargs['address'] = controller_address
            else:
                controller_address = self.address

            if username:
                controller_username = username
                controller_kwargs['username'] = controller_username
            else:
                controller_username = self.username

            if password:
                controller_password = password
                controller_kwargs['password'] = crypto.encrypt(password)
            else:
                controller_password = crypto.decrypt(self.password)

            if isinstance(ldap_connection, bool):
                controller_ldap = ldap_connection
                controller_kwargs['ldap_connection'] = controller_ldap
            else:
                controller_ldap = self.ldap_connection

            # Проверяем данные авторизации
            try:
                new_credentials = await Controller.get_credentials(controller_address, controller_username,
                                                                   controller_password, controller_ldap)
            except socket_error:
                # Если произошла ошибка на уровне сети - активируем старые данные и прерываем выполнение
                if self.status == Status.ACTIVE:
                    send_cmd_to_ws_monitor(self.address, WsMonitorCmd.ADD_CONTROLLER)

                msg = _('Address is unreachable')
                raise ValueError(msg)

            # Т.к. на фронте поля редактируются по 1 - нормальная ситуация, что учетные данные не подходят

            if new_credentials:
                # Добавляем данные авторизации в словарь для редактирования
                controller_kwargs.update(new_credentials)
            else:
                # Деактивируем контроллер с неверными учетными данными
                await Controller.deactivate(self.id)

        # Недостающие параметры для редактирования
        if verbose_name:
            controller_kwargs['verbose_name'] = verbose_name
        if description:
            controller_kwargs['description'] = description

        if controller_kwargs:
            try:
                # Если будет ошибка БД транзакция откатится
                async with db.transaction():
                    await Controller.update.values(**controller_kwargs).where(
                        Controller.id == self.id).gino.status()
            except DataError as transaction_error:
                # Если произошла ошибка на уровне сети - активируем старые данные и прерываем выполнение
                if self.status == Status.ACTIVE:
                    send_cmd_to_ws_monitor(self.address, WsMonitorCmd.ADD_CONTROLLER)
                # Отслеживаем только ошибки в БД
                log.debug(transaction_error)
                msg = _('Error with controller update: {}').format(transaction_error)
                raise ValueError(msg)

            updated_rec = await Controller.get(self.id)

            # Переводим контроллер в активный если есть новые учетные данные и он в другом статусе
            if updated_rec.status != Status.ACTIVE and controller_kwargs.get('token'):
                log.debug(_('Activate the controller'))
                await Controller.activate(self.id)

            # Добавляем обратно в монитор ресурсов
            log.debug(_('Add back to the resource monitor'))
            send_cmd_to_ws_monitor(updated_rec.address, WsMonitorCmd.ADD_CONTROLLER)

            msg = _('Successfully update controller {} with address {}.').format(
                self.verbose_name,
                self.address)

            if controller_kwargs.get('password'):
                controller_kwargs['password'] = '*****'
            if controller_kwargs.get('token'):
                controller_kwargs.pop('token')
            if controller_kwargs.get('expires_on'):
                controller_kwargs.pop('expires_on')
            if controller_kwargs.get('version'):
                controller_kwargs.pop('version')
            desc = str(controller_kwargs)

            await log.info(msg, description=desc, user=creator)
            return True

        return False

    async def soft_delete(self, dest, creator):
        """Удаление сущности независимо от статуса у которой нет зависимых сущностей"""
        controller_has_pools = await self.has_pools
        if controller_has_pools:
            raise SimpleError(_('Controller has pool of virtual machines. Please completely remove.'), user=creator)
        return super().soft_delete(dest=dest, creator=creator)

    async def full_delete_pools(self, creator):
        """Полное удаление пулов контроллера"""

        pools = await self.pools
        for pool in pools:
            await pool.full_delete(commit=True, creator=creator)

    async def full_delete(self, creator):
        """Удаление сущности с удалением зависимых сущностей"""

        msg = _('Controller {name} had completely remove.').format(name=self.verbose_name)
        await self.full_delete_pools(creator=creator)
        await self.delete()
        await log.info(msg, entity_dict=self.entity, user=creator)
        return True

    @classmethod
    async def activate(cls, id):
        controller = await Controller.get(id)
        if not controller:
            return False

        if controller.status != Status.ACTIVE:
            await controller.update(status=Status.ACTIVE).apply()
            await log.info(_('Controller {} has been activated.').format(controller.verbose_name))

            # Активируем пулы
            pools = await controller.pools
            for pool in pools:
                await pool.enable(pool.id)

        # TODO: активировать VM?
        return True

    @classmethod
    async def deactivate(cls, id):
        controller = await Controller.get(id)
        if not controller:
            return False

        if controller.status != Status.FAILED:
            await controller.update(status=Status.FAILED).apply()
            await log.info(_('Controller {} has been deactivated.').format(controller.verbose_name))

            # Деактивируем пулы
            pools = await controller.pools
            for pool in pools:
                await pool.disable(pool.id)

        # TODO: деактивировать VM?
        return True
