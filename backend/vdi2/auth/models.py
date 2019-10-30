# -*- coding: utf-8 -*-
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from auth.utils import hashers
from database import db


class User(db.Model):
    # TODO: indexes
    # TODO: validators
    __tablename__ = 'user'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    email = db.Column(db.Unicode(length=256), unique=True)
    first_name = db.Column(db.Unicode(length=32))
    last_name = db.Column(db.Unicode(length=128))
    date_joined = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    last_login = db.Column(db.DateTime(timezone=True), server_default=func.now())
    is_superuser = db.Column(db.Boolean())
    is_active = db.Column(db.Boolean())

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
