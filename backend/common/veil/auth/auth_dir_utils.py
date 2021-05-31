"""Extra utils for ldap.

Главная проблема - то, что приходит от AuthenticationDirectory в качестве GUID - совсем не бьется со стандартным
форматом UUID.
"""
import re
from typing import List, Optional


def split_into_chunks(string, chunk_length=2):
    """Split string to chunks fixed length."""
    chunks = []
    while len(string) > 0:
        chunks.append(string[:chunk_length])
        string = string[chunk_length:]
    return chunks


def to_oracle_raw16(string, strip_dashes=True, dashify_result=False):
    """Convert to raw16."""
    oracle_format_indices = [3, 2, 1, 0, 5, 4, 7, 6, 8, 9, 10, 11, 12, 13, 14, 15]
    if strip_dashes:
        string = string.replace("-", "")
    parts = split_into_chunks(string)
    result = ""
    for index in oracle_format_indices:
        result = result + parts[index]
    if dashify_result:
        result = (
            result[:8]
            + "-"  # noqa: W503
            + result[8:12]  # noqa: W503
            + "-"  # noqa: W503
            + result[12:16]  # noqa: W503
            + "-"  # noqa: W503
            + result[16:20]  # noqa: W503
            + "-"  # noqa: W503
            + result[20:]  # noqa: W503
        )
    return result


def escape_bytes(bytes_value):
    """Convert a byte sequence to a properly escaped for LDAP (format BACKSLASH HEX HEX) string."""
    if bytes_value:
        if isinstance(bytes_value, str):
            bytes_value = bytearray(bytes_value, encoding="utf-8")
        escaped = "\\".join([("%02x" % int(b)) for b in bytes_value])
    else:
        escaped = ""
    result = ("\\" + escaped) if escaped else ""
    return result


def pack_guid(string):
    return escape_bytes(bytearray.fromhex(to_oracle_raw16(string)))


def unpack_guid(ba):
    """Convert bytes-string returned by AuthenticationDirectory."""
    hex_s = "".join("%02x" % b for b in ba)
    return to_oracle_raw16(hex_s, True, True)


def unpack_ad_info(ad_info: dict, param_name: str) -> bytes:
    """Проверяет наличие ожидаемой структуры и возвращает значение."""
    # Красиво не сработает, потому что применение условий должно быть последовательным
    if (
        isinstance(ad_info, dict)
        and ad_info.get(param_name)  # noqa: W503
        and isinstance(ad_info[param_name], list)  # noqa: W503
        and isinstance(ad_info[param_name][0], bytes)  # noqa: W503
    ):
        return ad_info[param_name][0]
    return None


def extract_domain_from_username(username: str) -> List[str]:
    """Метод для разделения имени пользователя.

    Разделение по символу @ на имя пользовательской учетной записи и доменное имя контроллера доменов.

    :param username: имя пользователя
    :return: список, содержащий имя пользователской учетной записи (sAMAccountName)
    и доменное имя контроллера доменов
    """
    dog_list = username.split("@")
    if len(dog_list) > 1:
        return dog_list[0], dog_list[1]
    slash_list = username.split("\\")
    if len(slash_list) > 1:
        return slash_list[1], slash_list[0]
    backslash_list = username.split("/")
    if len(backslash_list) > 1:
        return backslash_list[1], None
    return username, None


def get_ad_user_ou(user_info: str) -> Optional[str]:
    """Получения информации о структурном подразделении.

    :param user_info: строка, содержащая имя структурного подразделения (OU).
    :return: имя структурного подразделения
    """
    if user_info:
        for chunk in re.split(r"(?<!\\),", user_info):
            if chunk.startswith("OU="):
                return chunk[3:]


def get_free_ipa_user_ou(user_info: str) -> Optional[str]:
    if not user_info:
        return
    if isinstance(user_info, bytes):
        user_info = user_info.decode()
    user_info = user_info.split(",")
    for attr in user_info:
        if attr.startswith("OU=") or attr.startswith("ou="):
            return attr[3:]


def get_ms_ad_user_groups(user_groups: List[bytes]) -> List[str]:
    """Метод получения имен групп пользователя службы каталогов.

    :param user_groups: список строк, содержащих имена (CN) групп пользователя службы каталогов.
    :return: список имен групп
    """
    groups_names = []
    for group in user_groups:
        group_attrs = re.split(r"(?<!\\),", group.decode())
        for attr in group_attrs:
            if attr.startswith("CN="):
                groups_names.append(attr[3:])
    return groups_names


def get_free_ipa_user_groups(user_groups: List[bytes]) -> List[str]:
    groups_names = []
    for group in user_groups:
        group_attr = group.decode().split(",")
        for attr in group_attr:
            if attr.startswith("CN=") or attr.startswith("cn="):
                groups_names.append(attr[3:])
                break
    return groups_names
