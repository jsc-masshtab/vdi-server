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
 *
 * Edited by A. Solomin a.solomin@mashtab.org  2019
 */

#include <config.h>

#include "settingsfile.h"
#include "virt-viewer-session-spice.h"
#include "remote-viewer-connect.h"
#include "virt-viewer-util.h"
#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>

#include <ctype.h>

#include "async.h"
#include "vdi_api_session.h"
#include "jsonhandler.h"


extern gboolean opt_manual_mode;

static gboolean b_save_credentials_to_file = FALSE;

typedef enum
{
    AUTH_BEFORE_CONNECT
    // more coming

} AuthDialogState;

typedef struct
{
    GMainLoop *loop;

    GtkWidget *address_entry;
    GtkWidget *port_entry;
    GtkWidget *login_entry;
    GtkWidget *password_entry;

    GtkWidget *connect_button;
    GtkWidget *connect_spinner;
    GtkWidget *message_display_label;

    GtkWidget *ldap_checkbutton;
    GtkWidget *conn_to_prev_pool_checkbutton;

    GtkResponseType dialog_window_response;

    gboolean response;

    gchar *current_pool_id;

    gchar **uri;
    gchar **user;
    gchar **password;
    gchar **ip;
    gchar **port;

    gboolean *is_connect_to_prev_pool_ptr;

} RemoteViewerData;

static void
shutdown_loop(GMainLoop *loop)
{
    if (g_main_loop_is_running(loop))
        g_main_loop_quit(loop);
}

// set gui state
static void
set_auth_dialog_state(AuthDialogState auth_dialog_state, RemoteViewerData *ci)
{
    switch (auth_dialog_state) {
    case AUTH_BEFORE_CONNECT: {
        // stop connect spinner
        gtk_spinner_stop((GtkSpinner *)ci->connect_spinner);

        // enable connect button if address_entry is not empty
        if (gtk_entry_get_text_length(GTK_ENTRY(ci->address_entry)) > 0)
            gtk_widget_set_sensitive(GTK_WIDGET(ci->connect_button), TRUE);

        break;
    }
    }
}

// save data to ini file
static void
save_data_to_ini_file(RemoteViewerData *ci)
{
    if(b_save_credentials_to_file){
        const gchar *paramToFileGrpoup = opt_manual_mode ? "RemoteViewerConnectManual" : "RemoteViewerConnect";
        write_to_settings_file(paramToFileGrpoup, "ip", *ci->ip);
        write_to_settings_file(paramToFileGrpoup, "port", *ci->port);
        write_to_settings_file(paramToFileGrpoup, "username", *ci->user);
        write_to_settings_file(paramToFileGrpoup, "password", *ci->password);
    }
}

// set error message
static void
set_error_message_to_label(GtkLabel *label, const gchar *message)
{
    gchar *message_str = g_strdup_printf("<span color=\"red\">%s</span>", message);
    gtk_label_set_markup(label, message_str);
    g_free(message_str);
}

// get vm from pool callback
static void
on_get_vm_from_pool_finished(GObject *source_object G_GNUC_UNUSED,
                                         GAsyncResult *res,
                                         gpointer user_data G_GNUC_UNUSED)
{
    RemoteViewerData *ci = user_data;

    set_auth_dialog_state(AUTH_BEFORE_CONNECT, ci);

    GError *error = NULL;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        set_error_message_to_label(GTK_LABEL(ci->message_display_label), "Не удалось получить вм из пула");
        return;
    }

    VdiVmData *vdi_vm_data = ptr_res;
    // if port == 0 it means VDI server can not provide a vm
    if (vdi_vm_data->vm_port == 0) {
        const gchar *user_message = vdi_vm_data->message ? vdi_vm_data->message : "Не удалось получить вм из пула";
        set_error_message_to_label(GTK_LABEL(ci->message_display_label), user_message);
    } else {

        ci->response = TRUE;
        ci->dialog_window_response = GTK_RESPONSE_OK;

        *ci->ip = g_strdup(vdi_vm_data->vm_host);
        *ci->port = g_strdup_printf("%ld", vdi_vm_data->vm_port);
        *ci->uri = g_strconcat("spice://", *ci->ip, ":", *ci->port, NULL);
        g_strstrip(*ci->uri);
        *ci->user = NULL;
        *ci->password = g_strdup(vdi_vm_data->vm_password);

        // save data to ini file if required
        save_data_to_ini_file(ci);

        shutdown_loop(ci->loop);
    }
    //
    free_vdi_vm_data(vdi_vm_data);
}

// token fetch callback
static void
on_get_vdi_token_finished(GObject *source_object G_GNUC_UNUSED,
                                      GAsyncResult *res,
                                      gpointer user_data)
{
    RemoteViewerData *ci = user_data;

    GError *error = NULL;
    gboolean token_refreshed = g_task_propagate_boolean(G_TASK(res), &error);
    printf("%s: is_token_refreshed %i\n", (const char *)__func__, token_refreshed);

    set_auth_dialog_state(AUTH_BEFORE_CONNECT, ci);

    if (token_refreshed) {
        ci->response = TRUE;
        ci->dialog_window_response = GTK_RESPONSE_OK;

        *ci->ip = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->address_entry)));
        *ci->port = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->port_entry)));
        *ci->uri = g_strconcat("spice://", *ci->ip, ":", *ci->port, NULL);
        g_strstrip(*ci->uri);
        *ci->user = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->login_entry)));
        *ci->password = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->password_entry)));

        // save data to ini file if required
        save_data_to_ini_file(ci);

        shutdown_loop(ci->loop);
    } else {
        set_error_message_to_label(GTK_LABEL(ci->message_display_label), "Не удалось авторизоваться");
    }
}

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
    b_save_credentials_to_file = gtk_toggle_button_get_active((GtkToggleButton *)check_button);
}

static gboolean
window_deleted_cb(RemoteViewerData *ci)
{
    ci->response = FALSE;
    ci->dialog_window_response = GTK_RESPONSE_CLOSE;
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
    RemoteViewerData *ci = data;

    if (gtk_entry_get_text_length(GTK_ENTRY(ci->address_entry)) > 0) {
        // In manual mode we shudown the loop.
        if (opt_manual_mode) {
            ci->response = TRUE;
            ci->dialog_window_response = GTK_RESPONSE_OK;
            shutdown_loop(ci->loop);
        } else {
            // set credential for connection to VDI server
            const gchar *ip = gtk_entry_get_text(GTK_ENTRY(ci->address_entry));
            const gchar *port = gtk_entry_get_text(GTK_ENTRY(ci->port_entry));
            const gchar *user = gtk_entry_get_text(GTK_ENTRY(ci->login_entry));
            const gchar *password = gtk_entry_get_text(GTK_ENTRY(ci->password_entry));
            gboolean is_ldap = gtk_toggle_button_get_active((GtkToggleButton *)ci->ldap_checkbutton);
            set_vdi_credentials(user, password, ip, port, is_ldap);

            // clear message display
            gtk_label_set_text(GTK_LABEL(ci->message_display_label), " ");

            // disable connect button
            gtk_widget_set_sensitive(GTK_WIDGET(ci->connect_button), FALSE);

            // start connect spinner
            gtk_spinner_start((GtkSpinner *)ci->connect_spinner);

            // 2 варианта: подключиться к сразу к предыдущему пулу, либо перейти к vdi менеджеру для выбора пула
            *ci->is_connect_to_prev_pool_ptr  =
                    gtk_toggle_button_get_active((GtkToggleButton *)ci->conn_to_prev_pool_checkbutton);
            if (*ci->is_connect_to_prev_pool_ptr) {

                // get pool id from settings file
                const gchar *last_pool_id = read_from_settings_file("RemoteViewerConnect", "last_pool_id");
                if (!last_pool_id) {
                    set_error_message_to_label(GTK_LABEL(ci->message_display_label), "Нет информации о предыдущем пуле");
                    set_auth_dialog_state(AUTH_BEFORE_CONNECT, ci);
                    return;
                }
                set_current_pool_id("8ecb8dce-af2d-41b8-a4c2-ed36a3b77578");

                // start async task  get_vm_from_pool
                execute_async_task(get_vm_from_pool, on_get_vm_from_pool_finished, NULL, data);
            } else {
                // fetch token task starting
                execute_async_task(get_vdi_token, on_get_vdi_token_finished, NULL, data);
            }
        }
    }
}

static void
connect_dialog_run(RemoteViewerData *ci)
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

static void
entry_activated_cb(GtkEntry *entry G_GNUC_UNUSED, gpointer data)
{
    RemoteViewerData *ci = data;
    if (gtk_entry_get_text_length(GTK_ENTRY(ci->address_entry)) > 0)
    {
        ci->response = TRUE;
        shutdown_loop(ci->loop);
    }
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
// todo: порт передавать как число, а не строку
gboolean
remote_viewer_connect_dialog(gchar **uri, gchar **user, gchar **password,
                             gchar **ip, gchar **port, gboolean *is_connect_to_prev_pool)
{

    // set params save group
    const gchar *paramToFileGrpoup = opt_manual_mode ? "RemoteViewerConnectManual" : "RemoteViewerConnect";

    GtkWidget *window, *address_entry, *port_entry, *login_entry, *password_entry,
            *connect_button, *veil_image, *ldap_checkbutton, *remember_checkbutton;

    GtkBuilder *builder;
    gboolean active;

    RemoteViewerData ci;
    memset(&ci, 0, sizeof(RemoteViewerData)); // in C++ I would do: RemoteViewerData ci = {};
    ci.response = FALSE;
    ci.dialog_window_response = GTK_RESPONSE_CANCEL;
    // save pointers
    ci.uri = uri;
    ci.user = user;
    ci.password = password;
    ci.ip = ip;
    ci.port = port;
    ci.is_connect_to_prev_pool_ptr = is_connect_to_prev_pool;

    /* Create the widgets */
    builder = virt_viewer_util_load_ui("remote-viewer-connect_veil.ui");
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    window = GTK_WIDGET(gtk_builder_get_object(builder, "remote-viewer-connection-window"));
    gtk_window_set_resizable (GTK_WINDOW(window), FALSE);

    connect_button = ci.connect_button = GTK_WIDGET(gtk_builder_get_object(builder, "connect-button"));

    ci.connect_spinner = GTK_WIDGET(gtk_builder_get_object(builder, "connect-spinner"));

    ci.message_display_label = GTK_WIDGET(gtk_builder_get_object(builder, "message-display-label"));

    address_entry = ci.address_entry = GTK_WIDGET(gtk_builder_get_object(builder, "connection-address-entry"));
    const gchar *ip_str_from_config_file = read_from_settings_file(paramToFileGrpoup, "ip");
    if(ip_str_from_config_file)
        gtk_entry_set_text(GTK_ENTRY(address_entry), ip_str_from_config_file);

    active = (gtk_entry_get_text_length(GTK_ENTRY(address_entry)) > 0);
    gtk_widget_set_sensitive(GTK_WIDGET(connect_button), active);

    // port entry
    port_entry = ci.port_entry = GTK_WIDGET(gtk_builder_get_object(builder, "connection-port-entry"));
    const gchar *port_str_from_config_file = read_from_settings_file(paramToFileGrpoup, "port");
    if(port_str_from_config_file)
        gtk_entry_set_text(GTK_ENTRY(port_entry), port_str_from_config_file);

    // Set veil image
    veil_image = GTK_WIDGET(gtk_builder_get_object(builder, "veil-image"));
    gtk_image_set_from_resource((GtkImage *)veil_image,
            VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png");

    // password entry
    password_entry = ci.password_entry = GTK_WIDGET(gtk_builder_get_object(builder, "password-entry"));
    gchar *password_from_settings_file = read_from_settings_file(paramToFileGrpoup, "password");
    if(password_from_settings_file){
        gtk_entry_set_text(GTK_ENTRY(password_entry), password_from_settings_file);
    }

    // login entry
    login_entry = ci.login_entry = GTK_WIDGET(gtk_builder_get_object(builder, "login-entry"));
    gtk_widget_set_sensitive(login_entry, !opt_manual_mode);

    if (!opt_manual_mode) {
        gchar *user_from_settings_file = read_from_settings_file(paramToFileGrpoup, "username");
        if(user_from_settings_file){
            gtk_entry_set_text(GTK_ENTRY(login_entry), user_from_settings_file);
        }
    }

    // LDAP check button
    ci.ldap_checkbutton = ldap_checkbutton = GTK_WIDGET(gtk_builder_get_object(builder, "ldap-button"));

    // Connect to prev pool check button
    ci.conn_to_prev_pool_checkbutton = GTK_WIDGET(gtk_builder_get_object(builder, "connect-to-prev-button"));

    // Remember check button
    remember_checkbutton = GTK_WIDGET(gtk_builder_get_object(builder, "remember-button"));

    // Signal - callbacks connections
    g_signal_connect(window, "key-press-event", G_CALLBACK(key_pressed_cb), window);
    g_signal_connect(connect_button, "clicked", G_CALLBACK(connect_button_clicked_cb), &ci);
    g_signal_connect_swapped(window, "delete-event", G_CALLBACK(window_deleted_cb), &ci);
    g_signal_connect(address_entry, "changed", G_CALLBACK(entry_changed_cb), connect_button);
    g_signal_connect(address_entry, "icon-release", G_CALLBACK(entry_icon_release_cb), address_entry);
    g_signal_connect(remember_checkbutton, "clicked", G_CALLBACK(on_remember_checkbutton_clicked), remember_checkbutton);
    g_signal_connect(G_OBJECT(port_entry), "insert-text", G_CALLBACK(on_insert_text_event), NULL);

    /* show and wait for response */
    gtk_window_set_position ((GtkWindow *)window, GTK_WIN_POS_CENTER);
    gtk_widget_show_all(window);

    connect_dialog_run(&ci);

    g_object_unref(builder);
    gtk_widget_destroy(window);

    return ci.dialog_window_response;
}


