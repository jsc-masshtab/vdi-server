#ifndef RDP_VIEWER_WINDOW_H
#define RDP_VIEWER_WINDOW_H

#include <gtk/gtk.h>

#include "rdp_client.h"

#include "remote-viewer-timed-revealer.h"

typedef struct{
    GtkResponseType *dialog_window_response_p;
    GMainLoop **loop_p;

    UINT32 *last_rdp_error_p;

    GtkBuilder *builder;
    GtkWidget *rdp_viewer_window;
    GtkWidget *overlay_toolbar;
    VirtViewerTimedRevealer *revealer;
    GtkWidget *top_menu;

    guint g_timeout_id;

} RdpViewerData;


RdpViewerData *rdp_viewer_window_create(ExtendedRdpContext *ex_context, UINT32 *last_rdp_error_p);
void rdp_viewer_window_destroy(RdpViewerData *rdp_viewer_data);

#endif // RDP_VIEWER_WINDOW_H
