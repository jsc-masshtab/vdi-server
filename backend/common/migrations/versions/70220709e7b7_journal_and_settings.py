"""Journal_and_settings.

Revision ID: 70220709e7b7
Revises: 07972ddc0723
Create Date: 2022-01-20 14:13:12.125546

"""
import json
import uuid
from datetime import datetime

from alembic import op

import sqlalchemy as sa

from common.languages import _local_
from common.settings import DB_USER

# revision identifiers, used by Alembic.
revision = "70220709e7b7"
down_revision = "07972ddc0723"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table("settings",
                    sa.Column("settings", sa.JSON, nullable=True),
                    sa.Column("smtp_settings", sa.JSON, nullable=True))

    settings_dict = {"LANGUAGE": "ru",
                     "DEBUG": False,
                     "REDIS_EXPIRE_TIME": 600,
                     "VEIL_CACHE_TTL": 1,
                     "VEIL_CACHE_SERVER": "localhost",
                     "VEIL_CACHE_PORT": 11211,
                     "VEIL_REQUEST_TIMEOUT": 15,
                     "VEIL_CONNECTION_TIMEOUT": 15,
                     "VEIL_GUEST_AGENT_EXTRA_WAITING": 3,
                     "VEIL_OPERATION_WAITING": 10,
                     "VEIL_MAX_BODY_SIZE": 1000 * 1024 ^ 3,
                     "VEIL_MAX_CLIENTS": 10,
                     "VEIL_SSL_ON": False,
                     "VEIL_WS_MAX_TIME_TO_WAIT": 60,
                     "VEIL_VM_PREPARE_TIMEOUT": 1200.0,
                     "VEIL_MAX_URL_LEN": 6000,
                     "VEIL_MAX_IDS_LEN": 3780,
                     "VEIL_MAX_VM_CREATE_ATTEMPTS": 10
                     }
    settings_json = json.dumps(settings_dict)
    op.execute(
        """INSERT INTO public.settings (settings) VALUES ('{}')""".format(settings_json))

    smtp_dict = {"TLS": False,
                 "SSL": False,
                 "hostname": None,
                 "port": 25,
                 "password": None,
                 "user": None,
                 "from_address": None,
                 "level": 4
                 }
    smtp_json = json.dumps(smtp_dict)
    op.execute(
        """UPDATE public.settings SET smtp_settings = '{}'""".format(smtp_json))

    # Параметры журнала
    sql = """insert
                         into
                         public.journal_settings
                         (id, interval, period, form, duration, by_count, count, 
                         dir_path, ru_msg_str, ru_name_str, ru_path_str, en_msg_str, 
                         en_name_str, en_path_str, create_date)
                         values
                         ('{uuid}', '1 month', 'month', 'YYYY_MM', 36, FALSE, 1000, 
                         '/tmp/', 'Добавлен новый архив журнала.', 'Имя архива:', 'путь:', 
                         'Add new journal archive.', 'Archive name:', 'path:', '{date}');
                  """.format(
        uuid=uuid.uuid4(), date=datetime.now().date()
    )
    op.execute(sql)

    msg_str = _local_("Add new journal archive.")
    name_str = _local_("Archive name:")
    path_str = _local_("path:")

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
                                                            TO ''%s'' DELIMITER '','' CSV HEADER', count, index, count, full_path) into sql;
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
                                                   select format('COPY event_%s TO ''%s'' DELIMITER '','' CSV HEADER',
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
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("settings")
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
    # ### end Alembic commands ###
