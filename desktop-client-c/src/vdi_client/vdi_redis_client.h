#ifndef VDI_REDIS_CLIENT_H
#define VDI_REDIS_CLIENT_H

#include <gtk/gtk.h>

#include <hiredis.h>

typedef struct{

    redisContext *redis_context;
    gboolean is_connected;
    //GMutex lock;
    //GCancellable *cancel_job;

} RedisClient;

void vdi_redis_client_connect(RedisClient *redis_client, gchar *password, gchar *channel, int port);

#endif // VDI_REDIS_CLIENT_H
