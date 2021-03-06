# -*- coding: utf-8 -*-
import uuid
from enum import Enum

from sqlalchemy import Enum as AlchemyEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from common.database import db
from common.veil.veil_gino import AbstractSortableStatusModel


class TkPermission(Enum):
    """Права пользователя ТК."""

    USB_REDIR = "USB_REDIR"
    FOLDERS_REDIR = "FOLDERS_REDIR"
    SHARED_CLIPBOARD_CLIENT_TO_GUEST = "SHARED_CLIPBOARD_CLIENT_TO_GUEST"
    SHARED_CLIPBOARD_GUEST_TO_CLIENT = "SHARED_CLIPBOARD_GUEST_TO_CLIENT"


class UserTkPermission(db.Model, AbstractSortableStatusModel):

    __tablename__ = "user_tk_permission"
    __table_args__ = (
        UniqueConstraint(
            "permission", "user_id", name="permission_user_id_unique_constraint"
        ),
    )

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    permission = db.Column(AlchemyEnum(TkPermission), nullable=False, index=True)
    user_id = db.Column(
        UUID(), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )


class GroupTkPermission(db.Model, AbstractSortableStatusModel):

    __tablename__ = "group_tk_permission"
    __table_args__ = (
        UniqueConstraint(
            "permission", "group_id", name="permission_group_id_unique_constraint"
        ),
    )

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    permission = db.Column(AlchemyEnum(TkPermission), nullable=False, index=True)
    group_id = db.Column(
        UUID(), db.ForeignKey("group.id", ondelete="CASCADE"), nullable=False
    )
