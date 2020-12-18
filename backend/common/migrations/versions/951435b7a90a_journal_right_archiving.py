"""Journal_right_archiving

Revision ID: 951435b7a90a
Revises: 40932ab2f84c
Create Date: 2020-11-27 17:01:17.721309

"""
import uuid
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from common.languages import lang_init


_ = lang_init()

# revision identifiers, used by Alembic.
revision = '951435b7a90a'
down_revision = '969d9b36df65'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('journal_settings',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('interval', sa.Unicode(length=128), nullable=False),
                    sa.Column('period', sa.Unicode(length=128), nullable=False),
                    sa.Column('form', sa.Unicode(length=128), nullable=False),
                    sa.Column('duration', sa.Integer(), nullable=False),
                    sa.Column('by_count', sa.Boolean(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=False),
                    sa.Column('dir_path', sa.Unicode(length=1000), nullable=False),
                    sa.Column('create_date', sa.DateTime(timezone=True), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('interval'),
                    sa.UniqueConstraint('period'),
                    sa.UniqueConstraint('form'),
                    sa.UniqueConstraint('duration'),
                    sa.UniqueConstraint('by_count'),
                    sa.UniqueConstraint('count'),
                    sa.UniqueConstraint('dir_path'),
                    sa.UniqueConstraint('create_date')
                    )
    sql = """insert
                 into
                 public.journal_settings
                 (id, interval, period, form, duration, by_count, count, dir_path, create_date)
                 values
                 ('{uuid}', '1 month', 'month', 'YYYY_MM', 36, FALSE, 1000, '/tmp/', '{date}');
          """.format(uuid=uuid.uuid4(), date=datetime.now().date())
    op.execute(sql)

    msg_str = _('Add new journal archive.')
    name_str = _('Archive name:')
    path_str = _('path:')

    op.execute("""DO $BODY$
                    BEGIN
                        BEGIN
                            IF (EXISTS(select public.archived('2020-01-01', 1))) THEN
                                DROP FUNCTION archived(partition_date timestamp, index int);
                            END IF;
                        EXCEPTION WHEN others THEN
                            RAISE NOTICE 'NO SUCH FUNCTION';
                        END;
                    END
                  $BODY$""")

    # Архивирование предыдущих N записей (формат csv)
    op.execute("""CREATE OR REPLACE FUNCTION archived(partition_date timestamp)
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
                            LANGUAGE plpgsql;""".format(message=msg_str, name_str=name_str, path_str=path_str))

    # Вставка данных в дочернюю таблицу
    op.execute("""CREATE OR REPLACE FUNCTION insert_row()
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
                        LANGUAGE plpgsql;""")

    # Создание новой таблицы, наследованной от основной таблицы event
    op.execute("""CREATE OR REPLACE FUNCTION create_new_partition(partition_date timestamp, partition_name text)
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
                        LANGUAGE plpgsql;""")

    # Удаление данных из таблицы спустя 3 года
    op.execute("""CREATE OR REPLACE FUNCTION delete_partition()
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
                        LANGUAGE plpgsql;""")
    # ### end Alembic commands ###


def downgrade():
    msg_str = _('Add new journal archive.')
    name_str = _('Archive name:')
    path_str = _('path:')

    # Архивирование предыдущих записей (формат csv) через месяц
    op.execute("""CREATE OR REPLACE FUNCTION archived(partition_date timestamp)
                            RETURNS VOID AS
                            $BODY$
                            DECLARE
                              part TEXT;
                              path TEXT;
                              sql TEXT;
                              entity_id uuid = uuid_generate_v4();
                              event_id uuid = uuid_generate_v4();
                            BEGIN
                              part := format('event_%s', to_char(partition_date - interval '{intrvl}', '{form}'));
                              path := format('{dir}%s.csv', part);
                              IF (EXISTS (SELECT *
                                            FROM INFORMATION_SCHEMA.TABLES
                                            WHERE TABLE_SCHEMA = 'public'
                                            AND TABLE_NAME = part)) THEN
                                 BEGIN
                                   select format('COPY (SELECT * from event_%s) TO ''%s'' With HEADER CSV',
                                          to_char(partition_date - interval '{intrvl}', '{form}'), path) into sql;
                                   EXECUTE sql;
                                   select format('INSERT INTO entity (id, entity_type, entity_uuid) VALUES
                                                 (''%s'', ''SECURITY'', NULL)', entity_id) into sql;
                                   EXECUTE sql;
                                   select format('INSERT INTO event
                                                 (id, event_type, message, description, "user", entity_id)
                                                 VALUES (''%s'', 0, ''{message}'',
                                                 ''{name_str} %s, {path_str} {dir}'', ''system'', ''%s'')',
                                                 event_id, part, entity_id) into sql;
                                   EXECUTE sql;
                                 END;
                              END IF;
                            END;
                            $BODY$
                            LANGUAGE plpgsql;""".format(intrvl='1 month', form='YYYY_MM', dir='/tmp/', message=msg_str,
                                                        name_str=name_str, path_str=path_str))

    # Вставка данных в дочернюю таблицу по месячному периоду
    op.execute("""CREATE OR REPLACE FUNCTION insert_row()
                        RETURNS TRIGGER AS
                        $BODY$
                        DECLARE
                          partition_date TIMESTAMP;
                          partition_name TEXT;
                          sql TEXT;
                        BEGIN
                          partition_date := date_trunc('{period}', NEW.created AT TIME ZONE 'UTC');
                          partition_name := format('event_%s', to_char(partition_date, '{form}'));
                          IF NOT EXISTS(SELECT relname FROM pg_class WHERE relname = partition_name) THEN
                                PERFORM create_new_partition(partition_date, partition_name);
                                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                                PERFORM archived(partition_date);
                          END IF;
                          select format('INSERT INTO %s values ($1.*)', partition_name) into sql;
                          EXECUTE sql USING NEW;
                          return NEW;
                        END;
                        $BODY$
                        LANGUAGE plpgsql;""".format(period='month', form='YYYY_MM'))

    # Создание новой таблицы, дочерней от event по месяцу
    op.execute("""CREATE OR REPLACE FUNCTION create_new_partition(partition_date timestamp, partition_name text)
                        RETURNS VOID AS
                        $BODY$
                        DECLARE
                          sql TEXT;
                        BEGIN
                          select format('CREATE TABLE IF NOT EXISTS %s (CHECK (
                                  created AT TIME ZONE ''UTC'' > ''%s'' AND
                                  created AT TIME ZONE ''UTC'' <= ''%s''))
                                  INHERITS (event)', partition_name, partition_date,
                                        partition_date + interval '{intrvl}') into sql;
                          EXECUTE sql;
                          PERFORM index_partition(partition_name);
                        END;
                        $BODY$
                        LANGUAGE plpgsql;""".format(intrvl='1 month'))

    # Функция удаления данных из таблицы спустя 3 года
    op.execute("""CREATE OR REPLACE FUNCTION delete_partition()
                        RETURNS TRIGGER AS
                        $BODY$
                        DECLARE
                          part TEXT;
                          sql TEXT;
                        BEGIN
                          IF (CURRENT_DATE >= '{create}'::date + {duration} * interval '{intrvl}') THEN
                            part := format('event_%s', to_char(CURRENT_DATE - {duration} * interval '{intrvl}', '{form}'));
                            IF (EXISTS (SELECT *
                                 FROM INFORMATION_SCHEMA.TABLES
                                 WHERE TABLE_SCHEMA = 'public'
                                 AND TABLE_NAME = part)) THEN
                                   BEGIN
                                     select format('DROP TABLE event_%s',
                                       to_char(CURRENT_DATE - {duration} * interval '{intrvl}', '{form}')) into sql;
                                     EXECUTE sql;
                                   END;
                            END IF;
                          END IF;
                          return null;
                        END;
                        $BODY$
                        LANGUAGE plpgsql;""".format(create='2020-08-01', duration=36, intrvl='1 month', form='YYYY_MM'))

    op.drop_table('journal_settings')
    # ### end Alembic commands ###
