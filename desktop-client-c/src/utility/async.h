#ifndef ASYNC_H
#define ASYNC_H

#include <gio/gio.h>

// threads
void execute_async_task(GTaskThreadFunc  task_func, GAsyncReadyCallback  callback, gpointer callback_data);

#endif // ASYNC_H
