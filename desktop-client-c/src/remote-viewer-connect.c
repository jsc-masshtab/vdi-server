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

#include <config.h>

#include "virt-viewer-session-spice.h"
#include "remote-viewer-connect.h"
#include "virt-viewer-util.h"
#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>

#include <ctype.h>

extern gchar *m_username;
extern gchar *m_password;
extern gboolean opt_manual_mode;

static gboolean b_save_credentials_to_file = FALSE;

static const gchar *ini_file_path = "veil_client_settings.ini";

typedef struct
{
    gboolean response;
    GMainLoop *loop;
    GtkWidget *entry;
} ConnectionInfo;

// read credentials_from_settings_file  todo: move to another file
static gchar *
read_from_settings_file(const gchar *group_name,  const gchar *key)
{
    GError *error = NULL;
    gchar *str_value = NULL;;

    GKeyFile *keyfile = g_key_file_new ();

    if(!g_key_file_load_from_file(keyfile, ini_file_path,
                                  G_KEY_FILE_KEEP_COMMENTS |
                                  G_KEY_FILE_KEEP_TRANSLATIONS,
                                  &error))
    {
        g_debug("%s", error->message);
    }
    else {
        str_value = g_key_file_get_string(keyfile, group_name, key, &error);
    }

    g_key_file_free(keyfile);

    return str_value;
}


static void
write_to_settings_file(const gchar *group_name,  const gchar *key, const gchar *str_value)
{
    if(str_value == NULL)
        return;

    GError *error = NULL;

    GKeyFile *keyfile = g_key_file_new ();

    if(!g_key_file_load_from_file(keyfile, ini_file_path,
                                  G_KEY_FILE_KEEP_COMMENTS |
                                  G_KEY_FILE_KEEP_TRANSLATIONS,
                                  &error))
    {
        g_debug("%s", error->message);
    }
    else {
        g_key_file_set_value(keyfile, group_name, key, str_value);
    }

    g_key_file_free(keyfile);
}
//--------------------

// Перехватывается событие ввода текста. Игнорируется, если есть нецифры
static void
on_insert_text_event(GtkEditable *editable, const gchar *text, gint length,
        gint *position G_GNUC_UNUSED, gpointer data G_GNUC_UNUSED)
{
    int i;

    for (i = 0; i < length; ++i) {
        if (!isdigit(text[i])) {
            g_signal_stop_emission_by_name(G_OBJECT(editable), "insert-text");
            return;
        }
    }
}

static void
on_remember_checkbutton_clicked(GtkCheckButton *check_button,
                                GtkEntry *entry G_GNUC_UNUSED)
{
    printf("on_remember_checkbutton_clicked\n");
    b_save_credentials_to_file = gtk_toggle_button_get_active(check_button);
}

static void
shutdown_loop(GMainLoop *loop)
{
    if (g_main_loop_is_running(loop))
        g_main_loop_quit(loop);
}

static gboolean
window_deleted_cb(ConnectionInfo *ci)
{
    ci->response = FALSE;
    shutdown_loop(ci->loop);
    return TRUE;
}

static gboolean
key_pressed_cb(GtkWidget *widget G_GNUC_UNUSED, GdkEvent *event, gpointer data)
{
    GtkWidget *window = data;
    gboolean retval;
    if (event->type == GDK_KEY_PRESS) {
        switch (event->key.keyval) {
            case GDK_KEY_Escape:
                g_signal_emit_by_name(window, "delete-event", NULL, &retval);
                return TRUE;
            default:
                return FALSE;
        }
    }

    return FALSE;
}

static void
connect_button_clicked_cb(GtkButton *button G_GNUC_UNUSED, gpointer data)
{
    printf("connect_button_clicked_cb\n");
    ConnectionInfo *ci = data;
    if (gtk_entry_get_text_length(GTK_ENTRY(ci->entry)) > 0)
    {
        ci->response = TRUE;
        shutdown_loop(ci->loop);
    }
}

static void
connect_dialog_run(ConnectionInfo *ci)
{
    ci->loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(ci->loop);
}

static void
entry_icon_release_cb(GtkEntry* entry, gpointer data G_GNUC_UNUSED)
{
    gtk_entry_set_text(entry, "");
    gtk_widget_grab_focus(GTK_WIDGET(entry));
}

static void
entry_changed_cb(GtkEditable* entry, gpointer data)
{
    GtkButton *connect_button = data;
    gboolean rtl = (gtk_widget_get_direction(GTK_WIDGET(entry)) == GTK_TEXT_DIR_RTL);
    gboolean active = (gtk_entry_get_text_length(GTK_ENTRY(entry)) > 0);

    gtk_widget_set_sensitive(GTK_WIDGET(connect_button), active);

    g_object_set(entry,
                 "secondary-icon-name", active ? (rtl ? "edit-clear-rtl-symbolic" : "edit-clear-symbolic") : NULL,
                 "secondary-icon-activatable", active,
                 "secondary-icon-sensitive", active,
                 NULL);
}
/*
static gboolean
entry_focus_in_cb(GtkWidget *widget G_GNUC_UNUSED, GdkEvent *event G_GNUC_UNUSED, gpointer data)
{
    GtkRecentChooser *recent = data;
    gtk_recent_chooser_unselect_all(recent);
    return FALSE;
}
*/
static void
entry_activated_cb(GtkEntry *entry G_GNUC_UNUSED, gpointer data)
{
    ConnectionInfo *ci = data;
    if (gtk_entry_get_text_length(GTK_ENTRY(ci->entry)) > 0)
    {
        ci->response = TRUE;
        shutdown_loop(ci->loop);
    }
}

static void
recent_selection_changed_dialog_cb(GtkRecentChooser *chooser, gpointer data)
{
    GtkRecentInfo *info;
    GtkWidget *entry = data;
    const gchar *uri;

    info = gtk_recent_chooser_get_current_item(chooser);
    if (info == NULL)
        return;

    uri = gtk_recent_info_get_uri(info);
    g_return_if_fail(uri != NULL);

    gtk_entry_set_text(GTK_ENTRY(entry), uri);

    gtk_recent_info_unref(info);
}

static void
recent_item_activated_dialog_cb(GtkRecentChooser *chooser G_GNUC_UNUSED, gpointer data)
{
    ConnectionInfo *ci = data;
    ci->response = TRUE;
    shutdown_loop(ci->loop);
}

static void
make_label_small(GtkLabel* label)
{
    PangoAttrList* attributes = pango_attr_list_new();
    pango_attr_list_insert(attributes, pango_attr_scale_new(0.9));
    gtk_label_set_attributes(label, attributes);
    pango_attr_list_unref(attributes);
}

/**
* remote_viewer_connect_dialog
*
* @brief Opens connect dialog for remote viewer
*
* @param uri For returning the uri of chosen server, must be NULL
*
* @return TRUE if Connect or ENTER is pressed
* @return FALSE if Cancel is pressed or dialog is closed
*/

gboolean
remote_viewer_connect_dialog(GtkWindow *main_window, gchar **uri) {

    GtkWidget *window, /* *label,*/ *entry, *port_entry, *login_entry, *password_entry, /**recent,*/
            *connect_button/*, *cancel_button*/, *veil_image, *remember_checkbutton;
    GtkRecentFilter *rfilter;
    GtkBuilder *builder;
    gboolean active;

    ConnectionInfo ci = {
            FALSE,
            NULL,
            NULL
    };

    g_return_val_if_fail(uri && *uri == NULL, FALSE);

    /* Create the widgets */
    builder = virt_viewer_util_load_ui("remote-viewer-connect_veil.ui"); // remote-viewer-connect_veil.ui
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    window = GTK_WIDGET(gtk_builder_get_object(builder, "remote-viewer-connection-window"));
    gtk_window_set_transient_for(GTK_WINDOW(window), main_window);
    connect_button = GTK_WIDGET(gtk_builder_get_object(builder, "connect-button"));
    //cancel_button = GTK_WIDGET(gtk_builder_get_object(builder, "cancel-button"));
    //label = GTK_WIDGET(gtk_builder_get_object(builder, "example-label"));
    entry = ci.entry = GTK_WIDGET(gtk_builder_get_object(builder, "connection-address-entry"));

    //make_label_small(GTK_LABEL(label));

    active = (gtk_entry_get_text_length(GTK_ENTRY(ci.entry)) > 0);
    gtk_widget_set_sensitive(GTK_WIDGET(connect_button), active);

    // port entry
    port_entry = GTK_WIDGET(gtk_builder_get_object(builder, "connection-port-entry"));
    //recent = GTK_WIDGET(gtk_builder_get_object(builder, "recent-chooser"));

    rfilter = gtk_recent_filter_new();
    gtk_recent_filter_add_mime_type(rfilter, "application/x-spice");
    gtk_recent_filter_add_mime_type(rfilter, "application/x-vnc");
    gtk_recent_filter_add_mime_type(rfilter, "application/x-virt-viewer");
    //gtk_recent_chooser_set_filter(GTK_RECENT_CHOOSER(recent), rfilter);
    //gtk_recent_chooser_set_local_only(GTK_RECENT_CHOOSER(recent), FALSE);

    // Set veil image
    veil_image = GTK_WIDGET(gtk_builder_get_object(builder, "veil-image"));
    gtk_image_set_from_resource(veil_image, VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png");

    // password entry
    password_entry = GTK_WIDGET(gtk_builder_get_object(builder, "password-entry"));
    gchar *password_from_settings_file = read_from_settings_file("RemoteViewerConnect", "password");
    if(password_from_settings_file){
        gtk_entry_set_text(GTK_ENTRY(password_entry), password_from_settings_file);
    }

    // login entry
    login_entry = GTK_WIDGET(gtk_builder_get_object(builder, "login-entry"));
    gtk_widget_set_sensitive(GTK_ENTRY(login_entry), !opt_manual_mode);

    if (!opt_manual_mode) {
        gchar *user_from_settings_file = read_from_settings_file("RemoteViewerConnect", "username");
        if(user_from_settings_file){
            gtk_entry_set_text(GTK_ENTRY(login_entry), user_from_settings_file);
        }
    }

    // Remember check button
    remember_checkbutton = GTK_WIDGET(gtk_builder_get_object(builder, "remember-button"));

    // Signal - callbacks connections
    g_signal_connect(window, "key-press-event",
                     G_CALLBACK(key_pressed_cb), window);
    g_signal_connect(connect_button, "clicked",
                     G_CALLBACK(connect_button_clicked_cb), &ci);

    /* make sure that user_data is passed as first parameter */
    //g_signal_connect_swapped(cancel_button, "clicked",
    //                         G_CALLBACK(window_deleted_cb), &ci);
    g_signal_connect_swapped(window, "delete-event",
                             G_CALLBACK(window_deleted_cb), &ci);

    g_signal_connect(entry, "activate",
                     G_CALLBACK(entry_activated_cb), &ci);
    g_signal_connect(entry, "changed",
                     G_CALLBACK(entry_changed_cb), connect_button);
    g_signal_connect(entry, "icon-release",
                     G_CALLBACK(entry_icon_release_cb), entry);

    g_signal_connect(remember_checkbutton, "clicked",
            G_CALLBACK(on_remember_checkbutton_clicked), remember_checkbutton);

    g_signal_connect(G_OBJECT(port_entry), "insert-text", G_CALLBACK(on_insert_text_event), NULL);
    /*
    g_signal_connect(recent, "selection-changed",
                     G_CALLBACK(recent_selection_changed_dialog_cb), entry);
    g_signal_connect(recent, "item-activated",
                     G_CALLBACK(recent_item_activated_dialog_cb), &ci);
    g_signal_connect(entry, "focus-in-event",
                     G_CALLBACK(entry_focus_in_cb), recent);
    */

    /* show and wait for response */
    gtk_widget_show_all(window);

    connect_dialog_run(&ci);
    if (ci.response == TRUE) {
        //*uri = g_strdup(gtk_entry_get_text(GTK_ENTRY(entry)));
        // example // spice://192.168.11.110:5904
        *uri = g_strconcat("spice://", gtk_entry_get_text(GTK_ENTRY(entry)), ":",
                gtk_entry_get_text(GTK_ENTRY(port_entry)), NULL);
        g_strstrip(*uri);
        // credentials
        if(m_username)
            g_free(m_username);
        m_username = g_strdup(gtk_entry_get_text(GTK_ENTRY(login_entry)));
        g_strstrip(m_username);

        if(m_password)
            g_free(m_password);
        m_password = g_strdup(gtk_entry_get_text(GTK_ENTRY(password_entry)));
        g_strstrip(m_password);

        // save credentials to ini file if required (m_username  m_password)
        if(b_save_credentials_to_file){
            write_to_settings_file("RemoteViewerConnect", "username", m_username);
            write_to_settings_file("RemoteViewerConnect", "password", m_password);
        }

    } else {
        *uri = NULL;
    }

    g_object_unref(builder);
    gtk_widget_destroy(window);

    return ci.response;
}


/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
