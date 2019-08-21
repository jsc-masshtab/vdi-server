//
// Created by solomin on 21.08.19.
//


#ifndef WS_VDI_CLIENT_H
#define WS_VDI_CLIENT_H

#include <libsoup/soup-session.h>
#include <libsoup/soup-message.h>

typedef void (*WsDataReceivedCallback) (GBytes *message);

typedef struct{
    SoupWebsocketConnection *soup_websocket_connection;
    WsDataReceivedCallback ws_data_received_callback;

} VdiWsClient;

// pool vdi server if it's online
void start_vdi_ws_polling(VdiWsClient *ws_vdi_client, SoupSession *soup_session, const gchar *vdi_ip);
void stop_vdi_ws_polling(VdiWsClient *ws_vdi_client);

#endif // WS_VDI_CLIENT_H
