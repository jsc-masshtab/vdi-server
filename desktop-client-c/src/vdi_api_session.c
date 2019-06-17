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

#include "vdi_api_session.h"

extern gchar *username_from_remote_dialog;
extern gchar *password_from_remote_dialog;
extern gchar *ip_from_remote_dialog;
extern gchar *port_from_remote_dialog;

gchar *api_url = NULL;
gchar *auth_url = NULL;

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
    printf("\n");
}

void stopSession()
{
    // todo: required to cancel all pending requests...

    g_object_unref(soupSession);
}

void configureSession()
{
    const gchar *jwtToken = getVdiSessionToken();
}

const gchar *getVdiSessionToken()
{
    printf("getVdiSessionToken\n");
    //printf("getVdiSessionToken thread %i \n", g_thread_self());

    SoupMessage *msg = soup_message_new ("POST", auth_url);

    gchar *messageBody = g_strdup_printf("{\"username\": \"%s\", \"password\": \"%s\"}",
            username_from_remote_dialog, password_from_remote_dialog);
    // set data   // data = '{"username": "%s", "password": "%s"}' % (self.username, self.password)
    soup_message_set_request (msg, "application/x-www-form-urlencoded",
                              SOUP_MEMORY_COPY, messageBody, strlen (messageBody));
    g_free(messageBody);

    GError *error = NULL;
    GInputStream *stream = soup_session_send (soupSession, msg, NULL, &error);

    printf("msg->status_code %i\n", msg->status_code);
    printf("reason_phrase %s\n", msg->reason_phrase);
    //printf("response_body %s\n", msg->response_body->data);

    g_object_unref(msg);

    const gchar *jwt = NULL;
    return jwt;
}

void getVdiVmData(GTask         *task,
                 gpointer       source_object,
                 gpointer       task_data,
                 GCancellable  *cancellable) {

    // get token
    const gchar *jwtToken = getVdiSessionToken();

    // check if token received
    //if (jwtToken == NULL) {
    //    gchar *failStr = g_strdup("Fail");
    //    g_task_return_pointer(task, failStr, NULL);
    //}

    // construct msg
    SoupMessage *msg = soup_message_new ("POST", "https://www.gismeteo.ru");
    gchar *authHeader = g_strdup_printf("jwt %s", jwtToken); // "jwt {}".format(self._get_token
    soup_message_headers_append (msg->request_headers, "Authorization", authHeader);
    g_free(authHeader);
    soup_message_headers_append (msg->request_headers, "Content-Type", "application/json; charset=utf8");

    // send post request to get Vdi Vm Data
    GInputStream *stream;
    GError *error = NULL;
    stream = soup_session_send (soupSession, msg, NULL, &error);

    // parse json response



    gchar *testStr = g_strdup("fail"); // json_string_with_vm_data
    g_task_return_pointer(task, testStr, NULL);
}