#ifndef VDI_REDIS_CLIENT_H
#define VDI_REDIS_CLIENT_H

#include <gtk/gtk.h>

#include <hiredis.h>

typedef struct{

    gboolean is_connected;
    //GMutex lock;
    //GCancellable *cancel_job;

} RedisClient;

void vdi_redis_client_connect(gchar *password, gchar *channel, int port);

#endif // VDI_REDIS_CLIENT_H
