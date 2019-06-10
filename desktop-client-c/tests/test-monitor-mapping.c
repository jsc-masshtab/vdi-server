/* -*- Mode: C; c-basic-offset: 4; indent-tabs-mode: nil -*- */
/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2016 Red Hat, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
 */

#include <config.h>
#include <glib.h>
#include <virt-viewer-util.h>

gboolean doDebug = FALSE;

/**
 * is_valid_monitor_mapping:
 * @mapping: a value for the "monitor-mapping" key
 *
 * Tests the validity of the settings file for the "monitor-mapping" key:
 *  [test-monitor-mapping]
 *  monitor-mapping=@mapping
 *
 * Returns: %TRUE if the mapping is valid
 */
static gboolean
is_valid_monitor_mapping(const gchar *mapping, gint nmonitors)
{
    GKeyFile *key_file;
    gboolean valid;
    const gchar *group_name = "test-monitor-mapping";
    const gchar *key = "monitor-mapping";
    const gchar *key_data_fmt = "[%s]\n%s=%s\n";
    gchar *key_data = g_strdup_printf(key_data_fmt, group_name, key, mapping);

    key_file = g_key_file_new();
    valid = g_key_file_load_from_data(key_file, key_data, -1, G_KEY_FILE_NONE, NULL);
    if (valid) {
        gsize nmappings;
        gchar **mappings = g_key_file_get_string_list(key_file, group_name, key, &nmappings, NULL);
        GHashTable *map = virt_viewer_parse_monitor_mappings(mappings, nmappings, nmonitors);

        valid = (map != NULL);

        g_strfreev(mappings);
        g_clear_pointer(&map, g_hash_table_unref);
    }

    g_key_file_free(key_file);
    g_free(key_data);
    return valid;
}

int main(void)
{
    /* valid monitor mappings */
    g_assert_true(is_valid_monitor_mapping("1:1", 4));
    g_assert_true(is_valid_monitor_mapping("1:1;2:2", 4));
    g_assert_true(is_valid_monitor_mapping("1:1;2:2;3:3;", 4));
    g_assert_true(is_valid_monitor_mapping("1:2;2:1;3:3;4:4", 4));
    g_assert_true(is_valid_monitor_mapping("4:1;3:2;2:3;1:4", 4));

    /* invalid monitors mappings */
    /* zero ids */
    g_assert_false(is_valid_monitor_mapping("0:0", 4));
    /* negative guest display id */
    g_assert_false(is_valid_monitor_mapping("-1:1", 4));
    /* negative client monitor id */
    g_assert_false(is_valid_monitor_mapping("1:-1", 4));
    /* negative guest display & client monitor id */
    g_assert_false(is_valid_monitor_mapping("-1:-1", 4));
    /* high guest display id */
    g_assert_false(is_valid_monitor_mapping("100:1", 4));
    /* high client monitor id */
    g_assert_false(is_valid_monitor_mapping("1:100", 4));
    /* missing guest display id */
    g_assert_false(is_valid_monitor_mapping("1:1;3:3", 4));
    /* guest display id used twice */
    g_assert_false(is_valid_monitor_mapping("1:1;1:2", 4));
    /* client monitor id used twice */
    g_assert_false(is_valid_monitor_mapping("1:1;2:1", 4));
    /* floating point guest display id */
    g_assert_false(is_valid_monitor_mapping("1.111:1", 4));
    /* floating point client monitor id */
    g_assert_false(is_valid_monitor_mapping("1:1.111", 4));
    /* empty mapping */
    g_assert_false(is_valid_monitor_mapping("", 4));
    g_assert_false(is_valid_monitor_mapping(";", 4));
    /* missing guest display id */
    g_assert_false(is_valid_monitor_mapping(":1", 4));
    /* missing client monitor id */
    g_assert_false(is_valid_monitor_mapping("1:", 4));
    /* missing guest display & client monitor id */
    g_assert_false(is_valid_monitor_mapping(":", 4));
    /*missing colon */
    g_assert_false(is_valid_monitor_mapping("11", 4));
    /*missing semicolon */
    g_assert_false(is_valid_monitor_mapping("1:12:2", 4));
    /* strings */
    g_assert_false(is_valid_monitor_mapping("1:a", 4));
    g_assert_false(is_valid_monitor_mapping("a:1", 4));
    g_assert_false(is_valid_monitor_mapping("a:a", 4));
    g_assert_false(is_valid_monitor_mapping("monitor mapping", 4));

    /* not enough available monitors */
    g_assert_false(is_valid_monitor_mapping("1:1;2:2", 1));
    g_assert_false(is_valid_monitor_mapping("1:1;2:2;3:3;", 2));
    g_assert_false(is_valid_monitor_mapping("1:2;2:1;3:3;4:4", 3));

    /* nmonitors==0 should not be a valid argument */
    g_assert_false(is_valid_monitor_mapping("1:1", 0));

    return 0;
}
