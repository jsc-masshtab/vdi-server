# -*- coding: utf-8 -*-
from common.database import db
from common.languages import _local_
from common.log.journal import system_logger


class Settings(db.Model):
    __tablename__ = "settings"

    settings = db.Column(db.JSON, nullable=True)
    smtp_settings = db.Column(db.JSON, nullable=True)
    gateway_settings = db.Column(db.JSON, nullable=True)

    @classmethod
    async def get_settings(cls, param=None, default=None):
        query = cls.select("settings")
        settings = await query.gino.first()
        if not settings:
            return default

        if param:
            return settings[0].get(param, default)
        else:
            return settings[0]

    @classmethod
    async def change_settings(
        cls,
        creator="system",
        **kwargs
    ):
        try:
            settings = await cls.get_settings()
            if settings is None:
                settings = {}

            if kwargs:
                for key, value in kwargs.items():
                    settings[key] = value
            await cls.update.values(settings=settings).gino.status()
            entity = {"entity_type": "SECURITY", "entity_uuid": None}
            await system_logger.info(_local_("Settings changed."), description=kwargs,
                                     entity=entity, user=creator)
            return True
        except Exception:
            return False

    @classmethod
    async def get_smtp_settings(cls, param=None):
        query = cls.select("smtp_settings")
        settings = await query.gino.first()
        if param:
            return settings[0][param]
        else:
            return settings[0]

    @classmethod
    async def change_smtp_settings(
        cls,
        creator="system",
        **kwargs
    ):
        try:
            smtp_settings = await cls.get_smtp_settings()
            if kwargs:
                for key, value in kwargs.items():
                    smtp_settings[key] = value
            await cls.update.values(smtp_settings=smtp_settings).gino.status()
            entity = {"entity_type": "SECURITY", "entity_uuid": None}
            await system_logger.info(_local_("Smtp settings are changed."), description=kwargs,
                                     entity=entity, user=creator)
            return True
        except Exception as e:
            await system_logger.debug(str(e))
            return False

    @classmethod
    async def get_gateway_settings(cls, param=None):
        query = cls.select("gateway_settings")
        settings = await query.gino.first()
        if param:
            return settings[0][param]
        else:
            return settings[0]

    @classmethod
    async def change_gateway_settings(
        cls,
        creator="system",
        **kwargs
    ):
        try:
            gateway_settings = await cls.get_gateway_settings()
            if kwargs:
                for key, value in kwargs.items():
                    gateway_settings[key] = value
            await cls.update.values(gateway_settings=gateway_settings).gino.status()
            entity = {"entity_type": "SECURITY", "entity_uuid": None}
            msg = _local_("Gateway settings in VDI-Server database are changed.")
            await system_logger.info(msg, description=kwargs,
                                     entity=entity, user=creator)
            return True
        except Exception as e:
            await system_logger.debug(str(e))
            return False
