#include "vdi_redis_client.h"

#include "remote-viewer-util.h"

static void vdi_redis_client_clear_redis_reply(redisReply *reply)
{
    if (reply)
        freeReplyObject(reply);
}

static gboolean vdi_redis_client_check_if_reply_contains_errors(
        RedisClient *redis_client, redisReply *reply, const gchar *cmd_category)
{
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {

        if (reply) {
            printf("%s: Redis %s failed: %s\n", (const char *)__func__, cmd_category, reply->str);
            vdi_redis_client_clear_redis_reply(reply);

        } else {
            printf("%s: Redis %s failed:\n", (const char *)__func__, cmd_category);
        }

        redisFree(redis_client->redis_context);
        redis_client->redis_context = NULL;
        return TRUE;
    }

    return FALSE;
}

void vdi_redis_client_init(RedisClient *redis_client)
{
    // do nothing if we alredy subscribed
    if (redis_client->is_subscribed)
        return;

    /// reddis connect
    struct timeval timeout = { 1, 500000 }; // 1.5 seconds
    redis_client->redis_context = redisConnectWithTimeout(
                redis_client->adress, redis_client->port, timeout);
    //g_free(redis_adress);

    if (redis_client->redis_context == NULL || redis_client->redis_context->err) {

        if (redis_client->redis_context) {
            printf("%s Connection error: %s\n", (const char *)__func__,
                   redis_client->redis_context->errstr);
            redisFree(redis_client->redis_context);
        } else {
            printf("%s Connection error: can't allocate redis context\n", (const char *)__func__);
        }

        redis_client->redis_context = NULL;
        return;
    }

    printf("%s Successfully connected to Reddis\n", (const char *)__func__);

    /// redis auth
    redisReply *reply = redisCommand(redis_client->redis_context, "AUTH %s", redis_client->password);
    if (vdi_redis_client_check_if_reply_contains_errors(redis_client, reply, "authentication"))
        return;
    vdi_redis_client_clear_redis_reply(reply);

    printf("%s Successfully authenticated on Redis\n", (const char *)__func__);

    /// select database
    reply = redisCommand(redis_client->redis_context, "SELECT %i", redis_client->db);
    if (vdi_redis_client_check_if_reply_contains_errors(redis_client, reply, "db selection"))
        return;
    vdi_redis_client_clear_redis_reply(reply);

    printf("%s Redis db %i successfully selected\n", (const char *)__func__, redis_client->db);

    /// redis subscribe
    reply = redisCommand(redis_client->redis_context, "SUBSCRIBE %s", redis_client->channel);
    if (vdi_redis_client_check_if_reply_contains_errors(redis_client, reply, "subscription"))
        return;
    vdi_redis_client_clear_redis_reply(reply);

    printf("%s Successfully subscrubed to channel %s\n", (const char *)__func__,
           redis_client->channel);

    redis_client->is_subscribed = TRUE;
}

void vdi_redis_client_deinit(RedisClient *redis_client)
{
    if (redis_client->redis_context) {
        // unsubscribe
        redisReply * reply = redisCommand(
                    redis_client->redis_context, "UNSUBSCRIBE %s", redis_client->channel);
        vdi_redis_client_check_if_reply_contains_errors(redis_client, reply, "unsubscribing");
        vdi_redis_client_clear_redis_reply(reply);

        // dissconnect
        redisFree(redis_client->redis_context);
    }
    redis_client->redis_context = NULL;
    redis_client->is_subscribed = FALSE;
    vdi_redis_client_clear_connection_data(redis_client);
}

void vdi_redis_client_clear_connection_data(RedisClient *redis_client)
{
    redis_client->port = 0;
    redis_client->db = 0;
    free_memory_safely(&redis_client->adress);
    free_memory_safely(&redis_client->password);
    free_memory_safely(&redis_client->channel);
}
