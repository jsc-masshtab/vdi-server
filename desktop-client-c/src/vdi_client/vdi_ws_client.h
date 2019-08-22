//
// Created by solomin on 21.08.19.
//


#ifndef WS_VDI_CLIENT_H
#define WS_VDI_CLIENT_H

#include <libsoup/soup-session.h>
#include <libsoup/soup-message.h>

typedef void (*WsDataReceivedCallback) (gboolean is_vdi_online);

typedef struct{
    // kind of public
    SoupSession *soup_session;
    WsDataReceivedCallback ws_data_received_callback;

    // kind of private
    //SoupMessage *ws_msg;
    gchar *vdi_url;

    SoupWebsocketConnection *soup_websocket_connection;

    gboolean is_correctly_closed_flag;

    guint reconnect_timer_descriptor;

    int test_int;

} VdiWsClient;

// pool vdi server if it's online
void init_vdi_ws_client(VdiWsClient *ws_vdi_client);
void deinit_vdi_ws_client(VdiWsClient *ws_vdi_client);
void start_vdi_ws_polling(VdiWsClient *ws_vdi_client, const gchar *vdi_ip,
                          WsDataReceivedCallback ws_data_received_callback);
void stop_vdi_ws_polling(VdiWsClient *ws_vdi_client);

#endif // WS_VDI_CLIENT_H
