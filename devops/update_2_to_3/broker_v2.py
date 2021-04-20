# -*- coding: utf-8 -*-
import asyncio
from psycopg2 import connect as db_connect
from veil_api_client import VeilClient

from common.settings import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DSN = "postgres://{U}:{PS}@{H}:{PT}/{N}".format(U=DB_USER, PS=DB_PASS, H=DB_HOST, PT=DB_PORT, N=DB_NAME)
# Запросы создания временных таблиц для таблиц с изменившейся структурой
# Только активные НЕ администраторы (суперпользователи)
temporary_users_query = """create table if not exists user_for_export as
                                 (select * from public.user as us
                                 where not us.is_superuser and us.is_active);"""
# Владельцы (в 3.0.0 убрали роли как возможные владельцы объектов)
temporary_entity_owner_query = """create table if not exists entity_owner as (
                                  select ero.id, ero.entity_id , ero.user_id, ero.group_id
                                  from entity_role_owner ero);"""
# Пулы - больше нет нод, кластеров и датапулов - теперь только пул ресурсов, который, будет установлен позже.
temporary_pools_query = """create table if not exists pool_for_export as (
                           select
                           p.id,
                           p.verbose_name,
                           p.status,
                           p.controller,
                           p.keep_vms_on,
                           p.connection_types,
                           tc.resource_pool_id
                           from
                           pool p
                           left join tmp_controller as tc on
                           p.controller = tc.id);"""
# Получаем данные для будущего подключения к контроллерам
controllers_query = """select c.id, c.address, c.token from public.controller as c;"""
# В controller_dict хранятся данные для будущего подключения к контроллерам и выявления пула ресурсов
controllers_dict = dict()


async def main():
    # Подключение к СТАРОЙ БД для формирования временных таблиц и ресурсов миграции
    with db_connect(DSN) as vdi_conn:
        with vdi_conn.cursor() as vdi_curs:
            vdi_curs.execute(temporary_users_query)
            vdi_curs.execute(temporary_entity_owner_query)
            # vdi_curs.execute(temporary_pools_query)
            vdi_curs.execute(controllers_query)
            controllers = vdi_curs.fetchall()
            for controller in controllers:
                # [0] = str_uuid
                # [1] = str_address (IP/domain_name)
                # [2] = str_jwt_token
                controllers_dict[controller[0]] = [controller[1], controller[2]]
    # получить данные о пуле ресурсов для каждого контроллера
    for controller in controllers_dict:
        controller_address = controllers_dict[controller][0]
        controller_token = controllers_dict[controller][1]
        async with VeilClient(server_address=controller_address, token=controller_token) as session:
            resource_pools = await session.resource_pool().list()
            for rp in resource_pools.data.get('results'):
                if 'default' in rp.get('verbose_name'):
                    controllers_dict[controller].append(rp.get('id'))
    # создать таблицу соответствия id контроллера и его пула ресурсов
    with db_connect(DSN) as vdi_conn:
        with vdi_conn.cursor() as vdi_curs:
            vdi_curs.execute(
                "create table if not exists public.tmp_controller (id uuid not null, resource_pool_id uuid not null);")
            for controller in controllers_dict:
                resource_pool_id = controllers_dict[controller][2]
                if resource_pool_id:
                    vdi_curs.execute("INSERT INTO public.tmp_controller (id, resource_pool_id) VALUES (%s, %s);",
                                     (controller, resource_pool_id))
            vdi_curs.execute(temporary_pools_query)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print('Done. Run pg_dump.')
