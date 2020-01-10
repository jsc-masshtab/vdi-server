# -*- coding: utf-8 -*-
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from auth.utils import hashers
from database import db, AbstractSortableStatusModel, AbstractEntity
from event.models import Event


class User(AbstractSortableStatusModel, db.Model, AbstractEntity):
    __tablename__ = 'user'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    email = db.Column(db.Unicode(length=256), unique=True, nullable=True)
    last_name = db.Column(db.Unicode(length=128))
    first_name = db.Column(db.Unicode(length=32))
    date_joined = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    last_login = db.Column(db.DateTime(timezone=True), server_default=func.now())
    is_superuser = db.Column(db.Boolean(), default=False)
    is_active = db.Column(db.Boolean(), default=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @staticmethod
    async def get_id(username):
        # TODO: это старый запрос. Есть мнение, что сейчас он уже не нужен. Лучше бы использовать get_object.
        #  например, user = await User.get_object(username = username). user_id = user.id if user else None
        return await User.select('id').where(User.username == username).gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    @classmethod
    async def activate(cls, id):
        query = cls.update.values(is_active=True).where(cls.id == id)
        operation_status = await query.gino.status()
        await Event.create_info('Auth: user {} has been activated.'.format(id))
        return operation_status

    @classmethod
    async def deactivate(cls, id):
        query = cls.update.values(is_active=False).where(cls.id == id)
        operation_status = await query.gino.status()
        await Event.create_info('Auth: user {} has been deactivated.'.format(id))
        return operation_status

    @staticmethod
    async def check_password(username, raw_password):
        password = await User.select('password').where(User.username == username).gino.scalar()
        return await hashers.check_password(raw_password, password)

    @staticmethod
    async def check_user(username, raw_password):
        count = await db.select([db.func.count()]).where(
            (User.username == username) & (User.is_active == True)).gino.scalar()
        if count == 0:
            return False
        return await User.check_password(username, raw_password)

    @staticmethod
    async def set_password(user_id, raw_password):
        encoded_password = hashers.make_password(raw_password)
        user_status = await User.update.values(password=encoded_password).where(
            User.id == user_id).gino.status()
        await Event.create_info('Auth: user {} changed local password.'.format(user_id))
        return user_status

    @staticmethod
    async def soft_create(username, password=None, email=None, last_name=None, first_name=None, is_superuser=False):
        """Если password будет None, то make_password вернет unusable password"""
        encoded_password = hashers.make_password(password)
        user_obj = await User.create(username=username, password=encoded_password, email=email, last_name=last_name,
                                     first_name=first_name, is_superuser=is_superuser)
        user_message = 'Superuser' if is_superuser else 'User'
        await Event.create_info('Auth: {} {} created.'.format(user_message, username))
        return user_obj

    @classmethod
    async def soft_update(cls, user_id, username, email, last_name, first_name, is_superuser):
        user_kwargs = dict()
        if username:
            user_kwargs['username'] = username
        if email:
            user_kwargs['email'] = email
        if last_name:
            user_kwargs['last_name'] = last_name
        if first_name:
            user_kwargs['first_name'] = first_name
        if is_superuser or is_superuser == False:
            user_kwargs['is_superuser'] = is_superuser
        if user_kwargs:
            await User.update.values(**user_kwargs).where(
                User.id == user_id).gino.status()
        user = await User.get(user_id)
        if user_kwargs.get('is_superuser'):
            await Event.create_info('Auth: {} has become a superuser.'.format(user.username))
        return user

    @classmethod
    async def login(cls, username, token, client_type, ip=None, ldap=False):
        """Записывает данные с которыми пользователь вошел в систему"""
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False
        await user.update(last_login=func.now()).apply()
        await UserJwtInfo.soft_create(user_id=user.id, token=token)

        # Login event
        login_message = 'User login (ldap)' if ldap else 'User login (local)'
        info_message = 'Auth by {}: {}: IP: {}. username: {}'.format(client_type, login_message, ip,
                                                                    username)
        await Event.create_info(info_message)
        return True

    @classmethod
    async def logout(cls, username, client_type, ip):
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == user.id).gino.status()
        info_message = 'Auth by {}: User {} logged out: IP: {}.'.format(client_type, username, ip)
        await Event.create_info(info_message)
        return True


class UserJwtInfo(db.Model):
    """
    При авторизации пользователя выполняется запись.
    В поле last_changed хранится дата последнего изменения токена. При изменении пароля/логауте/перегенерации токена
    значение поля меняется, вследствие чего токены, сгенерированные с помощью старых значений
    становятся невалидными.
    """
    __tablename__ = 'user_jwtinfo'
    user_id = db.Column(UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), primary_key=True)
    # не хранит в себе 'jwt ' максимальный размер намеренно не установлен, т.к. четкого ограничение в стандарте нет.
    token = db.Column(db.Unicode(), nullable=False, index=True)
    last_changed = db.Column(db.DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def soft_create(cls, user_id, token):
        # Не нашел в GINO create_or_update.

        count = await db.select([db.func.count()]).where(
            UserJwtInfo.user_id == user_id).gino.scalar()
        if count == 0:
            # Если записи для пользователя нет - создаем новую.
            await UserJwtInfo.create(user_id=user_id, token=token)
            return True
        # Если запись уже существует - обновлям значение токена.
        await UserJwtInfo.update.values(token=token, last_changed=func.now()).where(
            UserJwtInfo.user_id == user_id).gino.status()
        return True

    @classmethod
    async def check_token(cls, username, token):
        """Проверяет соответствие выданного токена тому, что пришел в payload."""
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False
        count = await db.select([db.func.count()]).where(
            (UserJwtInfo.user_id == user.id) & (UserJwtInfo.token == token)).gino.scalar()
        return count > 0
