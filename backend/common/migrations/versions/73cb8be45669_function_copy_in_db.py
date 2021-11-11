"""Function_copy_in_db.

Revision ID: 73cb8be45669
Revises: 5052a0fc5eb0
Create Date: 2021-11-03 13:06:56.910421

"""
from alembic import op

from common.languages import _local_

# revision identifiers, used by Alembic.
revision = "73cb8be45669"
down_revision = "5052a0fc5eb0"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE journal_settings SET by_count = false WHERE by_count = true")

    msg_str = _local_("Add new journal archive.")
    name_str = _local_("Archive name:")
    path_str = _local_("path:")

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


def downgrade():
    msg_str = _local_("Add new journal archive.")
    name_str = _local_("Archive name:")
    path_str = _local_("path:")

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
