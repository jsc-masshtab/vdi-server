#ifndef ASYNC_H
#define ASYNC_H

#include <gio/gio.h>

// threads
void execute_async_task(GTaskThreadFunc  task_func, GAsyncReadyCallback  callback, gpointer callback_data);

// sleep which can be cancelled so user will not notice any freeze
void cancellable_sleep(gulong time, volatile gboolean cancel_flag);

#endif // ASYNC_H
