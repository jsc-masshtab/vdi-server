# -*- coding: utf-8 -*-
"""Generate random string."""
import argparse

from cryptography.fernet import Fernet

from common.veil.auth.django_crypto import get_random_string

SECRET_ARGS = ["SECRET_KEY", "FERNET_KEY", "DB_PASS", "REDIS_PASSWORD"]


def get_secret_value(length: int = 10, bts: bool = False):
    """Random string.

    length: length of random string
    bts: generated string should be bytes
    """
    random_string = get_random_string(length)
    if bts:
        random_string = random_string.encode()
    return random_string


def local_settings_data():
    """Create array with secret_values."""
    secret_pattern_s = "{} = '{}'"
    secret_pattern_b = "{} = {}"
    secret_list = list()

    for arg in SECRET_ARGS:
        if "FERNET" in arg:
            secret_str = secret_pattern_b.format(arg, Fernet.generate_key())
        elif "_KEY" in arg:
            secret_str = secret_pattern_s.format(arg, get_secret_value(50))
        else:
            secret_str = secret_pattern_s.format(arg, get_secret_value(20))
        secret_list.append(secret_str)

    return secret_list


def write_local_settings(txt_data: list, file_name: str = "local_settings.py"):
    """Create file with file_name contains secret values for vdi-server.

    txt_data: list of strings to write
    file_name: File name and full system path

    """
    with open(file_name, "w", encoding="utf-8") as local_settings:
        local_settings.write("# -*- coding: utf-8 -*-")
        local_settings.write("\n\n")
        for line in txt_data:
            local_settings.write(line + "\n")


def parse_args():
    """Arguments parser module.

    file_name: full path to new file

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file_name",
        default="common/local_settings.py",
        type=str,
        help="full path to new file",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    options = local_settings_data()
    write_local_settings(options, file_name=args.file_name)


if __name__ == "__main__":
    main()
