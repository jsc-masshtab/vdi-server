# -*- coding: utf-8 -*-
"""Ограничение лицензии действует только на подключение тонких клиентов.

Если лицензия истекла - отсутствует возможность подключиться с тонкого клиента.

    TODO: заменить реалилизацию синглтона на декоратор?
    def singleton(cls):
        instances = {}
        def getinstance():
            if cls not in instances:
                instances[cls] = cls()
            return instances[cls]
        return getinstance

    @singleton
    class MyClass:
    ...
"""

import datetime
import json
import os
from uuid import uuid4

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from common.log.journal import system_logger
from common.settings import PRIVATE_PEM_FPATH, SERIAL_KEY_FPATH
from common.veil.veil_redis import read_license_dict, save_license_dict


class LicenseData:
    """Структура лицензионного ключа."""

    def __init__(
        self,
        uuid: str,
        verbose_name: str,
        thin_clients_limit: int = 0,
        expiration_date: str = None,
        support_expiration_date: str = None,
        company: str = None,
        email: str = None,
        date_format: str = "%Y-%m-%d",
    ):
        self._expiration_date = expiration_date
        self._support_expiration_date = support_expiration_date
        self.date_format = date_format

        self.uuid = uuid
        self.verbose_name = verbose_name
        self.thin_clients_limit = thin_clients_limit
        self.company = company
        self.email = email

    @property
    def expiration_date(self) -> datetime.date:
        expiration_date = self._expiration_date
        if not expiration_date or (
            isinstance(expiration_date, str) and len(expiration_date) < 8
        ):
            expiration_date = "2020-05-01"
        return self.convert_to_date(expiration_date)

    @property
    def support_expiration_date(self) -> datetime.date:
        support_expiration_date = self._support_expiration_date
        if not support_expiration_date or (
            isinstance(support_expiration_date, str)
            and len(support_expiration_date) < 8  # noqa: W503
        ):
            support_expiration_date = "2020-05-01"
        return self.convert_to_date(support_expiration_date)

    @property
    def expired(self) -> bool:
        return datetime.date.today() > self.expiration_date

    @property
    def support_expired(self) -> bool:
        return datetime.date.today() > self.support_expiration_date

    @property
    def remaining_days(self):
        return self.now_delta_days(self.expiration_date)

    @property
    def support_remaining_days(self):
        return self.now_delta_days(self.support_expiration_date)

    @property
    def all_attrs(self):
        return dict(
            vars(self),
            expired=self.expired,
            support_expired=self.support_expired,
            expiration_date=self.expiration_date,
            support_expiration_date=self.support_expiration_date,
            remaining_days=self.remaining_days,
            support_remaining_days=self.support_remaining_days,
        )

    @property
    def public_attrs_dict(self):
        public_dict = dict()
        for attr in self.all_attrs:
            if attr.startswith("_"):
                continue

            attr_value = self.all_attrs[attr]
            if isinstance(attr_value, datetime.date):
                attr_value = str(attr_value)

            public_dict[attr] = attr_value
        return public_dict

    @property
    def new_license_attrs_dict(self):
        public_dict = self.public_attrs_dict
        public_dict.pop("expired")
        public_dict.pop("support_expired")
        public_dict.pop("remaining_days")
        public_dict.pop("support_remaining_days")
        return public_dict

    @property
    def public_attrs_json(self):
        return json.dumps(self.public_attrs_dict)

    @property
    def new_license_attrs_json(self):
        return json.dumps(self.new_license_attrs_dict)

    def convert_to_date(self, date_str: str) -> datetime.date:
        return datetime.datetime.strptime(date_str, self.date_format).date()

    @staticmethod
    def now_delta_days(date: datetime.date):
        delta = date - datetime.date.today()
        if delta.days < 0:
            return 0
        return delta.days


class License:
    """Singleton лицензии. Борг показался идейно неправильным."""

    class __Singleton:
        def __init__(self):
            """При инициализации считываем параметры лицензии из файла."""
            self.veil_serial_key_path = SERIAL_KEY_FPATH
            self.veil_pem_path = PRIVATE_PEM_FPATH
            self.license_data = self.get_license_from_file()

        @property
        def date_format(self):
            return self.license_data.date_format

        @property
        def veil_serial_key(self):
            return (
                self.veil_serial_key_path
                if os.path.exists(self.veil_serial_key_path)
                else None
            )

        @property
        def veil_pem(self):
            return self.veil_pem_path if os.path.exists(self.veil_pem_path) else None

        @property
        def expiration_date(self) -> bool:
            return self.license_data.expiration_date

        @property
        def support_expiration_date(self) -> bool:
            return self.license_data.support_expiration_date

        @property
        def support_expired(self) -> bool:
            return self.license_data.support_expired

        @property
        def expired(self) -> bool:
            return self.license_data.expired

        @property
        def thin_clients_limit(self) -> int:
            return 0 if self.expired else self.license_data.thin_clients_limit

        @property
        def support_remaining_days(self):
            return self.license_data.support_remaining_days

        @property
        def remaining_days(self):
            return self.license_data.remaining_days

        @property
        def take_verbose_name(self):
            return self.license_data.verbose_name

        @property
        def license_data(self):
            return LicenseData(**read_license_dict(dict_name="license_dict"))

        @license_data.setter
        def license_data(self, license_data: LicenseData):
            return save_license_dict(
                dict_name="license_dict", data=license_data.new_license_attrs_dict
            )

        def get_license_from_file(self):
            """Проверяется ключ из файла."""
            try:
                with open(self.veil_pem, "rb") as key_file:
                    private_key = serialization.load_pem_private_key(
                        key_file.read(), backend=default_backend(), password=None
                    )

                    with open(self.veil_serial_key, "rb") as f:
                        data = f.read()
                        decrypted_data_bytes = private_key.decrypt(
                            data,
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
            except (TypeError, FileNotFoundError, ValueError):
                system_logger._debug("Licence file or vdi server key not found.")
                license_data = {
                    "verbose_name": "Unlicensed Veil VDI",
                    "thin_clients_limit": 0,
                    "uuid": str(uuid4()),
                }
            try:
                self.license_data = LicenseData(**license_data)
            except TypeError:
                # Ключ удается расшифровать, но он не подходит по структуре. Скорее всего это Veil-ключ
                license_data = {
                    "verbose_name": "Unlicensed Veil VDI",
                    "thin_clients_limit": 0,
                    "uuid": str(uuid4()),
                }
                self.license_data = LicenseData(**license_data)
            return self.license_data

        def save_license_key(self, file_body):
            with open(self.veil_serial_key_path, "wb") as key_file:
                key_file.write(file_body)

        def upload_license(self, file_body):
            self.save_license_key(file_body)
            return self.get_license_from_file().public_attrs_dict

    instance = None

    def __new__(cls):
        if not cls.instance:
            cls.instance = cls.__Singleton()
        return cls.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
