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

static ExtendedRdpContext* create_rdp_context(UINT32 *last_rdp_error_p)
{
    rdpContext* context = rdp_client_create_context();
    ExtendedRdpContext* ex_context = (ExtendedRdpContext*)context;
    ex_context->is_running = FALSE;
    //ex_context->update_image_callback = (UpdateImageCallback)update_image_callback;
    ex_context->update_cursor_callback = (UpdateCursorCallback)update_cursor_callback;
    ex_context->test_int = 666; // temp
    ex_context->last_rdp_error_p = last_rdp_error_p;
    // init mutex for rdp_routine syncronization
    g_mutex_init(&ex_context->rdp_routine_mutex);
    g_mutex_init(&ex_context->cursor_mutex);

    return ex_context;
}

static void destroy_rdp_context(ExtendedRdpContext* ex_context)
{
    if (ex_context && ex_context->is_running) {
        // stopping RDP routine

        printf("%s: abort now: %i\n", (const char *)__func__, ex_context->test_int);

        freerdp_abort_connect(ex_context->context.instance);
        // wait untill rdp thread finished. todo: seriously think if some sort of event primitive could be used
        wair_for_mutex_and_clear(&ex_context->rdp_routine_mutex);
        wair_for_mutex_and_clear(&ex_context->cursor_mutex);

        printf("%s: context free now: %i\n", (const char *)__func__, ex_context->test_int);
        freerdp_client_context_free((rdpContext*)ex_context);
        ex_context = NULL;
    }
}

GtkResponseType rdp_viewer_start(const gchar *usename, const gchar *password, gchar *domain, gchar *ip, int port)
{
    printf("%s domain %s\n", (const char *)__func__, domain);

    // create RDP context
    UINT32 last_rdp_error = 0;
    ExtendedRdpContext *ex_context = create_rdp_context(&last_rdp_error); // deleted upon widget deletion
    rdp_client_set_credentials(ex_context, usename, password, domain, ip, port);

    // determine monitor number
    unsigned int monitor_number = 1;

    // create rdp viewer windows
    RdpViewerData **rdp_viewer_data_array = malloc(monitor_number * sizeof (RdpViewerData *));
    for(unsigned int i = 0; i < monitor_number; ++i){
        rdp_viewer_data_array[i] = rdp_viewer_window_create(ex_context, &last_rdp_error);
    }

    GtkResponseType dialog_window_response = GTK_RESPONSE_CLOSE;
    GMainLoop *loop;
    create_loop_and_launch(&loop);

    // clear memory!
    destroy_rdp_context(ex_context);
    rdp_viewer_window_destroy(rdp_viewer_data);

    return dialog_window_response;
}
