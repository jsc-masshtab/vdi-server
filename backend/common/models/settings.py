# -*- coding: utf-8 -*-
from common.database import db
from common.languages import _
from common.log.journal import system_logger


class Settings(db.Model):
    __tablename__ = "settings"

    settings = db.Column(db.JSON, nullable=True)

    @classmethod
    async def get_settings(cls, param=None):
        query = cls.select("settings")
        settings = await query.gino.first()
        if param:
            return settings[0][param]
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
            if kwargs:
                for key, value in kwargs.items():
                    settings[key] = value
            await cls.update.values(settings=settings).gino.status()
            entity = {"entity_type": "SECURITY", "entity_uuid": None}
            await system_logger.info(_("Settings changed."), description=kwargs,
                                     entity=entity, user=creator)
            return True
        except Exception:
            return False
