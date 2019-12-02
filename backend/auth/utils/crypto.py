# -*- coding: utf-8 -*-
""" Extra cryptography for controller password store. """
# TODO: Заменить на какое-нибудь шифрование напрямую в БД? Какой-нибудь pg_crypto?

from cryptography.fernet import Fernet
from settings import FERNET_KEY


def encrypt(raw_string: bytes) -> str:
    if isinstance(raw_string, str):
        raw_string = bytes(raw_string, encoding='utf-8')
    encrypted_str = Fernet(FERNET_KEY).encrypt(raw_string).decode('utf-8')
    return encrypted_str


def decrypt(encripted_string: bytes) -> str:
    if isinstance(encripted_string, str):
        encripted_string = bytes(encripted_string, encoding='utf-8')
    decrypted_str = Fernet(FERNET_KEY).decrypt(encripted_string).decode('utf-8')
    return decrypted_str
