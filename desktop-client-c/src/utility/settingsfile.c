//
// Created by Solomin on 18.07.19.
//

#include "settingsfile.h"

static const gchar *ini_file_path = "veil_client_settings.ini";

const gchar *
get_ini_file_name()
{
    return ini_file_path;
}

// Это конечно не оптимально открывать файл каждый раз чтоб записать или получить одно значение.
// Но потери производительности не существенны, зато существенно облегчение работы с ini.
/// str
gchar *
read_str_from_ini_file(const gchar *group_name,  const gchar *key)
{
    GError *error = NULL;
    gchar *str_value = NULL;

    GKeyFile *keyfile = g_key_file_new();

    if(!g_key_file_load_from_file(keyfile, ini_file_path,
                                  G_KEY_FILE_KEEP_COMMENTS |
                                  G_KEY_FILE_KEEP_TRANSLATIONS,
                                  &error))
    {
        g_debug("%s", error->message);
    }
    else
    {
        str_value = g_key_file_get_string(keyfile, group_name, key, NULL);
    }

    g_clear_error(&error);
    g_key_file_free(keyfile);

    return str_value;
}


void
write_str_to_ini_file(const gchar *group_name,  const gchar *key, const gchar *str_value)
{
    if(str_value == NULL)
        return;

    GError *error = NULL;

    GKeyFile *keyfile = g_key_file_new();

    if(!g_key_file_load_from_file(keyfile, ini_file_path,
                                  G_KEY_FILE_KEEP_COMMENTS |
                                  G_KEY_FILE_KEEP_TRANSLATIONS,
                                  &error))
    {
        g_debug("%s", error->message);
    }
    else
    {
        g_key_file_set_value(keyfile, group_name, key, str_value);
    }

    g_clear_error(&error);
    g_key_file_save_to_file(keyfile, ini_file_path, NULL);
    g_key_file_free(keyfile);
}

///integer
gint
read_int_from_ini_file(const gchar *group_name,  const gchar *key)
{
    GError *error = NULL;
    gint value = 0;
    GKeyFile *keyfile = g_key_file_new();

    if(!g_key_file_load_from_file(keyfile, ini_file_path,
                                  G_KEY_FILE_KEEP_COMMENTS |
                                  G_KEY_FILE_KEEP_TRANSLATIONS,
                                  &error))
    {
        g_debug("%s", error->message);
    }
    else
    {
        value = g_key_file_get_integer(keyfile, group_name, key, &error);
    }

    g_key_file_free(keyfile);

    return value;
}


void
write_int_to_ini_file(const gchar *group_name,  const gchar *key, gint value)
{
    GError *error = NULL;
    GKeyFile *keyfile = g_key_file_new();

    if(!g_key_file_load_from_file(keyfile, ini_file_path,
                                  G_KEY_FILE_KEEP_COMMENTS |
                                  G_KEY_FILE_KEEP_TRANSLATIONS,
                                  &error))
    {
        g_debug("%s", error->message);
    }
    else
    {
        g_key_file_set_integer(keyfile, group_name, key, value);
    }

    g_clear_error(&error);
    g_key_file_save_to_file(keyfile, ini_file_path, NULL);
    g_key_file_free(keyfile);
}
