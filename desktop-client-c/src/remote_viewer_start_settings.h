#ifndef REMOTE_VIEWER_START_SETTINGS_H
#define REMOTE_VIEWER_START_SETTINGS_H

#include <gtk/gtk.h>

#include "vdi_api_session.h"

typedef struct{

   gchar *user;
   gchar *password;

   gboolean is_ldap;
   gboolean *is_connect_to_prev_pool;
   VdiVmRemoteProtocol *remote_protocol_type;

} StartSettingsData;

GtkResponseType remote_viewer_start_settings_dialog(void);


#endif // REMOTE_VIEWER_START_SETTINGS_H
