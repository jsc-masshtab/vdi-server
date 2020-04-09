#ifndef RDP_DISPLAY_H
#define RDP_DISPLAY_H

#include <gtk/gtk.h>

#include <freerdp/freerdp.h>
#include <freerdp/constants.h>
#include <freerdp/gdi/gdi.h>
#include <freerdp/utils/signal.h>

#include "rdp_client.h"
#include "rdp_viewer_window.h"

//typedef struct{
//    RdpViewerData *rdp_viewer_data;
//    ExtendedRdpContext *ex_rdp_context;

//} RdpDisplayData;

GtkWidget *rdp_display_create(RdpViewerData *rdp_viewer_data, ExtendedRdpContext *ex_rdp_context, UINT32 *last_rdp_error_p);









#endif // RDP_DISPLAY_H
