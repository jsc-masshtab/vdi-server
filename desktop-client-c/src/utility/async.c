#include "async.h"

void execute_async_task(GTaskThreadFunc task_func, GAsyncReadyCallback callback, gpointer task_data)
{
    GTask *task = g_task_new(NULL, NULL, callback, NULL);
    if(task_data)
        g_task_set_task_data(task, task_data, NULL);
    g_task_run_in_thread(task, task_func);
    g_object_unref (task);
}
