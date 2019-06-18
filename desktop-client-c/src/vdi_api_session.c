//
// Created by solomin on 15.06.19.
//
// https://developer.gnome.org/json-glib/stable/JsonParser.html
//// Allocates storage
//char *hello_world = (char*)malloc(13 * sizeof(char));
//// Prints "Hello world!" on hello_world
//sprintf(hello_world, "%s %s!", "Hello" "world");

#include <libsoup/soup-session.h>
#include "virt-viewer-util.h"
#include <json-glib/json-glib.h>

#include "vdi_api_session.h"

#define RESPONSE_BUFFER_SIZE 200

extern gchar *username_from_remote_dialog;
extern gchar *password_from_remote_dialog;
extern gchar *ip_from_remote_dialog;
extern gchar *port_from_remote_dialog;

static gchar *api_url = NULL;
static gchar *auth_url = NULL;
static gchar *jwt = NULL;

static SoupSession *soupSession = NULL; // thread safe

// create session
// get token  (make post request)
// set session header
// make api requests

void executeAsyncTask(GTaskThreadFunc  task_func, GAsyncReadyCallback  callback, gpointer  callback_data)
{

    GTask *task = g_task_new (NULL, NULL, callback, callback_data);
    g_task_run_in_thread(task, task_func);
    g_object_unref (task);
}

void startSession()
{
    soupSession = soup_session_new();

    free_memory_safely(&api_url);
    free_memory_safely(&auth_url);
    api_url = g_strdup_printf("http://%s", ip_from_remote_dialog);
    auth_url = g_strdup_printf("%s:%s/auth/", api_url, port_from_remote_dialog);
}

void configureSession(GTask         *task,
                      gpointer       source_object G_GNUC_UNUSED,
                      gpointer       task_data G_GNUC_UNUSED,
                      GCancellable  *cancellable G_GNUC_UNUSED)
{
    gboolean tokenReceived = refreshVdiSessionToken();

    g_task_return_boolean(task, tokenReceived);
}

void stopSession()
{
    // todo: required to cancel all pending requests...
    g_object_unref(soupSession);
    free_memory_safely(&api_url);
    free_memory_safely(&auth_url);
    free_memory_safely(&jwt);
}

void setupHeader(SoupMessage *msg)
{
    soup_message_headers_clear (msg->request_headers);
    gchar *authHeader = g_strdup_printf("jwt %s", jwt);
    soup_message_headers_append (msg->request_headers, "Authorization", authHeader);
    g_free(authHeader);
    soup_message_headers_append (msg->request_headers, "Content-Type", "application/json; charset=utf8");
}

gboolean refreshVdiSessionToken()
{
    printf("refreshVdiSessionToken\n");
    // clear token
    free_memory_safely(&jwt);

    // create request message
    SoupMessage *msg = soup_message_new ("POST", auth_url);

    gchar *messageBodyStr = g_strdup_printf("{\"username\": \"%s\", \"password\": \"%s\"}",
            username_from_remote_dialog, password_from_remote_dialog);

    soup_message_set_request (msg, "application/x-www-form-urlencoded",
                              SOUP_MEMORY_COPY, messageBodyStr, strlen (messageBodyStr));
    g_free(messageBodyStr);

    // send message
    GError *error = NULL;
    GInputStream *inputStream = soup_session_send (soupSession, msg, NULL, &error);

    gchar responseBuffer[RESPONSE_BUFFER_SIZE];
    gInputStreamToBuffer(inputStream, responseBuffer);

    // parse response
    printf("msg->status_code %i\n", msg->status_code);
    printf("reason_phrase %s\n", msg->reason_phrase);
    printf("responseBuffer %s\n", responseBuffer);

    if(msg->status_code != 200)
        return FALSE;

    JsonParser *parser = json_parser_new ();
    JsonObject *object = getJsonObject(parser, responseBuffer);
    if(object == NULL)
        return FALSE;

    jwt = g_strdup (json_object_get_string_member (object, "access_token"));

    g_object_unref(msg);
    g_object_unref (parser);

    printf("jwt: %s\n", jwt);
    return TRUE;
}

void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer)
{
    memset(responseBuffer, 0, RESPONSE_BUFFER_SIZE);
    GError *error = NULL;
    g_input_stream_read (inputStream, responseBuffer, RESPONSE_BUFFER_SIZE, NULL, &error);
    responseBuffer[RESPONSE_BUFFER_SIZE - 1] = '\0'; // limit string for safety reasons
}

gchar * apiCall(const char *method, const char *uri_string)
{
    if(jwt == NULL)
        refreshVdiSessionToken();

    SoupMessage *msg = soup_message_new (method, uri_string);

    // header
    setupHeader(msg);

    // send request. first attempt
    GError *error = NULL;
    GInputStream *inputStream = soup_session_send (soupSession, msg, NULL, &error);

    printf("apiCall: msg->status_code %i\n", msg->status_code);
    gchar *responseBodyStr = NULL;

    // check if token is bad and make the second attempt
    if(msg->status_code == 401) {
        refreshVdiSessionToken();
        setupHeader(msg);
        inputStream = soup_session_send(soupSession, msg, NULL, &error);
    }

    // if response is ok then fill responseBodyStr
    if(msg->status_code == 200) { // we are happy now
        gchar responseBuffer[RESPONSE_BUFFER_SIZE];
        gInputStreamToBuffer(inputStream, responseBuffer);

        responseBodyStr = g_strdup(responseBuffer); // json_string_with_data. memory allocation!
    }

    g_object_unref(msg);

    return responseBodyStr;
}

void getVdiVmData(GTask         *task,
                 gpointer       source_object G_GNUC_UNUSED,
                 gpointer       task_data G_GNUC_UNUSED,
                 GCancellable  *cancellable G_GNUC_UNUSED)
{

    gchar *getVmUrl = g_strdup_printf("%s/client/pools", api_url);
    gchar *responseBodyStr = apiCall("GET", getVmUrl);
    g_free(getVmUrl);

    g_task_return_pointer(task, responseBodyStr, NULL); // return pointer must be freed
}

void getVmDFromPool(GTask         *task,
                    gpointer       source_object G_GNUC_UNUSED,
                    gpointer       task_data G_GNUC_UNUSED,
                    GCancellable  *cancellable G_GNUC_UNUSED)
{
    gint64 vmId = 0; // get it through parameters
    gchar *getVmUrl = g_strdup_printf("%s/client/pools/%i", api_url, vmId);
    gchar *responseBodyStr = apiCall("POST", getVmUrl);
    g_free(getVmUrl);

    g_task_return_pointer(task, responseBodyStr, NULL); // return pointer must be freed
}

// json
JsonObject * getJsonObject(JsonParser *parser, const gchar *data)
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

JsonArray * getJsonArray(JsonParser *parser, const gchar *data)
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