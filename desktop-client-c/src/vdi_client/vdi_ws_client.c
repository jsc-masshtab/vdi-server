#include <stdio.h>

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


// implementations

static void ws_message_received(SoupWebsocketConnection *self G_GNUC_UNUSED, gint type G_GNUC_UNUSED,
                                GBytes *message,  gpointer user_data)
{
    VdiWsClient *vdi_ws_client = user_data;
    printf("%s %i\n", (char *)__func__, vdi_ws_client->test_int);
    vdi_ws_client->ws_data_received_callback(message);
}

static void ws_closed(SoupWebsocketConnection *self G_GNUC_UNUSED, gpointer user_data)
{
    VdiWsClient *vdi_ws_client = user_data;
    printf("%s %i\n", (char *)__func__, vdi_ws_client->test_int);

    // if web socket is not closed correctly then try to reconnect
    if(!vdi_ws_client->is_correctly_closed_flag) {
        try_to_connect_deffered(vdi_ws_client);
    }
}

static void connection_attempt_resault(GObject *object, GAsyncResult *result, gpointer user_data)
{
    VdiWsClient *vdi_ws_client = user_data;
    printf("%s %i\n", (char *)__func__, vdi_ws_client->test_int);
    GError *error = NULL;
    vdi_ws_client->soup_websocket_connection =
            soup_session_websocket_connect_finish(SOUP_SESSION (object), result, &error);

    if (vdi_ws_client->soup_websocket_connection == NULL) {
        printf("%s websocket error: %s\n", (char *)__func__, error->message);

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

    printf("%s\n", (char *)__func__);
    if (vdi_ws_client->ws_msg == NULL)
        return FALSE;

    vdi_ws_client->is_correctly_closed_flag = FALSE;
    vdi_ws_client->soup_websocket_connection = NULL;
    soup_session_websocket_connect_async(vdi_ws_client->soup_session, vdi_ws_client->ws_msg,
                             NULL, NULL, NULL, connection_attempt_resault, vdi_ws_client);

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

void start_vdi_ws_polling(VdiWsClient *vdi_ws_client, const gchar *vdi_ip,
                          WsDataReceivedCallback ws_data_received_callback)
{
    vdi_ws_client->ws_data_received_callback = ws_data_received_callback;
    vdi_ws_client->reconnect_timer_descriptor = 0;
    vdi_ws_client->test_int = 666;// temp trash test

    gchar *url = g_strdup_printf ("ws://%s/ws/client/vdi_server_check", vdi_ip);
    vdi_ws_client->ws_msg = soup_message_new("GET", url);
    g_free (url);
    if (vdi_ws_client->ws_msg == NULL)
        return;

    // start reconnect oneshot timer
    try_to_connect(vdi_ws_client);
}

void stop_vdi_ws_polling(VdiWsClient *vdi_ws_client)
{
    printf("%s\n", (char *)__func__);
    remove_recconect_timer(vdi_ws_client);
    vdi_ws_client->is_correctly_closed_flag = TRUE;

    if(vdi_ws_client->soup_websocket_connection)
        soup_websocket_connection_close(vdi_ws_client->soup_websocket_connection, 0, NULL);

    if(vdi_ws_client->ws_msg)
        g_object_unref(vdi_ws_client->ws_msg);
}
