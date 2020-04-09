#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import uuid
import json
import argparse
import logging

import sqlite3
import psycopg2
import requests

from settings import DB_NAME, DB_PASS, DB_PORT, DB_USER
from auth.utils import hashers

logger = logging.getLogger('VDI ammo generator')

parser = argparse.ArgumentParser(description='VDI ammo generator for Yandex.Tank.')
parser.add_argument('--users_count', type=int, default=10, metavar='Num of users to create.')
parser.add_argument('--mode', type=str, default='create', choices=['create', 'delete'], help='Working mode.')
parser.add_argument('--remote_host', type=str, default='127.0.0.1', help='Remote host address.')
parser.add_argument('--tag', type=str, default='local_auth', help='Tag in report.')


def make_ammo(method, url, headers, case, body):
    """ makes phantom ammo (c) Yandex """

    # http request w/o entity body template
    req_template = (
        "%s %s HTTP/1.1\r\n"
        "%s\r\n"
        "\r\n"
    )

    # http request with entity body template
    req_template_w_entity_body = (
        "%s %s HTTP/1.1\r\n"
        "%s\r\n"
        "Content-Length: %d\r\n"
        "\r\n"
        "%s\r\n"
    )

    if not body:
        req = req_template % (method, url, headers)
    else:
        req = req_template_w_entity_body % (method, url, headers, len(body), body)

    # phantom ammo template
    ammo_template = (
        "%d %s\n"
        "%s"
    )

    return ammo_template % (len(req), case, req)


def init_logger(level=logging.DEBUG):
    logger.setLevel(level)
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)


def get_tank_db_connection():
    # Если файл отсутствует, инициализация создаст новый файл с указанным именем
    db_filename = '.tank'
    connection = sqlite3.connect(db_filename)
    return connection


def get_vdi_db_connection(host, port, database, user, password):
    logger.debug('Connect to {} db {}:{}'.format(database, host, port))
    vdi_db_connection = psycopg2.connect(user=user, password=password, host=host, port=port, database=database)
    vdi_cursor = vdi_db_connection.cursor()
    vdi_cursor.execute('SELECT version();')
    version = vdi_cursor.fetchone()
    logger.debug('Postgres version: {}'.format(*version))
    return vdi_db_connection


def create_vdi_users(vdi_db_connection, users_list):
    """Создает пользователей в БД vdi-server"""
    insert_sql = """insert
                        into
                        public.user (id,
                        username,
                        password,
                        is_superuser,
                        is_active)
                    values (%s,
                    %s,
                    %s,
                    false,
                    true);"""
    with vdi_db_connection:
        with vdi_db_connection.cursor() as cursor:
            cursor.executemany(query=insert_sql, vars_list=users_list)


def create_tank_users_table(tank_connection):
    create_table_sql = """CREATE TABLE IF NOT EXISTS users (
                                            id text PRIMARY KEY,
                                            username text NOT NULL,
                                            encoded_password text NOT NULL,
                                            api_token text NOT NULL
                                        ); """

    with tank_connection as cursor:
        cursor.execute(create_table_sql)


def create_tank_users(tank_connection, users_list):
    create_tank_users_table(tank_connection)

    insert_sql = """insert into users (id, username, encoded_password, api_token) values (?, ?, ?, ?)"""
    with tank_connection as cursor:
        cursor.executemany(insert_sql, users_list)


def drop_tank_users_table(tank_connection):
    tank_delete_sql = "DROP TABLE users;"
    with tank_connection as cursor:
        cursor.execute(tank_delete_sql)


def get_tokens(users_list, remote_host):
    """Наработка для дальнейших запросов требующих токена"""

    url = 'http://{remote_host}:8888/auth'.format(remote_host=remote_host)
    user_token_list = list()

    for user in users_list:
        user_values_list = user.copy()

        username = user[1]
        payload = {"username": username, "password": username}
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            raise AssertionError('Fail to get response from VDI API.')
        data = r.json()
        if not isinstance(data, dict):
            raise AssertionError('Can\'t get VDI response data.')

        token = data['data']['access_token']
        user_values_list.append(token)
        user_token_list.append(user_values_list)
    return user_token_list


def init_users(vdi_db_connection, tank_connection, users_count: int, remote_host: str):
    logger.info('Creating temporary users...')

    users_list = list()
    # create temporary users list
    for i in range(users_count):
        user_id = str(uuid.uuid4())
        username = 'tank_user_{}'.format(i)
        encoded_password = hashers.make_password(username)
        users_list.append([user_id, username, encoded_password])

    # create temporary users in vdi db
    create_vdi_users(vdi_db_connection, users_list)

    # get created users api-tokens
    user_token_list = get_tokens(users_list, remote_host)

    # create temporary users in tank db for future execution
    create_tank_users(tank_connection, user_token_list)


def get_auth_ammo(tank_connection, remote_host, tag):
    method = 'POST'
    url = '/auth'
    case = tag

    headers = "Host: {remote_host}\r\n" + \
              "User-Agent: tank\r\n" + \
              "Accept: */*\r\n" + \
              "Content-Type: application/json\r\n" + \
              "Connection: Close".format(remote_host=remote_host)

    users_list = get_tank_users(tank_connection)
    with open('ammo', 'w') as data_file:
        for user in users_list:
            username = user[1]
            body = json.dumps({"username": username, "password": username})
            data_file.write(make_ammo(method, url, headers, case, body))


def get_tank_users(tank_connection):
    tank_select_sql = "SELECT id, username, encoded_password, api_token from users;"

    with tank_connection as cursor:
        cursor = cursor.execute(tank_select_sql)
        users_list = cursor.fetchall()
    return users_list


def delete_users(vdi_db_connection, tank_connection):
    vdi_delete_sql = "DELETE FROM public.user as u where u.id in (%s)"

    logger.info('Deleting all temporary users.')

    users_list = get_tank_users(tank_connection)
    with vdi_db_connection:
        with vdi_db_connection.cursor() as cursor:
            cursor.executemany(query=vdi_delete_sql, vars_list=[[user[0]] for user in users_list])

    drop_tank_users_table(tank_connection)
    logger.info('Temporary users deleted.')


def main():
    # TODO: transaction rollbacks if exception

    init_logger()
    logger.info('Starting VDI ammo generator...')

    args = parser.parse_args()

    vdi_connection = get_vdi_db_connection(host=args.remote_host, port=DB_PORT, database=DB_NAME, user=DB_USER,
                                           password=DB_PASS)
    tank_connection = get_tank_db_connection()

    if args.mode == 'create':
        init_users(vdi_connection, tank_connection, args.users_count, args.remote_host)
        get_auth_ammo(tank_connection, args.remote_host, args.tag)
    elif args.mode == 'delete':
        delete_users(vdi_connection, tank_connection)

    logger.info('Closing connections.')
    vdi_connection.close()
    tank_connection.close()

    logger.info('Finish.')


if __name__ == "__main__":
    main()
