# -*- coding: utf-8 -*-
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, desc

from auth.utils import hashers
from database import db
from common.veil_errors import SimpleError


# TODO: вынести модели в отдельный пакет auth?
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)  # TODO: try with id
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    email = db.Column(db.Unicode(length=256), unique=True, nullable=False)
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
            # Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order
            query = query.order_by(desc(getattr(User, ordering))) if reversed_order else query.order_by(
                getattr(User, ordering))
        except AttributeError:
            raise SimpleError('Неверный параметр сортировки {}'.format(ordering))
        return query

    @staticmethod
    def get_users_query(ordering=None, include_active=True):
        """Содержит только логику запроса без фетча"""

        query = User.query

        # Исключение удаленных ранее пулов
        if not include_active:
            query = query.where(User.is_active != True)

        # Сортировка
        if ordering:
            query = User.build_ordering(query, ordering)

        return query

    @staticmethod
    async def get_user(user_id=None, username=None):
        query = User.get_users_query()
        if user_id:
            query = query.where(User.id == user_id)
        elif username:
            query = query.where(User.username == username)
        return await query.gino.first()

    @staticmethod
    async def get_active_user(user_id=None, username=None):
        query = User.get_users_query()
        if user_id:
            query = query.where(User.id == user_id)
        elif username:
            query = query.where(User.username == username)
        query = query.where(User.is_active == True)
        return await query.gino.first()

    @staticmethod
    async def get_users(ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        query = User.get_users_query(ordering=ordering)
        return await query.gino.all()

    @staticmethod
    async def get_id(username):
        return await User.select('id').where(User.username == username).gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    @classmethod
    async def activate(cls, user_id):
        return await User.update.values(is_active=True).where(
            User.id == user_id).gino.status()

    @classmethod
    async def deactivate(cls, user_id):
        return await User.update.values(is_active=False).where(
            User.id == user_id).gino.status()

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
        return await User.update.values(password=encoded_password).where(
            User.id == user_id).gino.status()

    @staticmethod
    async def create_user(username, password, email, last_name, first_name, is_superuser=False):
        encoded_password = hashers.make_password(password)
        return await User.create(username=username, password=encoded_password, email=email, last_name=last_name,
                                 first_name=first_name, is_superuser=is_superuser)

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
        return user

    @classmethod
    async def login(cls, username, token):
        """Записывает данные с которыми пользователь вошел в систему"""
        user = await User.get_active_user(username=username)
        if not user:
            return False
        await UserJwtInfo.soft_create(user_id=user.id, token=token)
        return True


class UserJwtInfo(db.Model):
    """
    При авторизации пользователя выполняется запись.
    В поле last_changed хранится дата последнего изменения токена. При изменении пароля/логауте/перегенерации токена
    значение поля меняется, вследствие чего токены, сгенерированные с помощью старых значений
    становятся невалидными.
    """
    __tablename__ = 'user_jwtinfo'
    user_id = db.Column(UUID(), db.ForeignKey(User.id), primary_key=True)
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
        user = await User.get_active_user(username=username)
        if not user:
            return False
        count = await db.select([db.func.count()]).where(
            (UserJwtInfo.user_id == user.id) & (UserJwtInfo.token == token)).gino.scalar()
        return count > 0
