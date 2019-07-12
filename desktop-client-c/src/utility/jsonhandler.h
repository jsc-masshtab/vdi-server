//
// Created by Solomin on 11.07.19.
//

#ifndef THIN_CLIENT_VEIL_JSONHANDLER_H
#define THIN_CLIENT_VEIL_JSONHANDLER_H

#include <json-glib/json-glib.h>

JsonObject *getJsonObject(JsonParser *parser, const gchar *data);
JsonArray *getJsonArray(JsonParser *parser, const gchar *data);

#endif //THIN_CLIENT_VEIL_JSONHANDLER_H
