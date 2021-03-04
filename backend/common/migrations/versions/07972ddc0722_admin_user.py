"""Admin user.

Revision ID: 07972ddc0722
Revises: b58c521ba8d4
Create Date: 2021-02-19 18:36:34.395333

"""
from alembic import op

from common.veil.auth.hashers import make_password
from common.settings import DB_USER, SECRET_KEY
from common.languages import lang_init

import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "07972ddc0722"
down_revision = "b58c521ba8d4"
branch_labels = None
depends_on = None
_ = lang_init()


def upgrade():
    # Уникальный хэш для установки
    hashed_password = make_password(password="Bazalt1!", salt=SECRET_KEY)
    # Создаем пользователя аналогично пользователю из установки
    sql = """insert
                 into
                 public."user" (id, username, password, is_active, is_superuser)
                 values (
                    'f9599771-cc95-45e5-9ae5-c8177b796aff',
                    'vdiadmin',
                    '{}',
                    true,
                    true);""".format(
        hashed_password
    )
    op.execute(sql)
    # Параметры журнала
    sql = """insert
                     into
                     public.journal_settings
                     (id, interval, period, form, duration, by_count, count, dir_path, create_date)
                     values
                     ('{uuid}', '1 month', 'month', 'YYYY_MM', 36, FALSE, 1000, '/tmp/', '{date}');
              """.format(
        uuid=uuid.uuid4(), date=datetime.now().date()
    )
    op.execute(sql)
    # объединенные миграции журнала
    msg_str = _("Add new journal archive.")
    name_str = _("Archive name:")
    path_str = _("path:")

    # Архивирование предыдущих N записей (формат csv)
    op.execute(
        """CREATE OR REPLACE FUNCTION archived(partition_date timestamp)
                            RETURNS VOID AS
                            $BODY$
                            DECLARE
                              by_count BOOLEAN;
                              part_interval INTERVAL;
                              part_form TEXT;
                              path TEXT;
                              count INTEGER;
                              part TEXT;
                              full_path TEXT;
                              index INTEGER;
                              sql TEXT;
                              entity_id uuid = uuid_generate_v4();
                              event_id uuid = uuid_generate_v4();
                            BEGIN
                              EXECUTE 'SELECT by_count FROM journal_settings' into by_count;
                              IF by_count IS TRUE THEN
                                            BEGIN
                                              EXECUTE 'SELECT dir_path FROM journal_settings' into path;
                                              EXECUTE 'SELECT count FROM journal_settings' into count;
                                              EXECUTE 'SELECT COUNT(*) FROM event' into index;
                                              part := format('event_%s', index);
                                              full_path := format('%s%s.csv', path, part);
                                              select format('COPY (SELECT * from event LIMIT %s OFFSET (%s - %s))
                                                            TO ''%s'' With HEADER CSV', count, index, count, full_path) into sql;
                                              EXECUTE sql;
                                              select format('INSERT INTO entity (id, entity_type, entity_uuid) VALUES
                                                            (''%s'', ''SECURITY'', NULL)', entity_id) into sql;
                                              EXECUTE sql;
                                              select format('INSERT INTO event (id, event_type, message, description, "user", entity_id)
                                                            VALUES (''%s'', 0, ''{message}'',
                                                            ''{name_str} %s, {path_str} %s'', ''system'', ''%s'')',
                                                            event_id, part, path, entity_id) into sql;
                                              EXECUTE sql;
                                            EXCEPTION
                                                WHEN undefined_file OR insufficient_privilege THEN
                                                  select format('INSERT INTO entity (id, entity_type, entity_uuid) VALUES
                                                                (''%s'', ''SECURITY'', NULL)', entity_id) into sql;
                                                  EXECUTE sql;
                                                  select format('INSERT INTO event (id, event_type, message, description, "user", entity_id)
                                                                VALUES (''%s'', 2, ''Error archiving of journal: Permission denied.'',
                                                                ''%s'', ''system'', ''%s'')',
                                                                event_id, SQLERRM, entity_id) into sql;
                                                  EXECUTE sql;
                                            END;
                              ELSE
                                            BEGIN
                                              EXECUTE 'SELECT interval FROM journal_settings' into part_interval;
                                              EXECUTE 'SELECT form FROM journal_settings' into part_form;
                                              EXECUTE 'SELECT dir_path FROM journal_settings' into path;
                                              part := format('event_%s', to_char(partition_date - part_interval, part_form));
                                              full_path := format('%s%s.csv', path, part);
                                              IF (EXISTS (SELECT *
                                                            FROM INFORMATION_SCHEMA.TABLES
                                                            WHERE TABLE_SCHEMA = 'public'
                                                            AND TABLE_NAME = part)) THEN
                                                 BEGIN
                                                   select format('COPY (SELECT * from event_%s) TO ''%s'' With HEADER CSV',
                                                          to_char(partition_date - part_interval, part_form), full_path) into sql;
                                                   EXECUTE sql;
                                                   select format('INSERT INTO entity (id, entity_type, entity_uuid) VALUES
                                                                 (''%s'', ''SECURITY'', NULL)', entity_id) into sql;
                                                   EXECUTE sql;
                                                   select format('INSERT INTO event (id, event_type, message, description, "user", entity_id)
                                                            VALUES (''%s'', 0, ''{message}'',
                                                            ''{name_str} %s, {path_str} %s'', ''system'', ''%s'')',
                                                            event_id, part, path, entity_id) into sql;
                                                   EXECUTE sql;
                                                 END;
                                              END IF;
                                            EXCEPTION
                                                WHEN undefined_file OR insufficient_privilege THEN
                                                  select format('INSERT INTO entity (id, entity_type, entity_uuid) VALUES
                                                                (''%s'', ''SECURITY'', NULL)', entity_id) into sql;
                                                  EXECUTE sql;
                                                  select format('INSERT INTO event (id, event_type, message, description, "user", entity_id)
                                                                VALUES (''%s'', 2, ''Error archiving of journal: Permission denied.'',
                                                                ''%s'', ''system'', ''%s'')',
                                                                event_id, SQLERRM, entity_id) into sql;
                                                  EXECUTE sql;
                                            END;
                              END IF;
                            END;
                            $BODY$
                            LANGUAGE plpgsql;""".format(
            message=msg_str, name_str=name_str, path_str=path_str
        )
    )

    # Вставка данных в дочернюю таблицу
    op.execute(
        """CREATE OR REPLACE FUNCTION insert_row()
                            RETURNS TRIGGER AS
                            $BODY$
                            DECLARE
                              index INTEGER;
                              period TEXT;
                              form TEXT;
                              count INTEGER;
                              by_count BOOLEAN;
                              partition_date TIMESTAMP;
                              partition_name TEXT;
                              sql TEXT;
                            BEGIN
                              EXECUTE 'SELECT period FROM journal_settings' into period;
                              EXECUTE 'SELECT form FROM journal_settings' into form;
                              EXECUTE 'SELECT count FROM journal_settings' into count;
                              EXECUTE 'SELECT by_count FROM journal_settings' into by_count;
                              IF by_count IS TRUE THEN
                                  BEGIN
                                      partition_date := date_trunc(period, NEW.created AT TIME ZONE 'UTC');
                                      partition_name := format('event_%s', to_char(partition_date, form));
                                      -- Если нет такой таблицы, то создается новая
                                      IF NOT EXISTS(SELECT relname FROM pg_class WHERE relname = partition_name) THEN
                                            PERFORM create_new_partition(partition_date, partition_name);
                                            select format('ALTER TABLE %s OWNER TO {db_user}', partition_name) into sql;
                                            EXECUTE sql;
                                      END IF;
                                      select format('INSERT INTO %s values ($1.*)', partition_name) into sql;
                                      EXECUTE sql USING NEW;
                                      EXECUTE 'SELECT COUNT(*) FROM event' into index;
                                      IF (index % count = 0) THEN
                                        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                                        PERFORM archived(partition_date);
                                      END IF;
                                      return NEW;
                                  END;
                              ELSE
                                  BEGIN
                                      partition_date := date_trunc(period, NEW.created AT TIME ZONE 'UTC');
                                      partition_name := format('event_%s', to_char(partition_date, form));
                                      IF NOT EXISTS(SELECT relname FROM pg_class WHERE relname = partition_name) THEN
                                            PERFORM create_new_partition(partition_date, partition_name);
                                            select format('ALTER TABLE %s OWNER TO {db_user}', partition_name) into sql;
                                            EXECUTE sql;
                                            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                                            PERFORM archived(partition_date);
                                      END IF;
                                      select format('INSERT INTO %s values ($1.*)', partition_name) into sql;
                                      EXECUTE sql USING NEW;
                                      return NEW;
                                  END;
                              END IF;
                            END;
                            $BODY$
                            LANGUAGE plpgsql;""".format(
            db_user=DB_USER
        )
    )

    # Создание новой таблицы, наследованной от основной таблицы event
    op.execute(
        """CREATE OR REPLACE FUNCTION create_new_partition(partition_date timestamp, partition_name text)
                        RETURNS VOID AS
                        $BODY$
                        DECLARE
                          part_interval INTERVAL;
                          sql TEXT;
                        BEGIN
                          EXECUTE 'SELECT interval FROM journal_settings' into part_interval;
                          select format('CREATE TABLE IF NOT EXISTS %s (CHECK (
                                  created AT TIME ZONE ''UTC'' > ''%s'' AND
                                  created AT TIME ZONE ''UTC'' <= ''%s''))
                                  INHERITS (event)', partition_name, partition_date,
                                        partition_date + part_interval) into sql;
                          EXECUTE sql;
                          PERFORM index_partition(partition_name);
                        END;
                        $BODY$
                        LANGUAGE plpgsql;"""
    )

    op.execute(
        """CREATE OR REPLACE FUNCTION index_partition(partition_name text)
                    RETURNS VOID AS
                    $BODY$
                    -- индекс по дате создания события
                    BEGIN
                        EXECUTE 'CREATE INDEX IF NOT EXISTS ' || partition_name || '_idx ON ' || partition_name || ' (timezone(''UTC''::text, created))';
                    END;
                    $BODY$
                    LANGUAGE plpgsql;"""
    )

    op.execute(
        """CREATE TRIGGER before_insert_row_trigger
                    BEFORE INSERT ON event
                    FOR EACH ROW EXECUTE PROCEDURE insert_row();"""
    )

    op.execute(
        """CREATE OR REPLACE FUNCTION delete_parent_row()
                    RETURNS TRIGGER AS
                    $BODY$
                    -- удаление дублирующихся записей в родительской таблице
                    BEGIN
                        delete from only event where id = NEW.id;
                        RETURN null;
                    END;
                    $BODY$
                    LANGUAGE plpgsql;"""
    )

    op.execute(
        """CREATE TRIGGER after_insert_row_trigger
                    AFTER INSERT ON event
                    FOR EACH ROW EXECUTE PROCEDURE delete_parent_row();"""
    )

    # Удаление данных из таблицы спустя 3 года
    op.execute(
        """CREATE OR REPLACE FUNCTION delete_partition()
                        RETURNS TRIGGER AS
                        $BODY$
                        DECLARE
                          part TEXT;
                          part_interval INTERVAL;
                          part_form TEXT;
                          part_duration INTEGER;
                          create_date TIMESTAMP;
                          sql TEXT;
                        BEGIN
                          EXECUTE 'SELECT interval FROM journal_settings' into part_interval;
                          EXECUTE 'SELECT form FROM journal_settings' into part_form;
                          EXECUTE 'SELECT duration FROM journal_settings' into part_duration;
                          EXECUTE 'SELECT create_date FROM journal_settings' into create_date;
                          IF (CURRENT_DATE >= create_date::date + part_duration * part_interval) THEN
                            part := format('event_%s', to_char(CURRENT_DATE - part_duration * part_interval, part_form));
                            IF (EXISTS (SELECT *
                                 FROM INFORMATION_SCHEMA.TABLES
                                 WHERE TABLE_SCHEMA = 'public'
                                 AND TABLE_NAME = part)) THEN
                                   BEGIN
                                     select format('DROP TABLE event_%s',
                                       to_char(CURRENT_DATE - part_duration * part_interval, part_form)) into sql;
                                     EXECUTE sql;
                                   END;
                            END IF;
                          END IF;
                          return null;
                        END;
                        $BODY$
                        LANGUAGE plpgsql;"""
    )

    op.execute(
        """CREATE TRIGGER after_insert_row_for_delete_partition_trigger
                    AFTER INSERT ON event
                    FOR EACH ROW EXECUTE PROCEDURE delete_partition();"""
    )


def downgrade():
    op.execute(
        """DROP TRIGGER after_insert_row_for_delete_partition_trigger ON event"""
    )
    op.execute("""DROP FUNCTION delete_partition()""")
    op.execute("""DROP TRIGGER after_insert_row_trigger ON event""")
    op.execute("""DROP FUNCTION delete_parent_row()""")
    op.execute("""DROP TRIGGER before_insert_row_trigger ON event""")
    op.execute("""DROP FUNCTION index_partition(partition_name text)""")
    op.execute(
        """DROP FUNCTION create_new_partition(partition_date timestamp, partition_name text)"""
    )
    op.execute("""DROP FUNCTION archived(partition_date timestamp)""")
    op.execute("""DROP FUNCTION insert_row()""")
    op.execute(
        "delete from public.user where id = 'f9599771-cc95-45e5-9ae5-c8177b796aff';"
    )
