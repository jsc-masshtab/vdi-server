/**
 * FreeRDP: A Remote Desktop Protocol Implementation
 * GTK GUI
 * Solomin a.solomin@mashtab.otg
 */

#ifndef FREERDP_CLIENT_SAMPLE_H
#define FREERDP_CLIENT_SAMPLE_H

#include <freerdp/freerdp.h>
#include <freerdp/client/rdpei.h>
#include <freerdp/client/tsmf.h>
#include <freerdp/client/rail.h>
#include <freerdp/client/cliprdr.h>
#include <freerdp/client/rdpgfx.h>
#include <freerdp/client/encomsp.h>

#include <gtk/gtk.h>

#include "rdp_cursor.h"

struct ExtendedRdpContext;

typedef gboolean (*UpdateImageCallback) (rdpContext* context);
typedef gboolean (*UpdateCursorCallback) (rdpContext* context);

//#define MAX_DISPLAY_NUMBER 3

typedef struct {
	rdpContext context;

	/* Channels */
    RdpeiClientContext *rdpei;
    RdpgfxClientContext *gfx;
    EncomspClientContext *encomsp;

    GtkWidget *rdp_display; // pointer to display widget

    GdkPixbuf *frame_pix_buf; //frame image data
    GMutex primary_buffer_mutex; // mutex for protecting primary_buffer

    GMutex rdp_routine_mutex; // used to wait untill rdp_client_routine finished

    cairo_surface_t* surface; //

//    INT32 ninvalid;// number of invalid regions
//    HGDI_RGN cinvalid;

    GdkCursor *gdk_cursor; // cursor
    GMutex cursor_mutex; // mutex for protecting gdk_cursor

    int test_int;

    gboolean is_running; // is rdp routine running

    UINT32 *last_rdp_error_p; // pointer to last_rdp_error

    // credentials
    gchar *usename;
    gchar *password;
    gchar *ip;
    int port;

    //client monitors geometry info
    //GdkRectangle client_monitors_geometry[MAX_DISPLAY_NUMBER];
    GdkRectangle client_default_geometry;

    UpdateImageCallback update_image_callback; // callback for updating image in the main thread
    UpdateCursorCallback update_cursor_callback; // callback for updating cursor in the main thread

} ExtendedRdpContext;


rdpContext* rdp_client_create_context(void);

void rdp_client_set_credentials(ExtendedRdpContext *ex_context,
                                const gchar *usename, const gchar *password, gchar *ip, int port);
void rdp_client_set_screen_resolution(ExtendedRdpContext *ex_context, GdkRectangle client_default_geometry);

void rdp_client_routine(GTask   *task,
                 gpointer       source_object G_GNUC_UNUSED,
                 gpointer       task_data G_GNUC_UNUSED,
                 GCancellable  *cancellable G_GNUC_UNUSED);


#endif /* FREERDP_CLIENT_SAMPLE_H */
