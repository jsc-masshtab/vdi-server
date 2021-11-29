# -*- coding: utf-8 -*-
import shlex
import subprocess
from datetime import datetime

from common.languages import _local_
from common.veil.veil_errors import SimpleError


class Backup:
    @classmethod
    def create_backup(cls, db_user="postgres", db_host="localhost", db_port="5432",
                      backup_dir="/home/user/", backup_name="cluster.sql", creator="system"):
        """Создает бекап БД с помощью 'pg_dumpall'."""
        backup_file = cls.generate_name_with_timestamp(backup_name)
        backup_file = backup_dir + backup_file

        backup_pattern = "sudo pg_dumpall -h {} -U {} -p {} --clean --if-exists --file {}"
        backup_command = backup_pattern.format(db_host, db_user, db_port, backup_file)

        result_backup = subprocess.run(shlex.split(backup_command),
                                       universal_newlines=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

        if result_backup.returncode != 0:
            raise SimpleError(
                _local_("Backup DB failed."),
                description="Return code: {}; strerr: {}; stdout: {}.".format(
                    result_backup.returncode,
                    result_backup.stderr,
                    result_backup.stdout),
                user=creator
            )

        if result_backup.stderr:
            raise SimpleError(
                _local_("Error occurred during creating DB backup. {}.").format(result_backup.stderr),
                user=creator
            )

        return result_backup.returncode

    @staticmethod
    def terminate_sessions(db_name="vdi", db_user="postgres", db_host="localhost", db_port="5432", creator="system"):
        """Отключает все активные соединения у БД."""
        forbid_connections = \
            """sudo psql -h {} -p {} -c "UPDATE pg_database SET datallowconn = 'false' WHERE datname = '{}';" -U {}"""
        forbid_connections = forbid_connections.format(db_host, db_port, db_name, db_user)

        terminate_connections = \
            """sudo psql -h {} -p {} -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{}';" -U {}"""
        terminate_connections = terminate_connections.format(db_host, db_port, db_name, db_user)

        result_forbid_connections = subprocess.run(shlex.split(forbid_connections),
                                                   universal_newlines=True,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)

        if result_forbid_connections.returncode != 0:
            raise SimpleError(
                _local_("Forbid connections failed."),
                description="Return code: {}; strerr: {}; stdout: {}.".format(
                    result_forbid_connections.returncode,
                    result_forbid_connections.stderr,
                    result_forbid_connections.stdout),
                user=creator
            )

        result_terminate_sessions = subprocess.run(shlex.split(terminate_connections),
                                                   universal_newlines=True,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)

        if result_terminate_sessions.returncode != 0:
            raise SimpleError(
                _local_("Terminate sessions failed."),
                description="Return code: {}; strerr: {}; stdout: {}.".format(
                    result_terminate_sessions.returncode,
                    result_forbid_connections.stderr,
                    result_forbid_connections.stdout),
                user=creator
            )

        return result_terminate_sessions.returncode

    @classmethod
    def restore_db(cls, db_user="postgres", db_host="localhost", db_port="5432",
                   backup_dir="/home/user/", backup_file="cluster.sql", creator="system"):
        """Восстанавливает БД из бекапа с помощью 'psql'."""
        backup_file = backup_dir + backup_file
        restore_db = "sudo psql -U {} -h {} -p {} --file {}".format(db_user, db_host, db_port, backup_file)

        cls.terminate_sessions()

        result_restore_db = subprocess.run(shlex.split(restore_db), stdout=subprocess.DEVNULL)

        if result_restore_db.returncode != 0:
            raise SimpleError(
                _local_("Restore DB failed."),
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
    def drop_db(cls, db_name, db_user="postgres", db_host="localhost", db_port="5432", creator="system"):
        """Удаляет БД."""
        drop = """sudo psql -h {} -p {} -c "DROP DATABASE {};" -U {}""".format(db_host, db_port, db_name, db_user)

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
