# -*- coding: utf-8 -*-
from database import db

from auth.utils import hashers
# TODO: сделать схему человеческой


class User(db.Model):
    # TODO: missing columns
    # TODO: indexes
    # TODO: validators
    __tablename__ = 'user'
    username = db.Column(db.Unicode(length=128), nullable=False, primary_key=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    email = db.Column(db.Unicode(length=128))

    @staticmethod
    async def check_password(username, raw_password):
        password = await User.select('password').where(User.username == username).gino.scalar()
        return await hashers.check_password(raw_password, password)

    @staticmethod
    async def check_user(username, raw_password):
        count = await db.select([db.func.count()]).where(User.username == username).gino.scalar()
        if count == 0:
            return False
        return await User.check_password(username, raw_password)

    @staticmethod
    async def set_password(username, raw_password):
        encoded_password = hashers.make_password(raw_password)
        return await User.update.values(password=encoded_password).where(
            User.username == username).gino.status()

    @staticmethod
    async def create_user(username, raw_password, email):
        encoded_password = hashers.make_password(raw_password)
        return await User.create(username=username, password=encoded_password, email=email)


# class UserJwtInfo(db.Model):
#     """
#     В поле last_changed хранится дата последнего изменения токена. При изменении пароля/логауте/перегенерации токена
#     значение поля меняется, вследствие чего токены, сгенерированные с помощью старых значений
#     становятся невалидными.
#     """
#     __tablename__ = 'user_jwtinfo'
#
#     username = db.Column(db.Unicode(length=128), db.ForeignKey('user.username'), primary_key=True)
#     last_changed = db.Column(db.DateTime(), nullable=False)
