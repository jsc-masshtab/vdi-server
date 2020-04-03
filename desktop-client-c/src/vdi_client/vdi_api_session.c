//
// Created by solomin on 15.06.19.
//

#include <libsoup/soup-session.h>
#include "remote-viewer-util.h"
#include <json-glib/json-glib.h>

#include "vdi_api_session.h"
#include "jsonhandler.h"

//#define RESPONSE_BUFFER_SIZE 200
#define OK_RESPONSE 200
#define BAD_REQUEST 400
#define AUTH_FAIL_RESPONSE 401

static VdiSession vdiSession;

static const gchar *remote_protocol_to_str(VdiVmRemoteProtocol vm_remote_protocol)
{
    switch (vm_remote_protocol) {
    case VDI_SPICE_PROTOCOL:
        return "spice";
    case VDI_RDP_PROTOCOL:
        return "rdp";
    case VDI_ANOTHER_REMOTE_PROTOCOL:
        return "unknown_protocol";
    }
}

static void free_session_memory(){

    free_memory_safely(&vdiSession.vdi_username);
    free_memory_safely(&vdiSession.vdi_password);
    free_memory_safely(&vdiSession.vdi_ip);
    free_memory_safely(&vdiSession.vdi_port);

    free_memory_safely(&vdiSession.api_url);
    free_memory_safely(&vdiSession.auth_url);
    free_memory_safely(&vdiSession.jwt);

    free_memory_safely(&vdiSession.current_pool_id);
}

static void setup_header_for_api_call(SoupMessage *msg)
{
    soup_message_headers_clear(msg->request_headers);
    gchar *authHeader = g_strdup_printf("jwt %s", vdiSession.jwt);
    //printf("%s %s\n", (const char *)__func__, authHeader);
    soup_message_headers_append(msg->request_headers, "Authorization", authHeader);
    g_free(authHeader);
    soup_message_headers_append(msg->request_headers, "Content-Type", "application/json");
    soup_message_headers_append(msg->request_headers, "Client-Type", "thin-client");
}

static guint send_message(SoupMessage *msg)
{
    static int count = 0;
    printf("Send_count: %i\n", ++count);

    guint status = soup_session_send_message(vdiSession.soup_session, msg);
    printf("%s: Successfully sent. Response code: %i\n", (const char *)__func__, status);
    return status;
}

// Получаем токен
static gboolean refresh_vdi_session_token()
{
    printf("%s\n", (const char *)__func__);

    if(vdiSession.auth_url == NULL)
        return FALSE;

    // create request message
    SoupMessage *msg = soup_message_new("POST", vdiSession.auth_url);
    if(msg == NULL)
        return FALSE;

    // set header
    soup_message_headers_append(msg->request_headers, "Content-Type", "application/json");
    soup_message_headers_append(msg->request_headers, "Client-Type", "thin-client");

    // set body
    gchar *ldap_str = vdiSession.is_ldap ? g_strdup("true") : g_strdup("false");
    gchar *messageBodyStr = g_strdup_printf("{\"username\": \"%s\", \"password\": \"%s\", \"ldap\": %s}",
                                   vdiSession.vdi_username, vdiSession.vdi_password, ldap_str);
    printf("%s  messageBodyStr %s\n", (const char *)__func__, messageBodyStr);
    soup_message_set_request(msg, "application/json",
                             SOUP_MEMORY_COPY, messageBodyStr, strlen_safely(messageBodyStr));
    g_free(messageBodyStr);
    g_free(ldap_str);

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
    JsonObject *data_member_object = jsonhandler_get_data_object(parser, msg->response_body->data);

    if (!data_member_object) {
        g_object_unref(msg);
        g_object_unref (parser);
        return FALSE;
    }

    free_memory_safely(&vdiSession.jwt);
    vdiSession.jwt = g_strdup(json_object_get_string_member_safely (data_member_object, "access_token"));
    printf("new token: %s\n", vdiSession.jwt);

    g_object_unref(msg);
    g_object_unref (parser);
    return TRUE;
}

void start_vdi_session()
{
    memset(&vdiSession, 0, sizeof(VdiSession));

    // creae session
    vdiSession.soup_session = soup_session_new_with_options("timeout", HTTP_RESPONSE_TIOMEOUT, NULL);
    vdiSession.current_remote_protocol = VDI_SPICE_PROTOCOL; // by default
}

void stop_vdi_session()
{
    if (!vdiSession.is_active){
        printf("%s: Session is not active\n", (const char *)__func__);
        return;
    }

    // logout
    vdi_api_logout();

    vdi_api_cancell_pending_requests();
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

const gchar *get_vdi_port(void)
{
    return vdiSession.vdi_port;
}

const gchar *get_vdi_username(void)
{
    return vdiSession.vdi_username;
}

const gchar *get_vdi_password(void)
{
    return vdiSession.vdi_password;
}

void vdi_api_cancell_pending_requests()
{
    soup_session_abort(vdiSession.soup_session);
}

void set_vdi_credentials(const gchar *username, const gchar *password, const gchar *ip,
                         const gchar *port, gboolean is_ldap)
{
    free_session_memory();

    vdiSession.vdi_username = g_strdup(username);
    vdiSession.vdi_password = g_strdup(password);
    vdiSession.vdi_ip = g_strdup(ip);
    vdiSession.vdi_port = g_strdup(port);

    vdiSession.api_url = g_strdup_printf("http://%s:%s", vdiSession.vdi_ip, vdiSession.vdi_port);
    vdiSession.auth_url = g_strdup_printf("%s/auth/", vdiSession.api_url);

    vdiSession.is_ldap = is_ldap;
    vdiSession.jwt = NULL;
}

void set_current_pool_id(const gchar *current_pool_id)
{
    free_memory_safely(&vdiSession.current_pool_id);
    vdiSession.current_pool_id = g_strdup(current_pool_id);
}

const gchar *get_current_pool_id()
{
    return vdiSession.current_pool_id;
}

void set_current_remote_protocol(VdiVmRemoteProtocol remote_protocol)
{
    vdiSession.current_remote_protocol = remote_protocol;
}

VdiVmRemoteProtocol get_current_remote_protocol()
{
    return vdiSession.current_remote_protocol;
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

    SoupMessage *msg = soup_message_new(method, uri_string);
    if (msg == NULL) // this may happen according to doc
        return response_body_str;

    // set header
    setup_header_for_api_call(msg);
    // set body
    if(body_str)
        soup_message_set_request (msg, "application/json",
                                  SOUP_MEMORY_COPY, body_str, strlen_safely(body_str));

    // start attempts
    const int max_attempt_count = 2;
    for(int attempt_count = 0; attempt_count < max_attempt_count; attempt_count++) {
        // send request.
        send_message(msg);
        printf("msg->status_code: %i\n", msg->status_code);
        printf("msg->response_body: %s\n", msg->response_body->data);

        // if response is ok then fill response_body_str
        if (msg->status_code == OK_RESPONSE) { // we are happy now
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
    gchar *url_str = g_strdup_printf("%s/client/pools", vdiSession.api_url);
    gchar *response_body_str = api_call("GET", url_str, NULL);
    g_free(url_str);

    g_task_return_pointer(task, response_body_str, NULL); // return pointer must be freed
}

void get_vm_from_pool(GTask       *task,
                    gpointer       source_object G_GNUC_UNUSED,
                    gpointer       task_data G_GNUC_UNUSED,
                    GCancellable  *cancellable G_GNUC_UNUSED)
{
    gchar *url_str = g_strdup_printf("%s/client/pools/%s", vdiSession.api_url, vdiSession.current_pool_id);

    // todo: нормально создавать json
    gchar *bodyStr = g_strdup_printf("{\"remote_protocol\":\"%s\"}",
                                     remote_protocol_to_str(vdiSession.current_remote_protocol));

    gchar *response_body_str = api_call("POST", url_str, bodyStr);
    g_free(url_str);
    g_free(bodyStr);

    //response_body_str == NULL. didnt receive what we wanted
    if (!response_body_str) {
        g_task_return_pointer(task, NULL, NULL);
        return;
    }

    // parse response
    JsonParser *parser = json_parser_new();
    JsonObject *data_member_object = jsonhandler_get_data_object(parser, response_body_str);

    // no point to parse if data is invalid
    if (!data_member_object) {
        g_object_unref(parser);
        free_memory_safely(&response_body_str);
        g_task_return_pointer(task, NULL, NULL);
        return;
    }

    VdiVmData *vdi_vm_data = calloc(1, sizeof(VdiVmData));
    vdi_vm_data->vm_host = g_strdup(json_object_get_string_member_safely(data_member_object, "host"));
    vdi_vm_data->vm_port = json_object_get_int_member_safely(data_member_object, "port");
    vdi_vm_data->vm_password = g_strdup(json_object_get_string_member_safely(data_member_object, "password"));
    vdi_vm_data->message = g_strdup(json_object_get_string_member_safely(data_member_object, "message"));
    vdi_vm_data->vm_verbose_name = g_strdup(json_object_get_string_member_safely(data_member_object, "vm_verbose_name"));

    printf("vm_host %s \n", vdi_vm_data->vm_host);
    printf("vm_port %ld \n", vdi_vm_data->vm_port);
    printf("vm_password %s \n", vdi_vm_data->vm_password);
    printf("vm_verbose_name %s \n", vdi_vm_data->vm_verbose_name);

    g_object_unref(parser);
    g_task_return_pointer(task, vdi_vm_data, NULL); // return pointer must be freed
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
    free_action_on_vm_data(action_on_vm_data);
}

void vdi_api_session_connect_to_redis_and_subscribe(GTask         *task,
                                                    gpointer       source_object,
                                                    gpointer       task_data,
                                                    GCancellable  *cancellable)
{
    // do request to vdi server in order to get data fot Redis connection
    gchar *url_str = g_strdup_printf("%s/client/message_broker/", vdiSession.api_url);
    gchar *response_body_str = api_call("GET", url_str, NULL);
    printf("%s: response_body_str %s\n", (const char *)__func__, response_body_str);
    g_free(url_str);

    JsonParser *parser = json_parser_new();
    JsonObject *data_member_object = jsonhandler_get_data_object(parser, response_body_str);

    if (!data_member_object)
        return;

    // connect to Redis and subscribe to channel
}

gboolean vdi_api_logout(void)
{
    printf("%s \n", (const char *)__func__);
    if (vdiSession.jwt) {
        gchar *url_str = g_strdup_printf("%s/logout", vdiSession.api_url);

        SoupMessage *msg = soup_message_new("POST", url_str);
        g_free(url_str);

        if (msg == NULL) {
            printf("%s : Cant construct logout message\n", (const char *)__func__);
            return FALSE;

        } else {
            // set header
            setup_header_for_api_call(msg);
            // send
            g_object_set(vdiSession.soup_session, "timeout", 1, NULL);
            send_message(msg);
            g_object_set(vdiSession.soup_session, "timeout", HTTP_RESPONSE_TIOMEOUT, NULL);

            guint res_code = msg->status_code;
            g_object_unref(msg);

            if (res_code == OK_RESPONSE) {
                // logout was succesfull so we can foget the token
                free_memory_safely(&vdiSession.jwt);
                return TRUE;
            }
            else
                return FALSE;
        }

    } else {
        printf("%s : No token info\n", (const char *)__func__);
        return FALSE;
    }
}

void do_action_on_vm_launch_task(const gchar *actionStr, gboolean isForced)
{
    ActionOnVmData *action_on_vm_data = malloc(sizeof(ActionOnVmData));
    action_on_vm_data->current_vm_id = g_strdup(get_current_pool_id());
    action_on_vm_data->action_on_vm_str = g_strdup(actionStr);
    action_on_vm_data->is_action_forced = isForced;

    execute_async_task(do_action_on_vm, NULL, action_on_vm_data, NULL);
}

void free_action_on_vm_data(ActionOnVmData *action_on_vm_data)
{
    free_memory_safely(&action_on_vm_data->current_vm_id);
    free_memory_safely(&action_on_vm_data->action_on_vm_str);
    free(action_on_vm_data);
}

void free_vdi_vm_data(VdiVmData *vdi_vm_data)
{
    free_memory_safely(&vdi_vm_data->vm_host);
    free_memory_safely(&vdi_vm_data->vm_password);
    free_memory_safely(&vdi_vm_data->message);
    free_memory_safely(&vdi_vm_data->vm_verbose_name);
    free(vdi_vm_data);
}
