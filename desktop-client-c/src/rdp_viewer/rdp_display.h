#ifndef RDP_DISPLAY_H
#define RDP_DISPLAY_H

#include <gtk/gtk.h>

#include <freerdp/freerdp.h>
#include <freerdp/constants.h>
#include <freerdp/gdi/gdi.h>
#include <freerdp/utils/signal.h>

#include "rdp_client.h"

GtkWidget *rdp_display_create(ExtendedRdpContext *ex_context, UINT32 *last_rdp_error_p);









#endif // RDP_DISPLAY_H