# -*- coding: utf-8 -*-
import re
import secrets
import string
from enum import Enum
from functools import wraps


class PassSecLevel(Enum):  # PasswordSecurityLevel

    LOW = "LOW"
    MIDDLE = "MIDDLE"
    HIGH = "HIGH"


LOWER = "a-z"
UPPER = "A-Z"
DIGITAL = "0-9"
SYMBOLS = "!@#$%^&*\\-_=+.,\[\]"  # noqa
GROUP_LIST = [LOWER, UPPER, DIGITAL, SYMBOLS]
RE_TEMPLATE = r"^([{}]*[{}]+[{}]*)$".format("".join(GROUP_LIST), "{}", "".join(GROUP_LIST))
CHARACTER_GROUPS = [
    RE_TEMPLATE.format(LOWER),
    RE_TEMPLATE.format(UPPER),
    RE_TEMPLATE.format(DIGITAL),
    RE_TEMPLATE.format(SYMBOLS)
]
SECURE_LEVELS = {
    PassSecLevel.LOW: dict(
        min_length=3,
        groups_count=1,
        symbol_groups=CHARACTER_GROUPS[:-1],
        required_symbol_groups=[]),
    PassSecLevel.MIDDLE: dict(
        min_length=5,
        groups_count=2,
        symbol_groups=CHARACTER_GROUPS[:-1],
        required_symbol_groups=[]),
    PassSecLevel.HIGH: dict(
        min_length=8,
        groups_count=3,
        symbol_groups=CHARACTER_GROUPS,
        required_symbol_groups=CHARACTER_GROUPS[:-2])
}
SPLITTERS = "-|\\.|_|@"
PART_MIN_LENGTH = 2


def password_check_response(function):
    @wraps(function)
    def wrapper(*args, **kwargs) -> dict:
        try:
            result, comment, comment_values = function(*args, **kwargs)
            return {"name": function.__name__,
                    "result": result,
                    "comment": comment,
                    "comment_values": comment_values}
        except Exception as e:
            return {"name": function.__name__,
                    "result": False,
                    "comment": str(e),
                    "comment_values": {}}
    return wrapper


@password_check_response
def password_check(password: str, secure_level_id: PassSecLevel, login: str = ""):
    comment_values = {"LOWER": LOWER,
                      "UPPER": UPPER,
                      "DIGITAL": DIGITAL,
                      "SYMBOLS": SYMBOLS,
                      "secure_level_id": secure_level_id,
                      "login": login}
    # проверка ключа уровня безопасности
    if secure_level_id in SECURE_LEVELS.keys():
        secure_level_params = SECURE_LEVELS[secure_level_id]
    else:
        comment = "Not existing secure level ID provided: {secure_level_id}."
        return False, comment, comment_values

    comment_values["groups_count"] = secure_level_params["groups_count"]

    if secure_level_id == PassSecLevel.HIGH:
        # проверка наличия логина при высоком уровне безопасности
        if not login:
            comment = "No user login provided with {secure_level_id} secure level."
            return False, comment, comment_values
        else:
            # проверка отсутствия совпадений логина и пароля
            comment = "Provided password is too similar to login {login} " \
                      "for {secure_level_id} secure level."
            if login.lower() in password.lower() or password.lower() in login.lower():
                return False, comment, comment_values
            for login_part in re.split(SPLITTERS, login):
                if login_part and len(login_part) >= PART_MIN_LENGTH and login_part.lower() in password.lower():
                    return False, comment, comment_values

    # проверка количества символов
    if len(password) < secure_level_params["min_length"]:
        comment = f"Provided password is too short for {secure_level_id.value} secure level."
        return False, comment, comment_values

    # проверка наличия символов из достаточного количества разных групп
    groups_matched = 0
    for regexp in secure_level_params["symbol_groups"]:
        if re.match(regexp, password):
            groups_matched += 1
    if not groups_matched:
        comment = "Provided password contains invalid characters. " \
                  "Allowed characters: {LOWER}, {UPPER}, {DIGITAL}, {SYMBOLS}."
        return False, comment, comment_values
    if groups_matched < secure_level_params["groups_count"]:
        comment = "Provided password must contain characters at least from {groups_count} " \
                  "different groups for {secure_level_id} secure level. Character groups: "
        if secure_level_id == PassSecLevel.HIGH:
            comment += f"{'{LOWER}, {UPPER}, {DIGITAL}, {SYMBOLS}'}."
        else:
            comment += f"{'{LOWER}, {UPPER}, {DIGITAL}'}."
        return False, comment, comment_values

    # проверка наличия символов из обязательных групп
    for regexp in secure_level_params["required_symbol_groups"]:
        if not re.match(regexp, password):
            comment = "Provided password must contain lower and upper case letters " \
                      "for {secure_level_id} secure level."
            return False, comment, comment_values

    return True, "Provided password has been verified successfully " \
                 "for {secure_level_id} secure level.", comment_values


def generator(length: int = 16) -> str:
    """
    Функция генерации пароля заданной длины.

    Используются символы: [a-zA-Z0-9].
    :param length: длина пароля
    :return: сгенерированный пароль заданной длины
    """
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))
