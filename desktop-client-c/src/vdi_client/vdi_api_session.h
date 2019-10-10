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

#define VM_ID_UNKNOWN -1

// vm operational system
typedef enum{
    VDI_VM_WIN,
    VDI_VM_LINUX,
    VDI_VM_ANOTHER_OS
} VdiVmOs;

// Инфа о виртуальной машине полученная от vdi
typedef struct{

    int os_type;
    gchar *ip;
    gint test_data;

} VdiVmData;

// vdi session
typedef struct{

    SoupSession *soup_session;

    gchar *vdi_username;
    gchar *vdi_password;
    gchar *vdi_ip;
    gchar *vdi_port;

    gchar *api_url;
    gchar *auth_url;
    gchar *jwt;

    gboolean is_active;

    gint64 current_vm_id;

} VdiSession;

// Data which passed to api_call
typedef struct{
    gint64 current_vm_id;
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
// cancell pending requests
void cancell_pending_requests(void);
// set vdi session credentials
void set_vdi_credentials(const gchar *username, const gchar *password, const gchar *ip, const gchar *port);
// set current vm id
void set_current_vm_id(gint64 current_vm_id);
// get current vm id
gint64 get_current_vm_id(void);

//void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer);
// Do api call. Return response body
gchar *api_call(const char *method, const char *uri_string, const gchar *body_str);

// Запрашиваем список пулов
void get_vdi_vm_data(GTask         *task,
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

void do_action_on_vm_async(const gchar *actionStr, gboolean isForced);

#endif //VIRT_VIEWER_VEIL_VDI_API_SESSION_H
