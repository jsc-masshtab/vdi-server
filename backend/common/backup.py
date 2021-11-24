# -*- coding: utf-8 -*-
import shlex
import subprocess
from datetime import datetime

from common.languages import _local_
from common.veil.veil_errors import SilentError, SimpleError


class Backup:
    @classmethod
    def create_backup(cls, db_user="postgres", db_host="localhost", db_port="5432",
                      backup_dir="/home/", backup_name="cluster.sql", creator="system"):
        """Создает бекап БД с помощью 'pg_dumpall'."""
        backup_file = cls.generate_name_with_timestamp(backup_name)
        backup_file = backup_dir + backup_file

        command_pattern = "pg_dumpall -U {} -h {} -p {} --clean --if-exists --file={}"
        backup_command = command_pattern.format(db_user, db_host, db_port, backup_file)

        result_backup = subprocess.run(shlex.split(backup_command))

        if result_backup.returncode != 0:
            raise SimpleError(
                _local_("Backup DB failed."),
                description="Return code: {}".format(result_backup.returncode),
                user=creator
            )

        if result_backup.stderr:
            raise SimpleError(
                _local_("Error occurred during creating DB backup. {}.").format(result_backup.stderr),
                user=creator
            )

        return result_backup.returncode

    @staticmethod
    def terminate_sessions(db_name="vdi", db_user="postgres", creator="system"):
        """Отключает все активные соединения у БД."""
        forbid_connections = \
            """psql -c "UPDATE pg_database SET datallowconn = 'false' WHERE datname = '{}';" -U {}"""
        forbid_connections = forbid_connections.format(db_name, db_user)

        terminate_connections = \
            """psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{}';" -U {}"""
        terminate_connections = terminate_connections.format(db_name, db_user)

        result_forbid_connections = subprocess.run(shlex.split(forbid_connections), stdout=subprocess.DEVNULL)

        if result_forbid_connections.returncode != 0:
            raise SilentError(
                _local_("Forbid connections failed.")
            )

        result_terminate_sessions = subprocess.run(shlex.split(terminate_connections), stdout=subprocess.DEVNULL)

        if result_terminate_sessions.returncode != 0:
            raise SimpleError(
                _local_("Terminate sessions failed."),
                description="Return code: {}".format(result_terminate_sessions.returncode),
                user=creator
            )

        return result_terminate_sessions.returncode

    @classmethod
    def restore_db(cls, db_user="postgres", backup_dir="/home/",
                   backup_file="cluster.sql", creator="system"):
        """Восстанавливает БД из бекапа с помощью 'psql'."""
        backup_file = backup_dir + backup_file
        restore_db = "psql -U {} -f {} postgres".format(db_user, backup_file)

        cls.terminate_sessions()

        result_restore_db = subprocess.run(shlex.split(restore_db), stdout=subprocess.DEVNULL)

        if result_restore_db.returncode != 0:
            raise SimpleError(
                _local_("Restore BD failed."),
                description="Return code: {}".format(result_restore_db.returncode),
                user=creator
            )

        if result_restore_db.stderr:
            raise SimpleError(
                _local_("Error occurred during restoring DB. {}.").format(result_restore_db.stderr),
                user=creator
            )

        return result_restore_db.returncode

    @classmethod
    def drop_db(cls, db_name, creator="system"):
        """Удаляет БД."""
        drop = """psql -c "DROP DATABASE {};" -U postgres""".format(db_name)

        cls.terminate_sessions()

        result_drop = subprocess.run(shlex.split(drop), stdout=subprocess.DEVNULL)

        if result_drop.returncode != 0:
            raise SimpleError(
                _local_("Drop DB failed."),
                description="Return code: {}".format(result_drop.returncode),
                user=creator
            )

        return result_drop.returncode

    @staticmethod
    def generate_name_with_timestamp(name):
        now = datetime.now().replace(microsecond=0)
        name = str(now) + "_" + str(name)
        return name.replace(" ", "_")
