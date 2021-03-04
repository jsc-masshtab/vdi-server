# -*- coding: utf-8 -*-
"""Extra cryptography for controller password store."""

from cryptography.fernet import Fernet
from common.settings import FERNET_KEY


def encrypt(raw_string: str) -> str:
    if isinstance(raw_string, str):
        raw_string = bytes(raw_string, encoding="utf-8")
    encrypted_str = Fernet(FERNET_KEY).encrypt(raw_string).decode("utf-8")
    return encrypted_str


def decrypt(encrypted_string: str) -> str:
    if isinstance(encrypted_string, str):
        encrypted_string = bytes(encrypted_string, encoding="utf-8")
    decrypted_str = Fernet(FERNET_KEY).decrypt(encrypted_string).decode("utf-8")
    return decrypted_str
