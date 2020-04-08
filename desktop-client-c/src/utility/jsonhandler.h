//
// Created by Solomin on 11.07.19.
//

#ifndef THIN_CLIENT_VEIL_JSONHANDLER_H
#define THIN_CLIENT_VEIL_JSONHANDLER_H

#include <json-glib/json-glib.h>

JsonObject *get_root_json_object(JsonParser *parser, const gchar *data);
//JsonArray *get_json_array(JsonParser *parser, const gchar *data);

gint64 json_object_get_int_member_safely(JsonObject  *object, const gchar *member_name);
const gchar *json_object_get_string_member_safely(JsonObject  *object,const gchar *member_name);
JsonObject *json_object_get_object_member_safely(JsonObject  *object, const gchar *member_name);

// Return data_object pointer or NULL if an error occured
// Every reply from VDI must contain errors or data
JsonObject *jsonhandler_get_data_object(JsonParser *parser, const gchar *json_str);

#endif //THIN_CLIENT_VEIL_JSONHANDLER_H
