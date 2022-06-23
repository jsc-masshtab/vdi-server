# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.settings import PRIVATE_PEM_FPATH


invalid_license_data = {
    "verbose_name": "Unlicensed Veil VDI",
    "thin_clients_limit": 0,
    "uuid": str(uuid4()),
}


class License(db.Model):
    __tablename__ = "license"
    uuid = db.Column(UUID(), primary_key=True, default=uuid4)
    verbose_name = db.Column(db.Unicode(length=256), default="Unlicensed Veil VDI")
    thin_clients_limit = db.Column(db.Integer(), nullable=False, default=0)
    expiration_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    support_expiration_date = db.Column(db.DateTime(timezone=True), server_default=func.now())

    company = db.Column(db.Unicode(length=256))
    email = db.Column(db.Unicode(length=256))

    date_format = db.Column(db.Unicode(length=128), default="%Y-%m-%d")

    @classmethod
    async def upload_license(cls, file_body, user="system"):

        try:
            with open(cls.get_veil_pem(), "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(), backend=default_backend(), password=None
                )

                # decrypt data
                decrypted_data_bytes = private_key.decrypt(
                    file_body,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None,
                    ),
                )
                decrypted_data = (
                    decrypted_data_bytes.decode("utf-8")
                    if decrypted_data_bytes
                    else None
                )

                # При отсутствии значения в decrypted_data сработает TypeError
                license_data = json.loads(decrypted_data)

                date_format = license_data["date_format"]
                license_data["expiration_date"] = cls.convert_date(license_data["expiration_date"], date_format)
                license_data["support_expiration_date"] = \
                    cls.convert_date(license_data["support_expiration_date"], date_format)

                # Save to db
                license_obj = await cls.save_license_data_to_db(license_data)
                msg = _local_("Valid license key is uploaded.")
                await system_logger.info(msg, user=user)
                return license_obj

        except (OSError, TypeError, ValueError) as ex:

            if isinstance(ex, OSError):
                await system_logger.error(_local_("OS error."), description=str(ex), user=user)
            else:
                await system_logger.error(_local_("Wrong Licence file format."), description=str(ex), user=user)

            return await cls.save_license_data_to_db(invalid_license_data)

    @classmethod
    async def get_license(cls):
        license_obj = await cls.query.gino.first()
        if not license_obj:
            license_obj = await cls.save_license_data_to_db(invalid_license_data)
        return license_obj

    @classmethod
    async def save_license_data_to_db(cls, license_data):
        async with db.transaction():
            await db.status(db.text("TRUNCATE TABLE license;"))
            license_obj = await License.create(**license_data)
            return license_obj

    @classmethod
    def get_veil_pem(cls):
        return PRIVATE_PEM_FPATH if os.path.exists(PRIVATE_PEM_FPATH) else None

    @classmethod
    def convert_date(cls, date_str, date_format) -> datetime.date:

        if not date_str or (isinstance(date_str, str) and len(date_str) < 8):
            date_str = "2020-05-01"

        return datetime.strptime(date_str, date_format).date()

    @property
    def expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expiration_date

    @property
    def support_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.support_expiration_date

    @property
    def remaining_days(self):
        return self.now_delta_days(self.expiration_date)

    @property
    def support_remaining_days(self):
        return self.now_delta_days(self.support_expiration_date)

    @staticmethod
    def now_delta_days(date: datetime):
        delta = date - datetime.now(timezone.utc)
        if delta.days < 0:
            return 0
        return delta.days

    @property
    def real_thin_clients_limit(self) -> int:
        return 0 if self.expired else self.thin_clients_limit
