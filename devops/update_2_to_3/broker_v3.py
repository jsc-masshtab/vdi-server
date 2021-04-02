# -*- coding: utf-8 -*-
from psycopg2 import connect as db_connect
from common.settings import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER, PAM_AUTH, PAM_USER_GROUP
from common.veil.auth.veil_pam import veil_auth_class
import asyncio

dump_1_f = '/tmp/broker_pt_1.sql'
dump_2_f = '/tmp/broker_pt_2.sql'
dump_3_f = '/tmp/broker_pt_3.sql'

connection_str = "postgres://{U}:{PS}@{H}:{PT}/{N}".format(U=DB_USER, PS=DB_PASS, H=DB_HOST, PT=DB_PORT, N=DB_NAME)


def import_dump(fname: str, dsn: str):
    with open(fname, "r") as dump_1:
        lines = dump_1.readlines()
        with db_connect(dsn) as vdi_conn:
            with vdi_conn.cursor() as vdi_curs:
                for line in lines:
                    sql_str = line.rstrip()
                    if sql_str and not sql_str.startswith('--'):
                        try:
                            sql_str = sql_str.replace('user_for_export', 'user')
                            sql_str = sql_str.replace('pool_for_export', 'pool')
                            vdi_curs.execute(sql_str)
                        except Exception as E:
                            print(E)
                        finally:
                            vdi_curs.execute('commit;')


async def create_user(username: str, email: str = None):
    g = ",VDI,,,{}".format(email) if email else ",VDI,,,"
    return await veil_auth_class.user_create(
        username=username, group=PAM_USER_GROUP, gecos=g
    )


async def main():
    if not PAM_AUTH:
        return
    with db_connect(connection_str) as vdi_conn:
        with vdi_conn.cursor() as vdi_curs:
            vdi_curs.execute(
                "select u.id, u.username, u.email from public.user as u where u.is_active and not u.is_superuser;")
            users = vdi_curs.fetchall()
    if not users:
        return 'There is no active users.'
    created_users = set()
    for user in users:
        user_id = user[0]
        user_username = user[1]
        user_email = user[2]
        try:
            if user_username != 'vdiadmin':
                await create_user(username=user_username, email=user_email)
                created_users.add(user_id)
        except Exception as E:
            print('Can`t create user {}'.format(user_username))
            print(E)

    if not created_users:
        return 'There is no new users created after migration.'

    # блокируем добавленных пользователей
    with db_connect(connection_str) as vdi_conn:
        with vdi_conn.cursor() as vdi_curs:
            for user in created_users:
                vdi_curs.execute("update public.user set is_active = False where id = %s;", (user, ))
                vdi_curs.execute("commit;")


if __name__ == '__main__':
    import_dump(dump_1_f, connection_str)
    import_dump(dump_2_f, connection_str)
    import_dump(dump_3_f, connection_str)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
