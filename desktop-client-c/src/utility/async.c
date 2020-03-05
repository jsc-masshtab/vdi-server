#include "async.h"

void execute_async_task(GTaskThreadFunc task_func, GAsyncReadyCallback callback, gpointer task_data, gpointer callback_data)
{
    GTask *task = g_task_new(NULL, NULL, callback, callback_data);
    if (task_data)
        g_task_set_task_data(task, task_data, NULL);
    g_task_run_in_thread(task, task_func);
    g_object_unref (task);
}

// sleep which can be cancelled so user will not notice any freeze
void cancellable_sleep(gulong microseconds, volatile gboolean *running_flag)
{
    const gulong interval = 30000; // 30 ms

    gulong fractional_part = microseconds % interval;
    gulong integral_part = microseconds / interval;

    g_usleep(fractional_part);

    for (gulong i = 0; i < integral_part; ++i) {
        if (!(*running_flag))
            return;
        g_usleep(interval);
    }
}

void wair_for_mutex_and_clear(GMutex *cursor_mutex)
{
    g_mutex_lock(cursor_mutex);
    g_mutex_unlock(cursor_mutex);
    g_mutex_clear(cursor_mutex);
}
