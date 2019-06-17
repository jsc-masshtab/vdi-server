//
// Created by solomin on 15.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_API_SESSION_H
#define VIRT_VIEWER_VEIL_VDI_API_SESSION_H

#include <gtk/gtk.h>

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
void stopSession();

void configureSession();

const gchar *getVdiSessionToken();

void getVdiVmData(GTask         *task,
                 gpointer       source_object,
                 gpointer       task_data,
                 GCancellable  *cancellable);


#endif //VIRT_VIEWER_VEIL_VDI_API_SESSION_H
