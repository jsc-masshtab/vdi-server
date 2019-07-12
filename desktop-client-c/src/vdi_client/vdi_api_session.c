//
// Created by solomin on 15.06.19.
//
// !!* -переменные с этой пометкой используются в разных потоках,
// но одновременный доступ к ним не предполагается, так что защита не нужна

#include <libsoup/soup-session.h>
#include "virt-viewer-util.h"
#include <json-glib/json-glib.h>

#include "vdi_api_session.h"
#include "jsonhandler.h"

//#define RESPONSE_BUFFER_SIZE 200
#define OK_RESPONSE 200
#define BAD_REQUEST 400
#define AUTH_FAIL_RESPONSE 401
#define VM_ID_UNKNOWN -1

static gchar *vdi_username = NULL; // !!*
static gchar *vdi_password = NULL; // !!*
static gchar *vdi_ip = NULL;
static gchar *vdi_port = NULL;

static VdiSession vdiSession;


// get token  (make post request)
// set session header
// make api requests

void setVdiCredentials(const gchar *username, const gchar *password, const gchar *ip, const gchar *port)
{
    free_memory_safely(&vdi_username);
    vdi_username = g_strdup(username);

    free_memory_safely(&vdi_password);
    vdi_password = g_strdup(password);

    free_memory_safely(&vdi_ip);
    vdi_ip = g_strdup(ip);

    free_memory_safely(&vdi_port);
    vdi_port = g_strdup(port);
}

void startSession()
{
    vdiSession.soupSession = soup_session_new();

    vdiSession.api_url = g_strdup_printf("http://%s", vdi_ip);
    vdiSession.auth_url = g_strdup_printf("%s:%s/auth/", vdiSession.api_url, vdi_port);
    vdiSession.jwt = NULL;
}

void stopSession()
{
    cancellPendingRequests();
    // sleep to give the async tasks time to stop.
    // They will stop almost immediately after cancellPendingRequests
    g_usleep(20000);
    g_object_unref(vdiSession.soupSession);

    free_memory_safely(&vdiSession.api_url);
    free_memory_safely(&vdiSession.auth_url);
    free_memory_safely(&vdiSession.jwt);
}

void cancellPendingRequests()
{
    soup_session_abort(vdiSession.soupSession);
}

void setupHeaderForApiCall(SoupMessage *msg)
{
    soup_message_headers_clear (msg->request_headers);
    gchar *authHeader = g_strdup_printf("jwt %s", vdiSession.jwt);
    soup_message_headers_append (msg->request_headers, "Authorization", authHeader);
    g_free(authHeader);
    soup_message_headers_append (msg->request_headers, "Content-Type", "application/json; charset=utf8");
}

guint sendMessage(SoupMessage *msg)
{
    static int count = 0;
    printf("Send_count: %i\n", ++count);

    guint status = soup_session_send_message (vdiSession.soupSession, msg);
    printf("%s: Successfully sent \n", (char *)__func__);
    return status;
}

gboolean refreshVdiSessionToken()
{
    printf("%s\n", (char *)__func__);
    // clear token
    free_memory_safely(&vdiSession.jwt);

    // create request message
    SoupMessage *msg = soup_message_new ("POST", vdiSession.auth_url);
    if(msg == NULL)
        return FALSE;

    gchar *messageBodyStr = g_strdup_printf("{\"username\": \"%s\", \"password\": \"%s\"}",
            vdi_username, vdi_password);

    soup_message_set_request (msg, "application/x-www-form-urlencoded",
                              SOUP_MEMORY_COPY, messageBodyStr, strlen (messageBodyStr));
    g_free(messageBodyStr);

    // send message
    sendMessage(msg);

    // parse response
    printf("msg->status_code %i\n", msg->status_code);

    if(msg->status_code != OK_RESPONSE) {
        printf("%s : Unable to get token\n", (char *)__func__);
        return FALSE;
    }

    JsonParser *parser = json_parser_new ();
    JsonObject *object = getJsonObject(parser, msg->response_body->data);
    if(object == NULL)
        return FALSE;

    vdiSession.jwt = g_strdup (json_object_get_string_member (object, "access_token"));
    printf("%s\n", vdiSession.jwt);

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

gchar *apiCall(const char *method, const char *uri_string, const gchar *body_str)
{
    if(vdiSession.jwt == NULL) // get the token if we dont have it
        refreshVdiSessionToken();

    gchar *responseBodyStr = NULL;

    SoupMessage *msg = soup_message_new (method, uri_string);
    if(msg == NULL) // this may happen according to doc
        return responseBodyStr;

    // set header
    setupHeaderForApiCall(msg);
    // set body
    if(body_str)
        soup_message_set_request (msg, "application/x-www-form-urlencoded",
                                  SOUP_MEMORY_COPY, body_str, strlen (body_str));

    // start attempts
    int attemptCount = 0;
    const int maxAttemptCount = 2;
    do{
        // if an attempt is not the first we refresh the token and hope it would help us!
        if(attemptCount != 0)
            refreshVdiSessionToken();
        // send request.
        sendMessage(msg);
        printf("HERE msg->status_code: %i\n", msg->status_code);
        attemptCount++;

    } while (msg->status_code != OK_RESPONSE && attemptCount < maxAttemptCount);

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

    gchar *urlStr = g_strdup_printf("%s/client/pools", vdiSession.api_url);
    gchar *responseBodyStr = apiCall("GET", urlStr, NULL);
    g_free(urlStr);

    g_task_return_pointer(task, responseBodyStr, NULL); // return pointer must be freed
}

void getVmDFromPool(GTask         *task,
                    gpointer       source_object G_GNUC_UNUSED,
                    gpointer       task_data G_GNUC_UNUSED,
                    GCancellable  *cancellable G_GNUC_UNUSED)
{
    gint64 *currentVmIdPtr = g_task_get_task_data(task);

    gchar *urlStr = g_strdup_printf("%s/client/pools/%ld", vdiSession.api_url, *currentVmIdPtr);
    gchar *responseBodyStr = apiCall("POST", urlStr, NULL);
    g_free(urlStr);

    free(currentVmIdPtr);

    g_task_return_pointer(task, responseBodyStr, NULL); // return pointer must be freed
}

void doActionOnVm(GTask         *task,
                  gpointer       source_object G_GNUC_UNUSED,
                  gpointer       task_data G_GNUC_UNUSED,
                  GCancellable  *cancellable G_GNUC_UNUSED)
{
    ActionOnVmData *actionOnVmData = g_task_get_task_data(task);
    printf("%s: %s\n", (char *)__func__, actionOnVmData->actionOnVmStr);

    // url
    gchar *urlStr = g_strdup_printf("%s/client/pools/%ld/%s", vdiSession.api_url,
            actionOnVmData->currentVmId, actionOnVmData->actionOnVmStr);
    // body
    gchar *bodyStr;
    if(actionOnVmData->isActionForced)
        bodyStr = g_strdup_printf("{\"force\":true}");
    else
        bodyStr = g_strdup_printf("{\"force\":false}");

    gchar *responseBodyStr = apiCall("POST", urlStr, bodyStr);
    (void)responseBodyStr;
    // free url and body
    g_free(urlStr);
    g_free(bodyStr);
    // free ActionOnVmData
    g_free(actionOnVmData->actionOnVmStr);
    free(actionOnVmData);
}

void executeAsyncTask(GTaskThreadFunc task_func, GAsyncReadyCallback callback, gpointer task_data)
{
    GTask *task = g_task_new(NULL, NULL, callback, NULL);
    if(task_data)
        g_task_set_task_data(task, task_data, NULL);
    g_task_run_in_thread(task, task_func);
    g_object_unref (task);
}
