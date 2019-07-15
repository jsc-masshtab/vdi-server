//
// Created by solomin on 15.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_API_SESSION_H
#define VIRT_VIEWER_VEIL_VDI_API_SESSION_H

#include <gtk/gtk.h>
#include <json-glib/json-glib.h>
#include <libsoup/soup-session.h>
#include <libsoup/soup-message.h>

#define VM_ID_UNKNOWN -1

// vm operational system
typedef enum{
    VDI_VM_WIN,
    VDI_VM_LINUX,
    VDI_VM_ANOTHER_OS
} VdiVmOs;

// Инфа о виртуальной машине полученная от vdi
typedef struct{

    int osType;
    gchar *ip;
    gint testData;

} VdiVmData;

// vdi session
typedef struct{

    SoupSession *soupSession;

    gchar *vdi_username;
    gchar *vdi_password;
    gchar *vdi_ip;
    gchar *vdi_port;

    gchar *api_url;
    gchar *auth_url;
    gchar *jwt;

    gboolean isActive;

    gint64 currentVmId;

} VdiSession;

// Data which passed to apiCall
typedef struct{
    gint64 currentVmId;
    gchar *actionOnVmStr;
    gboolean isActionForced;

} ActionOnVmData;

// Functions
// init session
void startVdiSession();
// deinit session
void stopVdiSession();
// cancell pending requests
void cancellPendingRequests();
// set vdi session credentials
void setVdiCredentials(const gchar *username, const gchar *password, const gchar *ip, const gchar *port);
// set current vm id
void setCurrentVmId(gint64 currentVmId);
// get current vm id
gint64 getCurrentVmId();

//void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer);
// Do api call. Return response body
gchar *apiCall(const char *method, const char *uri_string, const gchar *body_str);

// Запрашиваем список пулов
void getVdiVmData(GTask         *task,
                 gpointer       source_object,
                 gpointer       task_data,
                 GCancellable  *cancellable);

// Получаем виртуалку из пула
void getVmDFromPool(GTask         *task,
                  gpointer       source_object,
                  gpointer       task_data,
                  GCancellable  *cancellable);

// Do action on virtual machine
void doActionOnVm(GTask         *task,
                  gpointer       source_object,
                  gpointer       task_data,
                  GCancellable  *cancellable);

// threads
void executeAsyncTask(GTaskThreadFunc  task_func, GAsyncReadyCallback  callback, gpointer callback_data);
void doActionOnVmAsync(const gchar *actionStr, gboolean isForced);

#endif //VIRT_VIEWER_VEIL_VDI_API_SESSION_H
