//
// Created by solomin on 15.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_API_SESSION_H
#define VIRT_VIEWER_VEIL_VDI_API_SESSION_H

#include <gtk/gtk.h>
#include <json-glib/json-glib.h>
#include <libsoup/soup-session.h>
#include <libsoup/soup-message.h>

#include "vdi_ws_client.h"
#include "async.h"
#include "vdi_redis_client.h"

#define HTTP_RESPONSE_TIOMEOUT 10

// remote protocol type
typedef enum{
    VDI_SPICE_PROTOCOL,
    VDI_RDP_PROTOCOL,
    VDI_ANOTHER_REMOTE_PROTOCOL
} VdiVmRemoteProtocol;

// vm operational system
typedef enum{
    VDI_VM_WIN,
    VDI_VM_LINUX,
    VDI_VM_ANOTHER_OS
} VdiVmOs;

// Инфа о виртуальной машине полученная от vdi
typedef struct{

    VdiVmOs os_type;

    gchar *vm_host;
    gint64 vm_port;
    gchar *vm_password;
    gchar *vm_verbose_name;

    gchar *message;

    gint test_data;

} VdiVmData;

// vdi session todo: по-хорошему надо защитить поля от одновременного домтупа из разных потоков
// soup_session - thread safe. его не надо защищать
typedef struct{

    SoupSession *soup_session;

    gchar *vdi_username;
    gchar *vdi_password;
    gchar *vdi_ip;
    gchar *vdi_port; // todo: make it int!

    gchar *api_url;
    gchar *auth_url;
    gchar *jwt;
    gboolean is_ldap;

    gboolean is_active;

    gchar *current_pool_id;
    VdiVmRemoteProtocol current_remote_protocol;

    RedisClient *redis_client;

} VdiSession;

// Data which passed to api_call
typedef struct{
    gchar *current_vm_id;
    gchar *action_on_vm_str;
    gboolean is_action_forced;

} ActionOnVmData;

// Functions
// init session
void start_vdi_session(void);
// deinit session
void stop_vdi_session(void);
// get session
SoupSession *get_soup_session(void);
// get vid server ip
const gchar *get_vdi_ip(void);
// get port
const gchar *get_vdi_port(void);
// get username
const gchar *get_vdi_username(void);
// get password
const gchar *get_vdi_password(void);
// cancell pending requests
void vdi_api_cancell_pending_requests(void);
// set vdi session credentials
void set_vdi_credentials(const gchar *username, const gchar *password, const gchar *ip,
                         const gchar *port, gboolean is_ldap);
// set current vm id
void set_current_pool_id(const gchar *current_pool_id);
// get current vm id
const gchar *get_current_pool_id(void);

// set current remote protocol
void set_current_remote_protocol(VdiVmRemoteProtocol remote_protocol);
// get current remote protocol
VdiVmRemoteProtocol get_current_remote_protocol(void);


//void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer);
// Do api call. Return response body
gchar *api_call(const char *method, const char *uri_string, const gchar *body_str);

/// Таски выполняемые в потоке
// Fetch token
void get_vdi_token(GTask         *task,
                   gpointer       source_object,
                   gpointer       task_data,
                   GCancellable  *cancellable);

// Запрашиваем список пулов
void get_vdi_pool_data(GTask         *task,
                       gpointer       source_object,
                       gpointer       task_data,
                       GCancellable  *cancellable);

// Получаем виртуалку из пула
void get_vm_from_pool(GTask         *task,
                      gpointer       source_object,
                      gpointer       task_data,
                      GCancellable  *cancellable);

// Do action on virtual machine
void do_action_on_vm(GTask         *task,
                     gpointer       source_object,
                     gpointer       task_data,
                     GCancellable  *cancellable);

// Connect to Redis and subscribe
void vdi_api_session_connect_to_redis_and_subscribe(GTask         *task,
                                                    gpointer       source_object,
                                                    gpointer       task_data,
                                                    GCancellable  *cancellable);

// Log out
gboolean vdi_api_logout(void);

void do_action_on_vm_launch_task(const gchar *actionStr, gboolean isForced);


void free_action_on_vm_data(ActionOnVmData *action_on_vm_data);
void free_vdi_vm_data(VdiVmData *vdi_vm_data);

#endif //VIRT_VIEWER_VEIL_VDI_API_SESSION_H
