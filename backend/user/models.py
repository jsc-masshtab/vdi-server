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
    @property
    def entity_type(self):
        return 'Security'

    @staticmethod
    async def get_id(username):
        # TODO: это старый запрос. Есть мнение, что сейчас он уже не нужен. Лучше бы использовать get_object.
        #  например, user = await User.get_object(username = username). user_id = user.id if user else None
        return await User.select('id').where(User.username == username).gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    async def activate(self):
        query = User.update.values(is_active=True).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = 'User {username} has been activated.'.format(username=self.username)
        await Event.create_info(info_message, entity_list=self.entity_list)

        return operation_status

    async def deactivate(self):
        query = User.update.values(is_active=False).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = 'User {username} has been deactivated.'.format(username=self.username)
        await Event.create_info(info_message, entity_list=self.entity_list)

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

    async def set_password(self, raw_password):
        encoded_password = hashers.make_password(raw_password)
        user_status = await User.update.values(password=encoded_password).where(
            User.id == self.id).gino.status()

        info_message = 'Password of user {username} has been changed.'.format(username=self.username)
        await Event.create_info(info_message, entity_list=self.entity_list)

        return user_status

    @staticmethod
    async def soft_create(username, password=None, email=None, last_name=None, first_name=None, is_superuser=False):
        """Если password будет None, то make_password вернет unusable password"""
        encoded_password = hashers.make_password(password)
        user_obj = await User.create(username=username, password=encoded_password, email=email, last_name=last_name,
                                     first_name=first_name, is_superuser=is_superuser)

        user_role = 'Superuser' if is_superuser else 'User'
        info_message = 'Creating user {username} with role {role}.'.format(username=username, role=user_role)
        await Event.create_info(info_message, entity_list=user_obj.entity_list)

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
        if is_superuser or is_superuser is False:
            user_kwargs['is_superuser'] = is_superuser
        if user_kwargs:
            await User.update.values(**user_kwargs).where(
                User.id == user_id).gino.status()
        user = await User.get(user_id)

        if user_kwargs.get('is_superuser'):
            info_message = 'User {username} has become a superuser.'.format(username=user.username)
            await Event.create_info(info_message, entity_list=user.entity_list)

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
        info_message = 'User {username} has been logged in successfully. IP address: {ip}.'.format(username=username,
                                                                                                   ip=ip)
        entity_list = list()
        entity_list.append({'entity_type': user.entity_type, 'entity_uuid': user.uuid})
        entity_list.append({'entity_type': client_type, 'entity_uuid': user.uuid})
        entity_list.append(
            {'entity_type': 'LDAP_AUTH' if ldap else 'LOCAL_AUTH', 'entity_uuid': user.uuid})

        await Event.create_info(info_message, entity_list=entity_list)
        return True

    @classmethod
    async def logout(cls, username, access_token):
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False
        # Проверяем, что нет попытки прервать запрещенный ранее токен
        is_valid = await UserJwtInfo.check_token(username, access_token)
        if not is_valid:
            return False

        # Запрещаем все выданные пользователю токены (Сейчас может быть только 1)
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == user.id).gino.status()

        info_message = 'User {username} has logged out.'.format(username=username)
        await Event.create_info(info_message, entity_list=user.entity_list)
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
