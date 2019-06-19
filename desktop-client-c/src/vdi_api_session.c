//
// Created by solomin on 15.06.19.
//
// !!* -переменные с этой пометкой используются в разных потоках,
// но одновременный доступ к ним не предполагается, так что защита не нужна


#include <libsoup/soup-session.h>
#include "virt-viewer-util.h"
#include <json-glib/json-glib.h>

#include "vdi_api_session.h"

//#define RESPONSE_BUFFER_SIZE 200
#define OK_RESPONSE 200
#define AUTH_FAIL_RESPONSE 401

extern gchar *username_from_remote_dialog; // !!*
extern gchar *password_from_remote_dialog; // !!*
extern gchar *ip_from_remote_dialog;
extern gchar *port_from_remote_dialog;

static gchar *api_url = NULL;
static gchar *auth_url = NULL;
static gchar *jwt = NULL;

SoupSession *soupSession; // thread safe according to doc
gint64 currentVmId = -1; // !!*

// get token  (make post request)
// set session header
// make api requests

void startSession()
{
    soupSession = soup_session_new();

    free_memory_safely(&api_url);
    free_memory_safely(&auth_url);
    api_url = g_strdup_printf("http://%s", ip_from_remote_dialog);
    auth_url = g_strdup_printf("%s:%s/auth/", api_url, port_from_remote_dialog);
    currentVmId = -1;
}

void stopSession()
{
    cancellPendingRequests();
    g_object_unref(soupSession);

    free_memory_safely(&api_url);
    free_memory_safely(&auth_url);
    free_memory_safely(&jwt);
    currentVmId = -1;
}

void cancellPendingRequests()
{
    soup_session_abort (soupSession);
}

void setupHeaderForApiCall(SoupMessage *msg)
{
    soup_message_headers_clear (msg->request_headers);
    gchar *authHeader = g_strdup_printf("jwt %s", jwt);
    soup_message_headers_append (msg->request_headers, "Authorization", authHeader);
    g_free(authHeader);
    soup_message_headers_append (msg->request_headers, "Content-Type", "application/json; charset=utf8");
}

guint sendMessage(SoupMessage *msg)
{
    static int count = 0;
    printf("Send_count: %i\n", ++count);

    guint status = soup_session_send_message (soupSession, msg);
    printf("%s: Successfully sent \n", (char *)__func__);
    return status;
}


gboolean refreshVdiSessionToken()
{
    printf("%s\n", (char *)__func__);
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
    sendMessage(msg);

    // parse response
    printf("msg->status_code %i\n", msg->status_code);
    //printf("reason_phrase %s\n", msg->reason_phrase);
    //printf("responseBuffer %s\n", responseBuffer);

    if(msg->status_code != OK_RESPONSE) {
        printf("%s : Unable to get token\n", (char *)__func__);
        return FALSE;
    }

    JsonParser *parser = json_parser_new ();
    JsonObject *object = getJsonObject(parser, msg->response_body->data);
    if(object == NULL)
        return FALSE;

    jwt = g_strdup (json_object_get_string_member (object, "access_token"));
    printf("%s\n", jwt);

    g_object_unref(msg);
    g_object_unref (parser);

    return TRUE;
}

/*
void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer)
{
    memset(responseBuffer, 0, RESPONSE_BUFFER_SIZE);
    GError *error = NULL;
    g_input_stream_read (inputStream, responseBuffer, RESPONSE_BUFFER_SIZE, NULL, &error);
    responseBuffer[RESPONSE_BUFFER_SIZE - 1] = '\0'; // limit string for safety reasons
}*/

gchar * apiCall(const char *method, const char *uri_string)
{
    if(jwt == NULL)
        refreshVdiSessionToken();

    SoupMessage *msg = soup_message_new (method, uri_string);

    // header
    setupHeaderForApiCall(msg);

    // send request. first attempt
    sendMessage(msg);

    gchar *responseBodyStr = NULL;
    // check if token is bad and make the second attempt
    if(msg->status_code == AUTH_FAIL_RESPONSE) {
        refreshVdiSessionToken();
        setupHeaderForApiCall(msg);
        sendMessage(msg);
    }

    // if response is ok then fill responseBodyStr
    if(msg->status_code == OK_RESPONSE ) { // we are happy now
        responseBodyStr = g_strdup(msg->response_body->data); // json_string_with_data. memory allocation!
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
    //gint64 vmId = 0; // get it through parameters
    gchar *getVmUrl = g_strdup_printf("%s/client/pools/%i", api_url, currentVmId);
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

void executeAsyncTask(GTaskThreadFunc  task_func, GAsyncReadyCallback  callback, gpointer  callback_data)
{
    GTask *task = g_task_new (NULL, NULL, callback, callback_data);
    g_task_run_in_thread(task, task_func);
    g_object_unref (task);
}

