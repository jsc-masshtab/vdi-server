#include "async.h"

void execute_async_task(GTaskThreadFunc task_func, GAsyncReadyCallback callback, gpointer task_data)
{
    GTask *task = g_task_new(NULL, NULL, callback, NULL);
    if (task_data)
        g_task_set_task_data(task, task_data, NULL);
    g_task_run_in_thread(task, task_func);
    g_object_unref (task);
}

// sleep which can be cancelled so user will not notice any freeze
void cancellable_sleep(gulong microseconds, volatile gboolean cancel_flag)
{
    const gulong interval = 30000; // 30 ms

    gulong fractional_part = microseconds % interval;
    gulong integral__part = microseconds / interval;

    g_usleep(fractional_part);

    for (gulong i = 0; i < integral__part; ++i) {
        if (cancel_flag)
            return;
        g_usleep(interval);
    }
}
