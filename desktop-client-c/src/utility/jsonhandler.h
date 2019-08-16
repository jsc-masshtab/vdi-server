//
// Created by Solomin on 11.07.19.
//

#ifndef THIN_CLIENT_VEIL_JSONHANDLER_H
#define THIN_CLIENT_VEIL_JSONHANDLER_H

#include <json-glib/json-glib.h>

JsonObject *get_json_object(JsonParser *parser, const gchar *data);
JsonArray *get_json_array(JsonParser *parser, const gchar *data);
gint64 json_object_get_int_member_safely(JsonObject  *object, const gchar *member_name);
const gchar *json_object_get_string_member_safely(JsonObject  *object,const gchar *member_name);

#endif //THIN_CLIENT_VEIL_JSONHANDLER_H
