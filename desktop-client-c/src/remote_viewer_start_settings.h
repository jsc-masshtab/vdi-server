#ifndef REMOTE_VIEWER_START_SETTINGS_H
#define REMOTE_VIEWER_START_SETTINGS_H

#include <gtk/gtk.h>

#include "vdi_api_session.h"

typedef struct{

   gchar *ip;
   int port;

   gboolean is_ldap;
   gboolean is_connect_to_prev_pool;

   VdiVmRemoteProtocol remote_protocol_type;

} ConnectSettingsData;


GtkResponseType remote_viewer_start_settings_dialog(ConnectSettingsData *connect_settings_data);
void fill_connect_settings_data_from_ini_file(ConnectSettingsData *connect_settings_data);


#endif // REMOTE_VIEWER_START_SETTINGS_H
