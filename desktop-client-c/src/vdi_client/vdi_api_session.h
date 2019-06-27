//
// Created by solomin on 15.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_API_SESSION_H
#define VIRT_VIEWER_VEIL_VDI_API_SESSION_H

#include <gtk/gtk.h>
#include <json-glib/json-glib.h>
#include <libsoup/soup-session.h>
#include <libsoup/soup-message.h>

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

    gchar *api_url;
    gchar *auth_url;
    gchar *jwt;

} VdiSession;

// Functions

void setVdiCredentials(const gchar *username, const gchar *password, const gchar *ip, const gchar *port);

void startSession();
void stopSession();
void cancellPendingRequests();

void setupHeaderForApiCall(SoupMessage *msg);

guint sendMessage(SoupMessage *msg);

// Получаем токен
gboolean refreshVdiSessionToken();

//void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer);

gchar * apiCall(const char *method, const char *uri_string);

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

// json (maybe to another file)
JsonObject * getJsonObject(JsonParser *parser, const gchar *data);
JsonArray * getJsonArray(JsonParser *parser, const gchar *data);
// threads
void executeAsyncTask(GTaskThreadFunc  task_func, GAsyncReadyCallback  callback, gpointer callback_data);


#endif //VIRT_VIEWER_VEIL_VDI_API_SESSION_H
