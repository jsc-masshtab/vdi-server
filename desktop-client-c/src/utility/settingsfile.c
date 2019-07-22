//
// Created by Solomin on 18.07.19.
//

#include "settingsfile.h"

static const gchar *ini_file_path = "veil_client_settings.ini";

gchar *
read_from_settings_file(const gchar *group_name,  const gchar *key)
{
    GError *error = NULL;
    gchar *str_value = NULL;;

    GKeyFile *keyfile = g_key_file_new ();

    if(!g_key_file_load_from_file(keyfile, ini_file_path,
                                  G_KEY_FILE_KEEP_COMMENTS |
                                  G_KEY_FILE_KEEP_TRANSLATIONS,
                                  &error))
    {
        g_debug("%s", error->message);
    }
    else
    {
        str_value = g_key_file_get_string(keyfile, group_name, key, &error);
    }

    g_key_file_free(keyfile);

    return str_value;
}


void
write_to_settings_file(const gchar *group_name,  const gchar *key, const gchar *str_value)
{
    if(str_value == NULL)
        return;

    GError *error = NULL;

    GKeyFile *keyfile = g_key_file_new ();

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

    g_key_file_save_to_file(keyfile, ini_file_path, &error);
    g_key_file_free(keyfile);
}