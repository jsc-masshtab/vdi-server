# -*- coding: utf-8 -*-
import uuid
from datetime import datetime

from sqlalchemy import Enum as AlchemyEnum

from sqlalchemy.dialects.postgresql import UUID

from auth.utils import crypto
from controller.client import ControllerClient
from database import db, Status, EntityType
from common.veil_errors import SimpleError, BadRequest, ValidationError

from languages import lang_init
from journal.journal import Log as log

_ = lang_init()


# TODO: validate token by expires_on parameter
# TODO: validate status

# TODO: Сейчас при деактивации контроллера задачи создания пула не прекращаются.
#  Нужно сделать, чтобы деактивация контроллера останавливала создание пула и скидывала задачу в очередь.
#  При активации контроллера нужно брать задачи в очереди.


class Controller(db.Model):
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
    def entity_type(self):
        return EntityType.CONTROLLER

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.id}

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
        await log.info(_('Controller {} check passed successful.').format(self.verbose_name))
        return True

    @classmethod
    async def get_credentials(cls, address, username, password, ldap_connection):
        log.debug(
            _('Checking controller credentials: address: {}, username: {}, ldap_connection: {}').format(
                address, username, ldap_connection))
        controller_client = ControllerClient(address)
        auth_info = dict(username=username, password=password, ldap=ldap_connection)
        token, expires_on = await controller_client.auth(auth_info=auth_info)
        version = await controller_client.fetch_version()
        log.debug(_('Get controller credentials: Controller\'s {} credentials are good.').format(address))
        return {'token': token, 'expires_on': expires_on, 'version': version}

    @classmethod
    async def soft_create(cls, verbose_name, address, username, password, ldap_connection, description=None):
        controller_client = ControllerClient(address)
        auth_info = dict(username=username, password=password, ldap=ldap_connection)
        token, expires_on = await controller_client.auth(auth_info=auth_info)
        version = await controller_client.fetch_version()

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

        controller = await Controller.create(**controller_dict)

        msg = _('Successfully added new controller {} with address {}.').format(controller.verbose_name, address)
        await log.info(msg)
        return controller

    async def soft_update(self, verbose_name, address, description, username=None, password=None, ldap_connection=None):
        controller_kwargs = dict()
        credentials_valid = True
        if verbose_name:
            controller_kwargs['verbose_name'] = verbose_name
        if address:
            controller_kwargs['address'] = address
        else:
            address = self.address
        if description:
            controller_kwargs['description'] = description
        if username:
            controller_kwargs['username'] = username
        else:
            username = self.username
        if password:
            controller_kwargs['password'] = crypto.encrypt(password)
        else:
            password = crypto.decrypt(self.password)
        if isinstance(ldap_connection, bool):
            controller_kwargs['ldap_connection'] = ldap_connection
        else:
            ldap_connection = self.ldap_connection

        if (controller_kwargs.get('username') or controller_kwargs.get('password') or controller_kwargs.get(  # noqa
                'address') or controller_kwargs.get('ldap_connection')):  # noqa
            try:
                credentials = await Controller.get_credentials(address, username, password, ldap_connection)
                controller_kwargs.update(credentials)
            except BadRequest:
                credentials_valid = False
                await log.warning(
                    _('Can\'t connect to controller {} with username: {}, ldap_connection: {}').format(
                        address, username, ldap_connection))

        if controller_kwargs:
            try:
                await Controller.update.values(**controller_kwargs).where(
                    Controller.id == self.id).gino.status()
                if not credentials_valid:
                    raise BadRequest(_('Can\'t login login to controller {}').format(address))
            except Exception as E:
                # log.debug(_('Error with controller update: {}').format(E))
                raise SimpleError(E)
            msg = _('Successfully update controller {} with address {}.').format(
                self.verbose_name,
                self.address)
            desc = str(controller_kwargs)
            await log.info(msg, description=desc)
            return True
        return False

    async def soft_delete(self, dest):
        """Удаление сущности независимо от статуса у которой нет зависимых сущностей"""
        controller_has_pools = await self.has_pools
        if controller_has_pools:
            raise SimpleError(_('Controller has pool of virtual machines. Please completely remove.'))

        try:
            await self.delete()
            msg = _('{} {} had remove.').format(dest, self.verbose_name)
            if self.entity:
                await log.info(msg, entity_dict=self.entity)
            else:
                await log.info(msg)
            return True
        except Exception as ex:
            log.debug(_('Soft_delete exception: {}').format(ex))
            return False

    async def full_delete_pools(self):
        """Полное удаление пулов контроллера"""

        pools = await self.pools
        for pool in pools:
            await pool.full_delete(commit=True)

    async def full_delete(self):
        """Удаление сущности с удалением зависимых сущностей"""

        msg = _('Controller {name} had completely remove.').format(name=self.verbose_name)
        await self.full_delete_pools()
        await self.delete()
        await log.info(msg, entity_dict=self.entity)
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
