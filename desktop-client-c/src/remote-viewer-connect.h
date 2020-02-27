/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2015 Red Hat, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#ifndef REMOTE_VIEWER_CONNECT_H
#define REMOTE_VIEWER_CONNECT_H

#include <gtk/gtk.h>

#include "vdi_api_session.h"

GtkResponseType remote_viewer_connect_dialog(gchar **user, gchar **password,
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
