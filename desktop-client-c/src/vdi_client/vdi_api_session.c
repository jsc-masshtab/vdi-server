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

static VdiSession vdiSession;

// Не предполагается одновременное выполнение больше одного запроса, поэтому защита полей VdiSession не реализуется
// get token  (make post request)
// set session header
// make api requests

static void free_session_memory(){

    free_memory_safely(&vdiSession.vdi_username);
    free_memory_safely(&vdiSession.vdi_password);
    free_memory_safely(&vdiSession.vdi_ip);
    free_memory_safely(&vdiSession.vdi_port);

    free_memory_safely(&vdiSession.api_url);
    free_memory_safely(&vdiSession.auth_url);
    free_memory_safely(&vdiSession.jwt);

    free_memory_safely(&vdiSession.current_vm_id);
}

static void setup_header_for_api_call(SoupMessage *msg)
{
    soup_message_headers_clear(msg->request_headers);
    gchar *authHeader = g_strdup_printf("jwt %s", vdiSession.jwt);
    //printf("%s %s\n", (const char *)__func__, authHeader);
    soup_message_headers_append(msg->request_headers, "Authorization", authHeader);
    g_free(authHeader);
    soup_message_headers_append(msg->request_headers, "Content-Type", "application/json");
}

static guint send_message(SoupMessage *msg)
{
    static int count = 0;
    printf("Send_count: %i\n", ++count);

    guint status = soup_session_send_message(vdiSession.soup_session, msg);
    printf("%s: Successfully sent \n", (const char *)__func__);
    return status;
}

// Получаем токен
static gboolean refresh_vdi_session_token()
{
    printf("%s\n", (const char *)__func__);

    if(vdiSession.auth_url == NULL)
        return FALSE;

    // clear token
    free_memory_safely(&vdiSession.jwt);

    // create request message
    SoupMessage *msg = soup_message_new("POST", vdiSession.auth_url);
    if(msg == NULL)
        return FALSE;

    // set header
    soup_message_headers_append(msg->request_headers, "Content-Type", "application/json");

    // set body
    gchar *messageBodyStr = g_strdup_printf("{\"username\": \"%s\", \"password\": \"%s\"}",
                                            vdiSession.vdi_username, vdiSession.vdi_password);
    soup_message_set_request(msg, "application/json",
                             SOUP_MEMORY_COPY, messageBodyStr, strlen (messageBodyStr));
    g_free(messageBodyStr);

    // send message
    send_message(msg);

    // parse response
    printf("msg->status_code %i\n", msg->status_code);
    printf("msg->response_body->data %s\n", msg->response_body->data);

    if(msg->status_code != OK_RESPONSE) {
        printf("%s : Unable to get token\n", (const char *)__func__);
        return FALSE;
    }

    JsonParser *parser = json_parser_new();
    JsonObject *root_object = get_root_json_object(parser, msg->response_body->data);
    if (!root_object)
        return FALSE;

    JsonObject *data_member_object = json_object_get_object_member(root_object, "data");
    if (!data_member_object)
        return FALSE;

    free_memory_safely(&vdiSession.jwt);
    vdiSession.jwt = g_strdup(json_object_get_string_member_safely (data_member_object, "access_token"));
    printf("new token: %s\n", vdiSession.jwt);

    g_object_unref(msg);
    g_object_unref (parser);

    return TRUE;
}

void start_vdi_session()
{
    if (vdiSession.is_active){
        printf("%s: Session is already active\n", (const char *)__func__);
        return;
    }
    // creae session
    vdiSession.soup_session = soup_session_new();

    vdiSession.vdi_username = NULL;
    vdiSession.vdi_password = NULL;
    vdiSession.vdi_ip = NULL;
    vdiSession.vdi_port = NULL;

    vdiSession.api_url = NULL;
    vdiSession.auth_url = NULL;
    vdiSession.jwt = NULL;

    vdiSession.is_active = TRUE;
    vdiSession.current_vm_id = NULL;
}

void stop_vdi_session()
{
    if (!vdiSession.is_active){
        printf("%s: Session is not active\n", (const char *)__func__);
        return;
    }

    cancell_pending_requests();
    g_object_unref(vdiSession.soup_session);

    free_session_memory();

    vdiSession.is_active = FALSE;
}

SoupSession *get_soup_session()
{
    return vdiSession.soup_session;
}

const gchar *get_vdi_ip()
{
    return vdiSession.vdi_ip;
}

void cancell_pending_requests()
{
    soup_session_abort(vdiSession.soup_session);
    // sleep to give the async tasks time to stop.
    // They will stop almost immediately after soup_session_abort
    g_usleep(20000);
}

void set_vdi_credentials(const gchar *username, const gchar *password, const gchar *ip, const gchar *port)
{
    free_session_memory();

    vdiSession.vdi_username = g_strdup(username);
    vdiSession.vdi_password = g_strdup(password);
    vdiSession.vdi_ip = g_strdup(ip);
    vdiSession.vdi_port = g_strdup(port);
    // /client/auth
//    // old
//    vdiSession.api_url = g_strdup_printf("http://%s", vdiSession.vdi_ip);
//    vdiSession.auth_url = g_strdup_printf("%s:%s/auth/", vdiSession.api_url, vdiSession.vdi_port);
    // new
    vdiSession.api_url = g_strdup_printf("http://%s:%s", vdiSession.vdi_ip, vdiSession.vdi_port);
    vdiSession.auth_url = g_strdup_printf("%s/auth/", vdiSession.api_url);

    vdiSession.jwt = NULL;
}

void set_current_vm_id(const gchar *current_vm_id)
{
    free_memory_safely(&vdiSession.current_vm_id);
    vdiSession.current_vm_id = g_strdup(current_vm_id);
}

const gchar *get_current_vm_id()
{
    return vdiSession.current_vm_id;
}

/*
void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer)
{
    memset(responseBuffer, 0, RESPONSE_BUFFER_SIZE);
    GError *error = NULL;
    g_input_stream_read (inputStream, responseBuffer, RESPONSE_BUFFER_SIZE, NULL, &error);
    responseBuffer[RESPONSE_BUFFER_SIZE - 1] = '\0'; // limit string for safety reasons
}*/

gchar *api_call(const char *method, const char *uri_string, const gchar *body_str)
{
    gchar *response_body_str = NULL;

    if (uri_string == NULL)
        return response_body_str;

    if (vdiSession.jwt == NULL) // get the token if we dont have it
        refresh_vdi_session_token();

    SoupMessage *msg = soup_message_new (method, uri_string);
    if (msg == NULL) // this may happen according to doc
        return response_body_str;

    // set header
    setup_header_for_api_call(msg);
    // set body
    if(body_str)
        soup_message_set_request (msg, "application/json",
                                  SOUP_MEMORY_COPY, body_str, strlen (body_str));

    // start attempts
    const int max_attempt_count = 2;
    for(int attempt_count = 0; attempt_count < max_attempt_count; attempt_count++) {
        // send request.
        send_message(msg);
        printf("HERE msg->status_code: %i\n", msg->status_code);

        // if response is ok then fill response_body_str
        if (msg->status_code == OK_RESPONSE ) { // we are happy now
            response_body_str = g_strdup(msg->response_body->data); // json_string_with_data. memory allocation!
            break;

        } else if (msg->status_code == AUTH_FAIL_RESPONSE) {
            refresh_vdi_session_token();
        }
    }

    g_object_unref(msg);

    return response_body_str;
}

void get_vdi_token(GTask       *task,
                 gpointer       source_object G_GNUC_UNUSED,
                 gpointer       task_data G_GNUC_UNUSED,
                 GCancellable  *cancellable G_GNUC_UNUSED)
{
    free_memory_safely(&vdiSession.jwt);
    gboolean token_refreshed = refresh_vdi_session_token();

    g_task_return_boolean(task, token_refreshed);
}

void get_vdi_pool_data(GTask   *task,
                 gpointer       source_object G_GNUC_UNUSED,
                 gpointer       task_data G_GNUC_UNUSED,
                 GCancellable  *cancellable G_GNUC_UNUSED)
{
    //printf("In %s :thread id = %lu\n", (const char *)__func__, pthread_self());
    gchar *urlStr = g_strdup_printf("%s/client/pools", vdiSession.api_url);
    gchar *response_body_str = api_call("GET", urlStr, NULL);
    g_free(urlStr);

    g_task_return_pointer(task, response_body_str, NULL); // return pointer must be freed
}

void get_vm_from_pool(GTask       *task,
                    gpointer       source_object G_GNUC_UNUSED,
                    gpointer       task_data G_GNUC_UNUSED,
                    GCancellable  *cancellable G_GNUC_UNUSED)
{
    gchar *urlStr = g_strdup_printf("%s/client/pools/%s", vdiSession.api_url, get_current_vm_id());
    gchar *response_body_str = api_call("POST", urlStr, NULL);
    g_free(urlStr);

    g_task_return_pointer(task, response_body_str, NULL); // return pointer must be freed
}

void do_action_on_vm(GTask      *task,
                  gpointer       source_object G_GNUC_UNUSED,
                  gpointer       task_data G_GNUC_UNUSED,
                  GCancellable  *cancellable G_GNUC_UNUSED)
{
    ActionOnVmData *action_on_vm_data = g_task_get_task_data(task);
    printf("%s: %s\n", (const char *)__func__, action_on_vm_data->action_on_vm_str);

    // url
    gchar *urlStr = g_strdup_printf("%s/client/pools/%s/%s", vdiSession.api_url,
            action_on_vm_data->current_vm_id, action_on_vm_data->action_on_vm_str);
    // body
    gchar *bodyStr;
    if(action_on_vm_data->is_action_forced)
        bodyStr = g_strdup_printf("{\"force\":true}");
    else
        bodyStr = g_strdup_printf("{\"force\":false}");

    gchar *response_body_str G_GNUC_UNUSED = api_call("POST", urlStr, bodyStr);

    // free url and body
    free_memory_safely(&urlStr);
    free_memory_safely(&bodyStr);
    // free ActionOnVmData
    free_memory_safely(&action_on_vm_data->current_vm_id);
    free_memory_safely(&action_on_vm_data->action_on_vm_str);
    free(action_on_vm_data);
}

void do_action_on_vm_async(const gchar *actionStr, gboolean isForced)
{
    ActionOnVmData *action_on_vm_data = malloc(sizeof(ActionOnVmData));
    action_on_vm_data->current_vm_id = g_strdup(get_current_vm_id());
    action_on_vm_data->action_on_vm_str = g_strdup(actionStr);
    action_on_vm_data->is_action_forced = isForced;

    execute_async_task(do_action_on_vm, NULL, action_on_vm_data);
}
