//
// Created by Solomin on 11.07.19.
//

#include "jsonhandler.h"

JsonObject *get_json_object(JsonParser *parser, const gchar *data)
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

JsonArray *get_json_array(JsonParser *parser, const gchar *data)
{
    gboolean result = json_parser_load_from_data (parser, data, -1, NULL);
    if(!result)
        return NULL;

    JsonNode *root = json_parser_get_root (parser);
    if(!JSON_NODE_HOLDS_ARRAY (root))
        return NULL;

    JsonArray *array = json_node_get_array (root);

    return array;
}