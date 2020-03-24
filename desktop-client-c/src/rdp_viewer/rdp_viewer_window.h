#ifndef RDP_VIEWER_WINDOW_H
#define RDP_VIEWER_WINDOW_H

#include <gtk/gtk.h>

#include "rdp_client.h"

#include "remote-viewer-timed-revealer.h"

typedef struct{
    GtkResponseType dialog_window_response;
    GMainLoop *loop;

    GtkWidget *rdp_viewer_window;
    GtkWidget *overlay_toolbar;
    VirtViewerTimedRevealer *revealer;
    GtkWidget *top_menu;

} RdpViewerData;


RdpViewerData rdp_viewer_window_create(ExtendedRdpContext *ex_context);

#endif // RDP_VIEWER_WINDOW_H
