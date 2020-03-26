/**
 * FreeRDP: A Remote Desktop Protocol Implementation
 * GTK GUI
 * Solomin a.solomin@mashtab.otg
 */

#include <gio/gio.h>
#include <gtk/gtk.h>
#include <glib/garray.h>
#include <gdk-pixbuf/gdk-pixbuf.h>

#include <cairo/cairo.h>

#include <freerdp/locale/keyboard.h>
#include <freerdp/scancode.h>

#include "rdp_viewer.h"
#include "rdp_client.h"
#include "rdp_display.h"
#include "rdp_viewer_window.h"

#include "remote-viewer-util.h"
#include "config.h"

#include "async.h"

static gboolean update_cursor_callback(rdpContext* context)
{
    ExtendedRdpContext* ex_rdp_context = (ExtendedRdpContext*)context;

    if (!ex_rdp_context || !ex_rdp_context->is_running)
        return TRUE;

    g_mutex_lock(&ex_rdp_context->cursor_mutex);

    for (guint i = 0; i < ex_rdp_context->rdp_viewer_data_array->len; ++i) {
        RdpViewerData *rdp_viewer_data = g_array_index(ex_rdp_context->rdp_viewer_data_array, RdpViewerData *, i);
        GdkWindow *parent_window = gtk_widget_get_parent_window(rdp_viewer_data->rdp_display);
        gdk_window_set_cursor(parent_window,  ex_rdp_context->gdk_cursor);
    }

    //printf("%s ex_pointer->test_int: \n", (const char *)__func__);
    g_mutex_unlock(&ex_rdp_context->cursor_mutex);

    return FALSE;
}

static ExtendedRdpContext* create_rdp_context(UINT32 *last_rdp_error_p)
{
    rdpContext* context = rdp_client_create_context();
    ExtendedRdpContext* ex_rdp_context = (ExtendedRdpContext*)context;
    ex_rdp_context->is_running = FALSE;
    //ex_rdp_context->update_image_callback = (UpdateImageCallback)update_image_callback;
    ex_rdp_context->update_cursor_callback = (UpdateCursorCallback)update_cursor_callback;
    ex_rdp_context->test_int = 666; // temp
    ex_rdp_context->last_rdp_error_p = last_rdp_error_p;
    // init mutex for rdp_routine syncronization
    g_mutex_init(&ex_rdp_context->rdp_routine_mutex);
    g_mutex_init(&ex_rdp_context->cursor_mutex);

    return ex_rdp_context;
}

static void destroy_rdp_context(ExtendedRdpContext* ex_rdp_context)
{
    if (ex_rdp_context && ex_rdp_context->is_running) {
        // stopping RDP routine

        printf("%s: abort now: %i\n", (const char *)__func__, ex_rdp_context->test_int);

        freerdp_abort_connect(ex_rdp_context->context.instance);
        // wait untill rdp thread finished. todo: seriously think if some sort of event primitive could be used
        wair_for_mutex_and_clear(&ex_rdp_context->rdp_routine_mutex);
        wair_for_mutex_and_clear(&ex_rdp_context->cursor_mutex);

        printf("%s: context free now: %i\n", (const char *)__func__, ex_rdp_context->test_int);
        freerdp_client_context_free((rdpContext*)ex_rdp_context);
        ex_rdp_context = NULL;
    }
}

GtkResponseType rdp_viewer_start(const gchar *usename, const gchar *password, gchar *domain, gchar *ip, int port)
{
    printf("%s domain %s\n", (const char *)__func__, domain);

    GtkResponseType dialog_window_response = GTK_RESPONSE_CLOSE;
    GMainLoop *loop;
    // create RDP context
    UINT32 last_rdp_error = 0;
    ExtendedRdpContext *ex_rdp_context = create_rdp_context(&last_rdp_error);
    rdp_client_set_credentials(ex_rdp_context, usename, password, domain, ip, port);

    // determine monitor number
    GdkDisplay *display = gdk_display_get_default();
    int monitor_number = gdk_display_get_n_monitors(display);

    // create rdp viewer windows
    GArray *rdp_viewer_data_array = g_array_new(FALSE, FALSE, sizeof(RdpViewerData *));
    int total_monitor_width = 0;
    int total_monitor_height = 0;
    for (int i = 0; i < monitor_number; ++i) {
        RdpViewerData *rdp_viewer_data = rdp_viewer_window_create(ex_rdp_context, &last_rdp_error);
        g_array_append_val(rdp_viewer_data_array, rdp_viewer_data);

        // set references
        rdp_viewer_data->dialog_window_response_p = &dialog_window_response;
        rdp_viewer_data->loop_p = &loop;

        // set monitor data
        GdkMonitor *monitor = gdk_display_get_monitor(display, i);
        GdkRectangle geometry;
        gdk_monitor_get_geometry(monitor, &geometry);
        rdp_viewer_set_monitor_data(rdp_viewer_data, geometry, i);

        total_monitor_width += geometry.width;
        total_monitor_height += geometry.height;
    }

    ex_rdp_context->rdp_viewer_data_array = rdp_viewer_data_array;

    // set monitor data to rdp client
    //GdkRectangle default_monitor_geometry = get_default_monitor_geometry(); // temp

    const int max_image_width = 3840;//1920;
    const int max_image_height = 1080;
    int optimal_image_width = MIN(max_image_width, total_monitor_width);
    int optimal_image_height = MIN(max_image_height, total_monitor_height);
    rdp_client_set_optimilal_image_size(ex_rdp_context, optimal_image_width, optimal_image_height);

    // launch RDP routine in thread
    GTask *task = g_task_new(NULL, NULL, NULL, NULL);
    g_task_set_task_data(task, (rdpContext *)ex_rdp_context, NULL);
    g_task_run_in_thread(task, rdp_client_routine);
    g_object_unref(task);

    // launch event loop
    create_loop_and_launch(&loop);

    // clear memory
    destroy_rdp_context(ex_rdp_context);

    guint i;
    for (i = 0; i < rdp_viewer_data_array->len; ++i) {
        RdpViewerData *rdp_viewer_data = g_array_index(rdp_viewer_data_array, RdpViewerData *, i);
        rdp_viewer_window_destroy(rdp_viewer_data);
    }
    g_array_free(rdp_viewer_data_array, TRUE);

    return dialog_window_response;
}
