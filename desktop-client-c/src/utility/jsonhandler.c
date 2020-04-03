//
// Created by Solomin on 11.07.19.
//

#include <stdio.h>

#include "jsonhandler.h"

JsonObject *get_root_json_object(JsonParser *parser, const gchar *data)
{

    gboolean result = json_parser_load_from_data (parser, data, -1, NULL);
    if(!result)
        return NULL;

    JsonNode *root = json_parser_get_root (parser);
    if(!JSON_NODE_HOLDS_OBJECT (root))
        return NULL;

    JsonObject *object = json_node_get_object (root);
    return object;
}

gint64 json_object_get_int_member_safely(JsonObject *object, const gchar *member_name)
{
    if (json_object_has_member(object, member_name))
        return json_object_get_int_member(object, member_name);

    printf("json member '%s' does not exist \n", member_name);
    return 0;
}

const gchar *json_object_get_string_member_safely(JsonObject *object,const gchar *member_name)
{
    if (json_object_has_member(object, member_name))
        return json_object_get_string_member(object, member_name);

    printf("json member '%s' does not exist \n", member_name);
    return "";
}

JsonObject *json_object_get_object_member_safely(JsonObject *object, const gchar *member_name)
{
    if (json_object_has_member(object, member_name))
        return json_object_get_object_member(object, member_name);

    printf("json member '%s' does not exist \n", member_name);
    return NULL;
}

JsonObject *jsonhandler_get_data_object(JsonParser *parser, gchar *json_str)
{
    JsonObject *root_object = get_root_json_object(parser, json_str);
    if (!root_object)
        return NULL;

    // if response contains errors feild we consider request as a failure and dont parse the data
    if (json_object_has_member(root_object, "errors"))
        return NULL;

    JsonObject *data_member_object = json_object_get_object_member_safely(root_object, "data");
    return data_member_object;
}
