# -*- coding: utf-8 -*-
import subprocess
import shlex

from common.settings import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER
from common.veil.veil_graphene import VeilResourceType


class Backup:

    def __init__(self):
        self.docker_prefix = "docker exec vdi-postgres "
        self.is_docker = True

    def create_backup(self, db_user="postgres", db_host="localhost",
                      db_port="5432", backup_filename="/home/cluster.sql"):
        """
        Создает бекап БД с помощью 'pg_dumpall'.
        Команада создаст бекап на сервере vdi-postgres, который в докере, в директории /home
        """
        command_template = "pg_dumpall -U {user} -h {host} -p {port} --clean --if-exists --file={filename}"
        backup_command = command_template.format(user=db_user, host=db_host, port=db_port, filename=backup_filename)

        if self.is_docker:
            backup_command = self.docker_prefix + backup_command

        process = subprocess.run(shlex.split(backup_command))
        print("returncode=", process.returncode)

        if int(process.returncode) != 0:
            print("Command failed. Return code: {}".format(process.returncode))

    def terminate_sessions(self, db_name="vdi", db_user="postgres"):
        """Отключает все активные соединения у БД."""
        forbid_connections = \
            """psql -c "UPDATE pg_database SET datallowconn = 'false' WHERE datname = '{name}';" -U {user}"""
        forbid_connections = forbid_connections.format(name=db_name, user=db_user)

        terminate_connections = \
            """psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{name}';" -U {user}"""
        terminate_connections = terminate_connections.format(name=db_name, user=db_user)

        if self.is_docker:
            forbid_connections = self.docker_prefix + forbid_connections
            terminate_connections = self.docker_prefix + terminate_connections

        result_update_system_catalog = subprocess.run(shlex.split(forbid_connections))
        print("forbid_connections returncode=", result_update_system_catalog.returncode)
        result_terminate_sessions = subprocess.run(shlex.split(terminate_connections))
        print("terminate_connections returncode=", result_terminate_sessions.returncode)

    def restore_postgres_db(self, db_user="postgres", backup_file="/home/cluster.sql"):
        """Восстанавливает БД из бекапа."""
        restore_db = "psql -U {user} -f {backup_file} postgres".format(user=db_user, backup_file=backup_file)

        if self.is_docker:
            restore_db = self.docker_prefix + restore_db

        self.terminate_sessions()
        result_restore_db = subprocess.run(shlex.split(restore_db))
        print("result_restore_db returncode=", result_restore_db.returncode)

    def drop_db(self, db_name):
        """Удаляет БД"""
        drop = """psql -c "DROP DATABASE {};" -U postgres""".format(db_name)

        if self.is_docker:
            drop = self.docker_prefix + drop

        self.terminate_sessions()
        result_drop = subprocess.run(shlex.split(drop), stdout=subprocess.DEVNULL)
        print("result_drop returncode=", result_drop.returncode)

    def check_backup(self):
        pass


backup = Backup()
# backup.terminate_sessions()
# backup.restore_postgres_db(backup_file="/home/cluster_base_config.sql")
# backup.create_backup()
