# -*- coding: utf-8 -*-

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import json
import os

from settings import CONF_PATH


class License:
    # TODO: описать структуру ключа?

    def __init__(self, serial_key_name: str = None, pem_name: str = None):
        """

        :param serial_key_name: имя файла
        :param pem_name:  имя pem-файла
        """

        veil_serial_key = 'serial.key' if not serial_key_name else serial_key_name
        self.veil_serial_key_path = os.path.join(CONF_PATH, veil_serial_key)
        self.veil_serial_key = self.veil_serial_key_path if os.path.exists(self.veil_serial_key_path) else None

        veil_pem = 'controller.pem' if not pem_name else pem_name
        veil_pem_path = os.path.join(CONF_PATH, veil_pem)
        self.veil_pem = veil_pem_path if os.path.exists(veil_pem_path) else None

    def get_license(self):
        """
        Проверяется ключ из файла.
        """

        try:
            with open(self.veil_pem, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend())
                with open(self.veil_serial_key, "rb") as f:
                    data = f.read()
                    decrypted_data_bytes = private_key.decrypt(
                        data,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None))

                    decrypted_data = decrypted_data_bytes.decode('utf-8') if decrypted_data_bytes else None
                    # Если на предыдущем шаге отсутствовало значение в decrypted_data, то сработает TypeError
                    decrypted_data = json.loads(decrypted_data)
                    return decrypted_data
        except TypeError as type_err:  # noqa
            # TODO: log exception
            default_data = {
                "verbose_name": "Unlicensed Veil VDI",
                "thin_clients_limit": 0,
                "expired_time": None,
                "support_expired_time": None
            }
            return default_data

    def save_license_key(self, file_body):

        try:
            with open(self.veil_serial_key_path, 'wb') as key_file:
                key_file.write(file_body)
                # TODO: logging
        except IOError as e:
            # TODO: logging
            print(e)

    def upload_license(self, file_body):
        self.save_license_key(file_body)
        # TODO: была мысль вернуть прежний файл с лицензией, если что-то пошло не так, но идея кажется сомнительной
        return License().get_license()
