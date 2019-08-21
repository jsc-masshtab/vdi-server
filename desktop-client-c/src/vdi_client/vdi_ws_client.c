#include "vdi_ws_client.h"


static void ws_message_received(SoupWebsocketConnection *self G_GNUC_UNUSED, gint type G_GNUC_UNUSED,
                                GBytes *message,  gpointer user_data)
{
    VdiWsClient *vdi_ws_client = user_data;
    vdi_ws_client->ws_data_received_callback(message);
}

static void ws_closed(SoupWebsocketConnection *self, gpointer user_data)
{
    printf("%s\n", (char *)__func__);
}

static void got_ws_connection(GObject *object, GAsyncResult *result, gpointer user_data)
{
    printf("%s\n", (char *)__func__);
    VdiWsClient *vdi_ws_client = user_data;
    GError *error = NULL;
    vdi_ws_client->soup_websocket_connection =
            soup_session_websocket_connect_finish(SOUP_SESSION (object), result, &error);
    if (vdi_ws_client->soup_websocket_connection == NULL) {
        printf("%s ws error: %s\n", (char *)__func__, error->message);
        return;
    }
    // connects
    g_signal_connect(vdi_ws_client->soup_websocket_connection, "message", G_CALLBACK(ws_message_received), user_data);
    g_signal_connect(vdi_ws_client->soup_websocket_connection, "closed", G_CALLBACK(ws_closed), user_data);
}

void start_vdi_ws_polling(VdiWsClient *vdi_ws_client, SoupSession *soup_session, const gchar *vdi_ip)
{
    gchar *url = g_strdup_printf ("ws://%s/ws/client/vdi_server_check", vdi_ip);
    SoupMessage *msg = soup_message_new("GET", url);
    g_free (url);
    if (msg == NULL)
        return;

    soup_session_websocket_connect_async(soup_session, msg, NULL, NULL, NULL,
                              got_ws_connection, vdi_ws_client);
    g_object_unref(msg);
}

void stop_vdi_ws_polling(VdiWsClient *vdi_ws_client)
{
    soup_websocket_connection_close(vdi_ws_client->soup_websocket_connection, 0, NULL);
}
