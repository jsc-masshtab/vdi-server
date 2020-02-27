#ifndef RDK_VIEWER_H
#define RDK_VIEWER_H

#include <gtk/gtk.h>

GtkResponseType rdp_viewer_start(const gchar *usename, const gchar *password, gchar *ip, int port);

#endif /* RDK_VIEWER_H */
