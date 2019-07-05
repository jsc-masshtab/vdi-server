//
// Created by Solomin on 13.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_MANAGER_H
#define VIRT_VIEWER_VEIL_VDI_MANAGER_H

#include <gtk/gtk.h>


GtkResponseType vdi_manager_dialog(GtkWindow *main_window, gchar **uri, gchar **user, gchar **password);

#endif //VIRT_VIEWER_VEIL_VDI_MANAGER_H
