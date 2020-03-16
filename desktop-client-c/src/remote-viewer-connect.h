/*
 * Veil VDI thin client
 * Based on virt-viewer and freerdp
 *
 */

#ifndef REMOTE_VIEWER_CONNECT_H
#define REMOTE_VIEWER_CONNECT_H

#include <gtk/gtk.h>

#include "vdi_api_session.h"

GtkResponseType remote_viewer_connect_dialog(gchar **user, gchar **password, gchar **domain,
                                      gchar **ip, gchar **port, gboolean *is_connect_to_prev_pool,
                                      gchar **vm_verbose_name, VdiVmRemoteProtocol *remote_protocol_type);

#endif /* REMOTE_VIEWER_CONNECT_H */

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
