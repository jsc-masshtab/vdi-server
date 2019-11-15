#include <stdio.h>
#include <pthread.h>

#include <libsoup/soup-session.h>
#include <libsoup/soup-message.h>
#include <libsoup/soup-websocket.h>
#include <gio/gio.h>

#include "async.h"
#include "vdi_ws_client.h"

#define TIMEOUT 500000 // 1 sec
#define WS_READ_TIMEOUT 200000

// static functions declarations
void static async_create_ws_connect(GTask         *task,
                                    gpointer       source_object G_GNUC_UNUSED,
                                    gpointer       task_data G_GNUC_UNUSED,
                                    GCancellable  *cancellable G_GNUC_UNUSED);

// implementations

static void protocol_switching_callback(SoupMessage *ws_msg, gpointer user_data)
{

    printf("In %s :thread id = %lu\n", (const char *)__func__, pthread_self());
    VdiWsClient *vdi_ws_client = user_data;

    printf("WS: %s %i\n", (const char *)__func__, vdi_ws_client->test_int);
    vdi_ws_client->stream = soup_session_steal_connection(vdi_ws_client->ws_soup_session, ws_msg);
}

static void async_create_ws_connect(GTask         *task G_GNUC_UNUSED,
                                    gpointer       source_object G_GNUC_UNUSED,
                                    gpointer       task_data,
                                    GCancellable  *cancellable G_GNUC_UNUSED)
{
    VdiWsClient *vdi_ws_client = task_data;
    g_mutex_lock(&vdi_ws_client->lock);

    // hand shake preparation
    SoupMessage *ws_msg = soup_message_new("GET", vdi_ws_client->vdi_url);
    if (ws_msg == NULL) {
        printf("%s Cant parse message\n", (const char *)__func__);
        g_mutex_unlock(&vdi_ws_client->lock);
        return;
    }
    soup_websocket_client_prepare_handshake(ws_msg, NULL, NULL);
    soup_message_headers_replace(ws_msg->request_headers, "Connection", "keep-alive, Upgrade");

    soup_message_add_status_code_handler(ws_msg, "got-informational",
                          SOUP_STATUS_SWITCHING_PROTOCOLS,
                          G_CALLBACK (protocol_switching_callback), vdi_ws_client);

    while (vdi_ws_client->is_running) {
        vdi_ws_client->stream = NULL;

        // make handshake
        guint status = soup_session_send_message(vdi_ws_client->ws_soup_session, ws_msg);

        if (vdi_ws_client->stream == NULL) {
            g_idle_add((GSourceFunc)vdi_ws_client->ws_data_received_callback, (gpointer)FALSE); // notify GUI
            // try to reconnect (go to another loop)
            cancellable_sleep(TIMEOUT, !vdi_ws_client->is_running);
            continue;
        } else {
            printf("WS: %s: SUCCESSFUL HANDSHAKE %i \n", (const char *)__func__, status);
            g_idle_add((GSourceFunc)vdi_ws_client->ws_data_received_callback, (gpointer)TRUE);
        }

        GInputStream *inputStream = g_io_stream_get_input_stream(vdi_ws_client->stream);

        enum { buf_length = 2 };
        gchar buffer[buf_length];
        gsize bytes_read = 0;

        const guint8 max_read_try = 3; // maximum amount of read tries
        guint8 read_try_count = 0; // read try counter

        // receiving messages
        while (vdi_ws_client->is_running && !g_io_stream_is_closed(vdi_ws_client->stream)) {
            GError *error = NULL;
            gboolean res = g_input_stream_read_all(inputStream,
                                                   &buffer,
                                                   buf_length, &bytes_read,
                                                   vdi_ws_client->cancel_job, &error);
//            if (error) {
//                printf("WS: %i", error->code);
//                printf("WS: %s ", error->message);
//                //break; // try to reconnect (another loop)
//            }

            printf("WS: %s res: %i bytes_read: %lu\n", (const char *)__func__, res, bytes_read);

            if (bytes_read == 0) {
                read_try_count ++;

                if (read_try_count == max_read_try) {
                    g_idle_add((GSourceFunc)vdi_ws_client->ws_data_received_callback, (gpointer)FALSE); // notify GUI
                    break; // try to reconnect (another loop)
                }
            } else { // successfull read
                read_try_count = 0;
                g_idle_add((GSourceFunc)vdi_ws_client->ws_data_received_callback, (gpointer)TRUE); // notify GUI
            }
            cancellable_sleep(WS_READ_TIMEOUT, !vdi_ws_client->is_running); // sec
        }

        //free(buffer);

        // close stream
        if (vdi_ws_client->stream)
            g_io_stream_close(vdi_ws_client->stream, NULL, NULL);
    }

    g_mutex_unlock(&vdi_ws_client->lock);
}

void start_vdi_ws_polling(VdiWsClient *vdi_ws_client, const gchar *vdi_ip, const gchar *vdi_port,
                          WsDataReceivedCallback ws_data_received_callback)
{
    printf("%s\n", (const char *)__func__);
    printf("In %s :thread id = %lu\n", (const char *)__func__, pthread_self());
    vdi_ws_client->ws_soup_session = soup_session_new_with_options("idle-timeout", 0, "timeout", 0, NULL);

    vdi_ws_client->ws_data_received_callback = ws_data_received_callback;
    vdi_ws_client->test_int = 666;// temp trash test
    vdi_ws_client->vdi_url = g_strdup_printf("http://%s:%s/ws/client/vdi_server_check", vdi_ip, vdi_port);
    vdi_ws_client->is_running = TRUE;
    vdi_ws_client->cancel_job = g_cancellable_new();

    g_mutex_init(&vdi_ws_client->lock);

    execute_async_task(async_create_ws_connect, NULL, vdi_ws_client, NULL);
}

void stop_vdi_ws_polling(VdiWsClient *vdi_ws_client)
{
    printf("%s\n", (const char *)__func__);

    // cancell
    vdi_ws_client->is_running = FALSE;
    g_cancellable_cancel(vdi_ws_client->cancel_job);
    soup_session_abort(vdi_ws_client->ws_soup_session);

    // for syncronization. wait untill thread ws job finished. Is there a better solution? (like event primitive)
    g_mutex_lock(&vdi_ws_client->lock);
    g_mutex_unlock(&vdi_ws_client->lock);
    g_mutex_clear(&vdi_ws_client->lock);

    // free memory
    g_object_unref(vdi_ws_client->ws_soup_session);
    g_free(vdi_ws_client->vdi_url);
    g_object_unref(vdi_ws_client->cancel_job);
}
