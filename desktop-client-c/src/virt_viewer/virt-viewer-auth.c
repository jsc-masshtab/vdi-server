/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2007-2012 Red Hat, Inc.
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
 *
 * Author: Daniel P. Berrange <berrange@redhat.com>
 */

#include <config.h>

#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>

#ifdef HAVE_GTK_VNC
#include <vncdisplay.h>
#endif

#include "virt-viewer-auth.h"
#include "virt-viewer-util.h"

static void
show_password(GtkCheckButton *check_button G_GNUC_UNUSED,
              GtkEntry *entry)
{
    gtk_entry_set_visibility(entry, !gtk_entry_get_visibility(entry));
}

/* NOTE: if username is provided, and *username is non-NULL, the user input
 * field will be pre-filled with this value. The existing string will be freed
 * before setting the output parameter to the user-entered value.
 */
gboolean
virt_viewer_auth_collect_credentials(GtkWindow *window,
                                     const char *type,
                                     const char *address,
                                     char **username,
                                     char **password)
{
    GtkWidget *dialog = NULL;
    GtkBuilder *creds = virt_viewer_util_load_ui("virt-viewer-auth.ui");
    GtkWidget *credUsername;
    GtkWidget *credPassword;
    GtkWidget *promptUsername;
    GtkWidget *promptPassword;
    GtkWidget *labelMessage;
    GtkWidget *checkPassword;
    int response;
    char *message;

    dialog = GTK_WIDGET(gtk_builder_get_object(creds, "auth"));
    gtk_dialog_set_default_response(GTK_DIALOG(dialog), GTK_RESPONSE_OK);
    gtk_window_set_transient_for(GTK_WINDOW(dialog), window);

    labelMessage = GTK_WIDGET(gtk_builder_get_object(creds, "message"));
    credUsername = GTK_WIDGET(gtk_builder_get_object(creds, "cred-username"));
    promptUsername = GTK_WIDGET(gtk_builder_get_object(creds, "prompt-username"));
    credPassword = GTK_WIDGET(gtk_builder_get_object(creds, "cred-password"));
    promptPassword = GTK_WIDGET(gtk_builder_get_object(creds, "prompt-password"));
    checkPassword = GTK_WIDGET(gtk_builder_get_object(creds, "show-password"));

    gtk_widget_set_sensitive(credUsername, username != NULL);
    if (username && *username) {
        gtk_entry_set_text(GTK_ENTRY(credUsername), *username);
        /* if username is pre-filled, move focus to password field */
        gtk_widget_grab_focus(credPassword);
    }
    gtk_widget_set_sensitive(promptUsername, username != NULL);
    gtk_widget_set_sensitive(credPassword, password != NULL);
    gtk_widget_set_sensitive(promptPassword, password != NULL);

    g_signal_connect(checkPassword, "clicked", G_CALLBACK(show_password), credPassword);

    if (address) {
        message = g_strdup_printf(_("Authentication is required for the %s connection to:\n\n<b>%s</b>\n\n"),
                                  type,
                                  address);
    } else {
        message = g_strdup_printf(_("Authentication is required for the %s connection:\n"),
                                  type);
    }

    gtk_label_set_markup(GTK_LABEL(labelMessage), message);
    g_free(message);

    gtk_widget_show_all(dialog);
    response = gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_hide(dialog);

    if (response == GTK_RESPONSE_OK) {
        if (username) {
            g_free(*username);
            *username = g_strdup(gtk_entry_get_text(GTK_ENTRY(credUsername)));
        }
        if (password)
            *password = g_strdup(gtk_entry_get_text(GTK_ENTRY(credPassword)));
    }

    gtk_widget_destroy(GTK_WIDGET(dialog));
    g_object_unref(G_OBJECT(creds));

    return response == GTK_RESPONSE_OK;
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
