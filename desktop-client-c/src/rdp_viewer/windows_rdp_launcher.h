#ifndef WINDOWS_RDP_LAUNCHER_H
#define WINDOWS_RDP_LAUNCHER_H

#include <gtk/gtk.h>

void launch_windows_rdp_client(const gchar *usename, const gchar *password, gchar *ip, int port);

#endif // WINDOWS_RDP_LAUNCHER_H