#ifndef RDP_VIEWER_WINDOW_H
#define RDP_VIEWER_WINDOW_H

#include <gtk/gtk.h>

#include "rdp_client.h"

#include "remote-viewer-timed-revealer.h"

typedef struct{
    GtkResponseType *dialog_window_response_p;
    GMainLoop **loop_p;

    UINT32 *last_rdp_error_p;

    // gui
    GtkBuilder *builder;
    GtkWidget *rdp_viewer_window;
    GtkWidget *overlay_toolbar;
    VirtViewerTimedRevealer *revealer;
    GtkWidget *top_menu;

    GtkWidget *rdp_display;

    // image data
    int im_origin_x;
    int im_origin_y;
    int im_width;
    int im_height;

    // monitor data
    int monitor_index;
    GdkRectangle monitor_geometry;

    guint g_timeout_id;

    ExtendedRdpContext *ex_rdp_context;

    GdkGrabStatus ggs;

} RdpViewerData;


RdpViewerData *rdp_viewer_window_create(ExtendedRdpContext *ex_rdp_context, UINT32 *last_rdp_error_p);
void rdp_viewer_window_destroy(RdpViewerData *rdp_viewer_data);
void rdp_viewer_set_monitor_data(RdpViewerData *rdp_viewer_data, GdkRectangle geometry, int monitor_index);

#endif // RDP_VIEWER_WINDOW_H
