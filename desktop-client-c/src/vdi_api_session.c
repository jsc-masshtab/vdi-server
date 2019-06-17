//
// Created by solomin on 15.06.19.
//
// https://developer.gnome.org/json-glib/stable/JsonParser.html
//// Allocates storage
//char *hello_world = (char*)malloc(13 * sizeof(char));
//// Prints "Hello world!" on hello_world
//sprintf(hello_world, "%s %s!", "Hello" "world");

#include <libsoup/soup-session.h>

#include "vdi_api_session.h"

static SoupSession *soupSession; // thread safe

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

    SoupMessage *msg = soup_message_new ("POST", "https://www.gismeteo.ru");

    GInputStream *stream;
    GError *error = NULL;

    stream = soup_session_send (soupSession, msg, NULL, &error);

    printf("%i", msg->status_code); printf("\n");
    printf(msg->reason_phrase); printf("\n");
    printf(msg->response_body->data); printf("\n");

    g_object_unref(msg);

    const gchar *jwt = "";
    return jwt;
}

void getVdiVmData(GTask         *task,
                 gpointer       source_object,
                 gpointer       task_data,
                 GCancellable  *cancellable)
{

    // get token
    const gchar *jwtToken = getVdiSessionToken();

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

    //! move to callback
    /*
    GArray *garray;
    gint i;
    const guint numberOfVm = 1;

    garray = g_array_sized_new  (FALSE, TRUE, sizeof (VdiVmData), numberOfVm);
    for (i = 0; i < numberOfVm; i++) {
        VdiVmData vdiVmData;
        vdiVmData.osType = VDI_VM_LINUX;
        vdiVmData.testData = i;
        g_array_append_val (garray, vdiVmData);
    }

    for (i = 0; i < numberOfVm; i++) {
        VdiVmData vdiVmData = g_array_index (garray, VdiVmData, i);
        printf("%i", vdiVmData.testData);
        printf("\n");
    }

    //g_array_free (garray, TRUE);
    //return garray;
     */

    gchar *testStr = g_strdup("test_str");

    g_task_return_pointer(task, testStr, NULL);
}