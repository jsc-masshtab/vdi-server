//
// Created by Solomin on 13.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_MANAGER_H
#define VIRT_VIEWER_VEIL_VDI_MANAGER_H

#include <gtk/gtk.h>

#include "vdi_api_session.h"

GtkResponseType vdi_manager_dialog(GtkWindow *main_window, gchar **ip, gchar **port,
                                   gchar **password, gchar **vm_verbose_name, VdiVmRemoteProtocol *remote_protocol_type);

#endif //VIRT_VIEWER_VEIL_VDI_MANAGER_H
