# -*- coding: utf-8 -*-

from common.settings import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

import subprocess
import shlex


# print("DB_HOST:", DB_HOST)
# print("DB_NAME:", DB_NAME)
# print("DB_PASS:", DB_PASS)
# print("DB_PORT:", DB_PORT)
# print("DB_USER:", DB_USER, "\n")


def create_backup():  # args: host, user, password, table_name
    """Создает бекап БД с помощью 'pg_dumpall'."""
    # Команада создаст бекап на сервере vdi-postgres, который в докере, в директории /home
    command = "docker exec vdi-postgres pg_dumpall -U postgres -h localhost -p 5432 --clean --if-exists --file=/home/cluster.sql"
    process = subprocess.run(shlex.split(command))

    print("returncode=", process.returncode)

    if int(process.returncode) != 0:
        print("Command failed. Return code: {}".format(process.returncode))


def terminate_db_sessions(is_docker=True):
    """Отключает все активные соединения у БД."""
    update_system_catalog = """psql -c "UPDATE pg_database SET datallowconn = 'false' WHERE datname = 'vdi';" -U postgres"""
    terminate_sessions = """psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'vdi';" -U postgres"""
    docker_prefix = "docker exec vdi-postgres "

    if is_docker:
        update_system_catalog = docker_prefix + update_system_catalog
        terminate_sessions = docker_prefix + terminate_sessions

    result_update_system_catalog = subprocess.run(shlex.split(update_system_catalog))
    print("update_system_catalog returncode=", result_update_system_catalog.returncode)
    result_terminate_sessions = subprocess.run(shlex.split(terminate_sessions))
    print("terminate_sessions returncode=", result_terminate_sessions.returncode)


def restore_postgres_db(backup_file):
    """Восстанавливает БД из бекапа."""
    restore_db = "docker exec vdi-postgres psql -U postgres -f {} postgres".format(backup_file)
    result_restore_db = subprocess.run(shlex.split(restore_db))
    print("result_restore_db returncode=", result_restore_db.returncode)


def check_backup():
    pass


def drop_db(db_name="vdi"):
    """Удаляет БД"""
    drop = """docker exec vdi-postgres psql -c "DROP DATABASE {};" -U postgres""".format(db_name)
    terminate_db_sessions()
    result_drop = subprocess.run(shlex.split(drop), stdout=subprocess.DEVNULL)
    print("result_drop returncode=", result_drop.returncode)


# create_backup()
# terminate_db_sessions()
# restore_postgres_db("/home/cluster.sql")
# drop_db()
