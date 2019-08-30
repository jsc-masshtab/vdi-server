#include <stdio.h>

#include <libsoup/soup-session.h>
#include <libsoup/soup-message.h>
#include <libsoup/soup-websocket.h>
#include <gio/gio.h>

#include "async.h"
#include "vdi_ws_client.h"

#define RECONNECT_TIMEOUT 1500

// static functions declarations
static void ws_message_received(SoupWebsocketConnection *self G_GNUC_UNUSED, gint type G_GNUC_UNUSED,
                                GBytes *message,  gpointer user_data);
static void ws_closed(SoupWebsocketConnection *self G_GNUC_UNUSED, gpointer user_data);
static void connection_attempt_resault(GObject *object, GAsyncResult *result, gpointer user_data);
static gboolean try_to_connect(VdiWsClient *vdi_ws_client);
static void try_to_connect_deffered(VdiWsClient *vdi_ws_client);
static void remove_recconect_timer(VdiWsClient *vdi_ws_client);
//void static async_create_ws_coonect(GTask         *task,
//                                    gpointer       source_object G_GNUC_UNUSED,
//                                    gpointer       task_data G_GNUC_UNUSED,
//                                    GCancellable  *cancellable G_GNUC_UNUSED);

// implementations

static void ws_message_received(SoupWebsocketConnection *self G_GNUC_UNUSED, gint type G_GNUC_UNUSED,
                                GBytes *message G_GNUC_UNUSED,  gpointer user_data)
{
    VdiWsClient *vdi_ws_client = user_data;
    //printf("%s %i\n", (char *)__func__, vdi_ws_client->test_int);
    vdi_ws_client->ws_data_received_callback(TRUE);
}

static void ws_closed(SoupWebsocketConnection *self G_GNUC_UNUSED, gpointer user_data)
{
    VdiWsClient *vdi_ws_client = user_data;
    printf("%s %i\n", (char *)__func__, vdi_ws_client->test_int);
    vdi_ws_client->ws_data_received_callback(FALSE);

    // if web socket is not closed correctly then try to reconnect
    if (!vdi_ws_client->is_correctly_closed_flag) {
        try_to_connect_deffered(vdi_ws_client);
    }
}

static void connection_attempt_resault(GObject *object, GAsyncResult *result, gpointer user_data)
{
//    GError *error = NULL;
//    VdiWsClient *vdi_ws_client = g_task_propagate_pointer(G_TASK(result), &error);
//    //printf("%s %i\n", (char *)__func__, vdi_ws_client->test_int);

//    printf("%s Before\n", (const char *)__func__);
//    //GTask *task = G_TASK(result);
//    //vdi_ws_client->soup_websocket_connection = g_task_propagate_pointer(G_TASK(result), &error);
//            //soup_session_websocket_connect_finish(SOUP_SESSION(object), result, &error);
//    printf("%s After\n", (const  char *)__func__);

//    // failed
//    if (vdi_ws_client->soup_websocket_connection == NULL) {
//        if (error)
//            printf("%s websocket error: %s\n", (char *)__func__, error->message);
//        vdi_ws_client->ws_data_received_callback(FALSE);

//        // try to reconnect
//        try_to_connect_deffered(vdi_ws_client);
//        return;
//    }
//    // success connection
//    // connect signals
//    g_signal_connect(vdi_ws_client->soup_websocket_connection, "message",
//                     G_CALLBACK(ws_message_received), user_data);
//    g_signal_connect(vdi_ws_client->soup_websocket_connection, "closed",
//                     G_CALLBACK(ws_closed), user_data);

    VdiWsClient *vdi_ws_client = user_data;
     //printf("%s %i\n", (char *)__func__, vdi_ws_client->test_int);
     GError *error = NULL;
     vdi_ws_client->soup_websocket_connection =
             soup_session_websocket_connect_finish(SOUP_SESSION (object), result, &error);

     // failed
     if (vdi_ws_client->soup_websocket_connection == NULL) {
         printf("%s websocket error: %s\n", (const char *)__func__, error->message);
         vdi_ws_client->ws_data_received_callback(FALSE);

         // try to reconnect
         try_to_connect_deffered(vdi_ws_client);
         return;
     }
     // success connection
     // connect signals
     g_signal_connect(vdi_ws_client->soup_websocket_connection, "message",
                      G_CALLBACK(ws_message_received), user_data);
     g_signal_connect(vdi_ws_client->soup_websocket_connection, "closed",
                      G_CALLBACK(ws_closed), user_data);
}

static gboolean try_to_connect(VdiWsClient *vdi_ws_client)
{
    remove_recconect_timer(vdi_ws_client);

    vdi_ws_client->is_correctly_closed_flag = FALSE;
    vdi_ws_client->soup_websocket_connection = NULL;
    SoupMessage *ws_msg = soup_message_new("GET", vdi_ws_client->vdi_url);
    if (ws_msg == NULL)
        return FALSE;

    soup_session_websocket_connect_async(vdi_ws_client->ws_soup_session, ws_msg,
                             NULL, NULL, NULL, connection_attempt_resault, vdi_ws_client);
    g_object_unref(ws_msg);
    //execute_async_task(async_create_ws_coonect, connection_attempt_resault, vdi_ws_client);

    return FALSE;
}

// one shot timeout. trying to connect
static void try_to_connect_deffered(VdiWsClient *vdi_ws_client)
{
    vdi_ws_client->reconnect_timer_descriptor =
            g_timeout_add(RECONNECT_TIMEOUT, (GSourceFunc)try_to_connect, vdi_ws_client);
}

static void remove_recconect_timer(VdiWsClient *vdi_ws_client)
{
    if(vdi_ws_client->reconnect_timer_descriptor > 0)
        g_source_remove(vdi_ws_client->reconnect_timer_descriptor);
    vdi_ws_client->reconnect_timer_descriptor = 0;
}

//void init_vdi_ws_client(VdiWsClient *ws_vdi_client)
//{

//}

//void deinit_vdi_ws_client(VdiWsClient *ws_vdi_client)
//{

//}

//void static async_create_ws_coonect(GTask         *task,
//                                    gpointer       source_object G_GNUC_UNUSED,
//                                    gpointer       task_data G_GNUC_UNUSED,
//                                    GCancellable  *cancellable G_GNUC_UNUSED)
//{
//    VdiWsClient *vdi_ws_client = g_task_get_task_data(task);

//    SoupMessage *ws_msg = soup_message_new("GET", vdi_ws_client->vdi_url);
//    printf("%s %s \n", (const char *)__func__, vdi_ws_client->vdi_url);

//    //soup_websocket_client_prepare_handshake(ws_msg, NULL, NULL);

//    //guint status = soup_session_send_message(vdi_ws_client->ws_soup_session, ws_msg);
//    //printf("%s: ws sent %i \n", (const char *)__func__, status);

////    GError *error = NULL;
////    gboolean handshake_res = soup_websocket_client_verify_handshake(ws_msg, &error);
////    printf("%s %i\n", (const char *)__func__, handshake_res);

////    GIOStream *stream = soup_session_steal_connection(vdi_ws_client->ws_soup_session, ws_msg);
////    g_socket_client_connect_to_host_finish
////    SoupWebsocketConnection *ws_connection = soup_websocket_connection_new(stream,
////                soup_message_get_uri(ws_msg), SOUP_WEBSOCKET_CONNECTION_CLIENT, NULL, NULL);

////    g_object_unref(ws_msg);
////    g_task_return_pointer(task, ws_connection, NULL);

//    GSocketClient *client = g_socket_client_new();

//    GSocketConnection *conn = g_socket_client_connect_to_host(client, "0.0.0.0", 80, NULL, NULL);
//    if (conn == NULL) {
//        printf("%s conn null \n", (const char *)__func__);
//    }

//    //uri = soup_uri_new ("http://127.0.0.1/");
//    vdi_ws_client->soup_websocket_connection = soup_websocket_connection_new (G_IO_STREAM (conn),
//                                                  soup_message_get_uri(ws_msg),
//                                                  SOUP_WEBSOCKET_CONNECTION_CLIENT,
//                                                  NULL, NULL);
//    if (vdi_ws_client->soup_websocket_connection == NULL) {
//        printf("%s ws conn null \n", (const char *)__func__);
//    }
//    //soup_uri_free (uri);
//    //g_object_unref (conn);

//    g_task_return_pointer(task, vdi_ws_client, NULL);
//}

void start_vdi_ws_polling(VdiWsClient *vdi_ws_client, const gchar *vdi_ip,
                          WsDataReceivedCallback ws_data_received_callback)
{
    printf("%s\n", (const char *)__func__);
    //vdi_ws_client->ws_soup_session = soup_session_new();

    vdi_ws_client->ws_data_received_callback = ws_data_received_callback;
    vdi_ws_client->reconnect_timer_descriptor = 0;
    //vdi_ws_client->test_int = 666;// temp trash test
    vdi_ws_client->vdi_url = g_strdup_printf ("ws://%s/ws/client/vdi_server_check", vdi_ip);

    // start reconnect oneshot timer
    try_to_connect(vdi_ws_client);
    g_usleep(100000); // remove later
}

void stop_vdi_ws_polling(VdiWsClient *vdi_ws_client)
{
    printf("%s\n", (const char *)__func__);
    remove_recconect_timer(vdi_ws_client);
    vdi_ws_client->is_correctly_closed_flag = TRUE;

    if (vdi_ws_client->soup_websocket_connection) {
        SoupWebsocketState soup_websocket_state =
                soup_websocket_connection_get_state(vdi_ws_client->soup_websocket_connection);
        if (soup_websocket_state == SOUP_WEBSOCKET_STATE_OPEN)
        soup_websocket_connection_close(vdi_ws_client->soup_websocket_connection, 0, NULL);
    }

    g_free(vdi_ws_client->vdi_url);

//    soup_session_abort(vdi_ws_client->ws_soup_session);
//    g_object_unref(vdi_ws_client->ws_soup_session);
}
