#ifndef VDI_REDIS_CLIENT_H
#define VDI_REDIS_CLIENT_H

#include <gtk/gtk.h>

#include <hiredis.h>

typedef struct{

    redisContext *redis_context;
    gboolean is_subscribed;

    // connection data
    int port;
    int db;
    gchar *adress;
    gchar *password;
    gchar *channel;

    //GMutex lock;
    //GCancellable *cancel_job;

} RedisClient;

void vdi_redis_client_init(RedisClient *redis_client);
void vdi_redis_client_deinit(RedisClient *redis_client);
void vdi_redis_client_clear_connection_data(RedisClient *redis_client);

#endif // VDI_REDIS_CLIENT_H
