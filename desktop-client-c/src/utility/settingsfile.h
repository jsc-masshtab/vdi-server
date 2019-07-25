//
// Created by Solomin on 18.07.19.
//

#ifndef THIN_CLIENT_VEIL_SETTINGSFILE_H
#define THIN_CLIENT_VEIL_SETTINGSFILE_H

#include <gtk/gtk.h>
#include <config.h>
#include <gdk/gdkkeysyms.h>
#include <glib/gtypes.h>


gchar *read_from_settings_file(const gchar *group_name,  const gchar *key);
void write_to_settings_file(const gchar *group_name,  const gchar *key, const gchar *str_value);

#endif //THIN_CLIENT_VEIL_SETTINGSFILE_H
