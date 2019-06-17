//
// Created by solomin on 15.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_API_SESSION_H
#define VIRT_VIEWER_VEIL_VDI_API_SESSION_H

#include <gtk/gtk.h>
#include <json-glib/json-glib.h>

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

// Functions
void executeAsyncTask(GTaskThreadFunc  task_func, GAsyncReadyCallback  callback, gpointer callback_data);

void startSession();
void configureSession(GTask         *task,
                      gpointer       source_object G_GNUC_UNUSED,
                      gpointer       task_data G_GNUC_UNUSED,
                      GCancellable  *cancellable G_GNUC_UNUSED);
void stopSession();

gboolean refreshVdiSessionToken();

void gInputStreamToBuffer(GInputStream *inputStream, gchar *responseBuffer);

gchar * apiCall(const char *method, const char *uri_string);

void getVdiVmData(GTask         *task,
                 gpointer       source_object,
                 gpointer       task_data,
                 GCancellable  *cancellable);

JsonObject * getJsonObject(JsonParser *parser, const gchar *data);


#endif //VIRT_VIEWER_VEIL_VDI_API_SESSION_H
