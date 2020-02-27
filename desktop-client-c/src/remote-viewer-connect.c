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
//#include "virt-viewer-session-spice.h"
#include "remote-viewer-connect.h"
#include "virt-viewer-util.h"
#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>

#include <ctype.h>

#include "async.h"
#include "jsonhandler.h"


extern gboolean opt_manual_mode;


typedef enum
{
    AUTH_GUI_BEFORE_CONNECT,
    AUTH_GUI_CONNECT_TRY_STARTED

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
    GtkWidget *header_label;

    GtkWidget *ldap_checkbutton;
    GtkWidget *conn_to_prev_pool_checkbutton;
    GtkWidget *remember_checkbutton;

    GtkWidget *remote_protocol_combobox;

    GtkResponseType dialog_window_response;

    gboolean response;

    gchar *current_pool_id;

    gchar **user;
    gchar **password;
    gchar **ip;
    gchar **port;

    gboolean *is_connect_to_prev_pool_ptr;

    gchar **vm_verbose_name;
    VdiVmRemoteProtocol *remote_protocol_type;

} RemoteViewerData;

// set gui state
static void
set_auth_dialog_state(AuthDialogState auth_dialog_state, RemoteViewerData *ci)
{
    switch (auth_dialog_state) {
    case AUTH_GUI_BEFORE_CONNECT: {
        // stop connect spinner
        gtk_spinner_stop((GtkSpinner *)ci->connect_spinner);

        // enable connect button if address_entry is not empty
        if (gtk_entry_get_text_length(GTK_ENTRY(ci->address_entry)) > 0)
            gtk_widget_set_sensitive(GTK_WIDGET(ci->connect_button), TRUE);

        break;
    }
    case AUTH_GUI_CONNECT_TRY_STARTED: {
        // clear message display
        gtk_label_set_text(GTK_LABEL(ci->message_display_label), " ");

        // disable connect button
        gtk_widget_set_sensitive(GTK_WIDGET(ci->connect_button), FALSE);

        // start connect spinner
        gtk_spinner_start((GtkSpinner *)ci->connect_spinner);
        break;
    }
    }
}

static void
get_data_from_gui(RemoteViewerData *ci)
{
    *ci->ip = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->address_entry)));
    *ci->port = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->port_entry)));
    *ci->user = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->login_entry)));
    *ci->password = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->password_entry)));
}

// save data to ini file
static void
save_data_to_ini_file(RemoteViewerData *ci)
{
    gboolean save_credentials_to_file = gtk_toggle_button_get_active((GtkToggleButton *)ci->remember_checkbutton);
    if (save_credentials_to_file) {

        const gchar *paramToFileGrpoup = opt_manual_mode ? "RemoteViewerConnectManual" : "RemoteViewerConnect";
        write_str_to_ini_file(paramToFileGrpoup, "ip", gtk_entry_get_text(GTK_ENTRY(ci->address_entry)));
        write_str_to_ini_file(paramToFileGrpoup, "port", gtk_entry_get_text(GTK_ENTRY(ci->port_entry)));
        write_str_to_ini_file(paramToFileGrpoup, "username", gtk_entry_get_text(GTK_ENTRY(ci->login_entry)));
        write_str_to_ini_file(paramToFileGrpoup, "password", gtk_entry_get_text(GTK_ENTRY(ci->password_entry)));

        gboolean is_ldap_btn_checked = gtk_toggle_button_get_active((GtkToggleButton *)ci->ldap_checkbutton);
        write_int_to_ini_file(paramToFileGrpoup, "is_ldap_btn_checked", is_ldap_btn_checked);
        gboolean is_conn_to_prev_pool_btn_checked =
                gtk_toggle_button_get_active((GtkToggleButton *)ci->conn_to_prev_pool_checkbutton);
        write_int_to_ini_file(paramToFileGrpoup, "is_conn_to_prev_pool_btn_checked", is_conn_to_prev_pool_btn_checked);

        if (ci->remote_protocol_combobox) {
            gint cur_remote_protocol_index = gtk_combo_box_get_active((GtkComboBox*)ci->remote_protocol_combobox);
            write_int_to_ini_file("General", "cur_remote_protocol_index", cur_remote_protocol_index);
        }
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

    set_auth_dialog_state(AUTH_GUI_BEFORE_CONNECT, ci);

    GError *error = NULL;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if (ptr_res == NULL) {
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
        *ci->user = NULL;
        *ci->password = g_strdup(vdi_vm_data->vm_password);
        *ci->vm_verbose_name = g_strdup(vdi_vm_data->vm_verbose_name);

        shutdown_loop(ci->loop);
    }

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

    set_auth_dialog_state(AUTH_GUI_BEFORE_CONNECT, ci);

    if (token_refreshed) {
        ci->response = TRUE;
        ci->dialog_window_response = GTK_RESPONSE_OK;
        get_data_from_gui(ci);

        shutdown_loop(ci->loop);
    } else {
        set_error_message_to_label(GTK_LABEL(ci->message_display_label), "Не удалось авторизоваться");
    }
}

// connect to VDI server
void connect_to_vdi_server(RemoteViewerData *ci)
{
    // set credential for connection to VDI server
    const gchar *ip = gtk_entry_get_text(GTK_ENTRY(ci->address_entry));
    const gchar *port = gtk_entry_get_text(GTK_ENTRY(ci->port_entry));
    const gchar *user = gtk_entry_get_text(GTK_ENTRY(ci->login_entry));
    const gchar *password = gtk_entry_get_text(GTK_ENTRY(ci->password_entry));
    gboolean is_ldap = gtk_toggle_button_get_active((GtkToggleButton *)ci->ldap_checkbutton);
    set_vdi_credentials(user, password, ip, port, is_ldap);

    set_auth_dialog_state(AUTH_GUI_CONNECT_TRY_STARTED, ci);

    // 2 варианта: подключиться к сразу к предыдущему пулу, либо перейти к vdi менеджеру для выбора пула
    *ci->is_connect_to_prev_pool_ptr  =
            gtk_toggle_button_get_active((GtkToggleButton *)ci->conn_to_prev_pool_checkbutton);
    if (*ci->is_connect_to_prev_pool_ptr) {

        // get pool id from settings file
        gchar *last_pool_id = read_str_from_ini_file("RemoteViewerConnect", "last_pool_id");
        if (!last_pool_id) {
            set_error_message_to_label(GTK_LABEL(ci->message_display_label), "Нет информации о предыдущем пуле");
            set_auth_dialog_state(AUTH_GUI_BEFORE_CONNECT, ci);
            return;
        }
        set_current_pool_id(last_pool_id);
        free_memory_safely(&last_pool_id);

        VdiVmRemoteProtocol remote_protocol = read_int_from_ini_file("General", "cur_remote_protocol_index");
        set_current_remote_protocol(remote_protocol);

        // start async task  get_vm_from_pool
        execute_async_task(get_vm_from_pool, on_get_vm_from_pool_finished, NULL, ci);
    } else {
        // fetch token task starting
        execute_async_task(get_vdi_token, on_get_vdi_token_finished, NULL, ci);
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
            get_data_from_gui(ci);

            gint cur_remote_protocol_index;
            // get remote protocol from gui
            if (ci->remote_protocol_combobox) {
                cur_remote_protocol_index = gtk_combo_box_get_active((GtkComboBox*)ci->remote_protocol_combobox);
                set_current_remote_protocol((VdiVmRemoteProtocol)cur_remote_protocol_index);
                *ci->remote_protocol_type = get_current_remote_protocol();
            }

            shutdown_loop(ci->loop);
        } else {
            connect_to_vdi_server(ci);
        }
    }
}

static void
connect_dialog_run(RemoteViewerData *ci)
{
    ci->loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(ci->loop);
    g_main_loop_unref(ci->loop);
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

//static void
//entry_activated_cb(GtkEntry *entry G_GNUC_UNUSED, gpointer data)
//{
//    RemoteViewerData *ci = data;
//    if (gtk_entry_get_text_length(GTK_ENTRY(ci->address_entry)) > 0)
//    {
//        ci->response = TRUE;
//        shutdown_loop(ci->loop);
//    }
//}

//static void
//make_label_small(GtkLabel* label)
//{
//    PangoAttrList* attributes = pango_attr_list_new();
//    pango_attr_list_insert(attributes, pango_attr_scale_new(0.9));
//    gtk_label_set_attributes(label, attributes);
//    pango_attr_list_unref(attributes);
//}

// В этом ёба режиме сразу автоматом пытаемся подрубиться к предыдущему пулу не дожидаясь действий пользователя.
// Поступаем так только один раз при старте приложения, чтоб у пользователя была возможносмть сменить
// логин пароль
static void fast_forward_connect_to_prev_pool_if_enabled(RemoteViewerData *ci)
{
    gboolean is_fastforward_conn_to_prev_pool =
            read_int_from_ini_file("RemoteViewerConnect", "is_fastforward_conn_to_prev_pool");

    static gboolean is_first_time = TRUE;
    if (is_fastforward_conn_to_prev_pool && is_first_time) {
        connect_to_vdi_server(ci);
        is_first_time = FALSE;
    }
}

/**
* remote_viewer_connect_dialog
*
* @brief Opens connect dialog for remote viewer
*/
// todo: порт передавать как число, а не строку
// todo: this function seems to be too big. its kinda bad
gboolean
remote_viewer_connect_dialog(gchar **user, gchar **password,
                             gchar **ip, gchar **port, gboolean *is_connect_to_prev_pool,
                             gchar **vm_verbose_name, VdiVmRemoteProtocol *remote_protocol_type)
{
    // set params save group
    const gchar *paramToFileGrpoup = opt_manual_mode ? "RemoteViewerConnectManual" : "RemoteViewerConnect";

    GtkWidget *window, *address_entry, *port_entry, *login_entry, *password_entry,
            *connect_button, *veil_image, *ldap_checkbutton, *remember_checkbutton;

    GtkBuilder *builder;
    gboolean active;

    RemoteViewerData ci;
    memset(&ci, 0, sizeof(RemoteViewerData));
    ci.response = FALSE;
    ci.dialog_window_response = GTK_RESPONSE_CLOSE;
    // save pointers
    ci.user = user;
    ci.password = password;
    ci.ip = ip;
    ci.port = port;
    ci.is_connect_to_prev_pool_ptr = is_connect_to_prev_pool;
    ci.vm_verbose_name = vm_verbose_name;
    ci.remote_protocol_type = remote_protocol_type;

    /* Create the widgets */
    builder = virt_viewer_util_load_ui("remote-viewer-connect_veil.ui");
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    window = GTK_WIDGET(gtk_builder_get_object(builder, "remote-viewer-connection-window"));
    gtk_window_set_resizable (GTK_WINDOW(window), FALSE);

    connect_button = ci.connect_button = GTK_WIDGET(gtk_builder_get_object(builder, "connect-button"));

    ci.connect_spinner = GTK_WIDGET(gtk_builder_get_object(builder, "connect-spinner"));

    ci.message_display_label = GTK_WIDGET(gtk_builder_get_object(builder, "message-display-label"));

    ci.header_label = GTK_WIDGET(gtk_builder_get_object(builder, "header-label"));
    gtk_label_set_text(GTK_LABEL(ci.header_label), VERSION);

    address_entry = ci.address_entry = GTK_WIDGET(gtk_builder_get_object(builder, "connection-address-entry"));
    gchar *ip_str_from_config_file = read_str_from_ini_file(paramToFileGrpoup, "ip");
    if (ip_str_from_config_file) {
        gtk_entry_set_text(GTK_ENTRY(address_entry), ip_str_from_config_file);
        free_memory_safely(&ip_str_from_config_file);
    }

    active = (gtk_entry_get_text_length(GTK_ENTRY(address_entry)) > 0);
    gtk_widget_set_sensitive(GTK_WIDGET(connect_button), active);

    // port entry
    port_entry = ci.port_entry = GTK_WIDGET(gtk_builder_get_object(builder, "connection-port-entry"));
    gchar *port_str_from_config_file = read_str_from_ini_file(paramToFileGrpoup, "port");
    if (port_str_from_config_file) {
        gtk_entry_set_text(GTK_ENTRY(port_entry), port_str_from_config_file);
        free_memory_safely(&port_str_from_config_file);
    }

    // Set veil image
    veil_image = GTK_WIDGET(gtk_builder_get_object(builder, "veil-image"));
    gtk_image_set_from_resource((GtkImage *)veil_image,
            VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png");

    // password entry
    password_entry = ci.password_entry = GTK_WIDGET(gtk_builder_get_object(builder, "password-entry"));
    gchar *password_from_settings_file = read_str_from_ini_file(paramToFileGrpoup, "password");
    if (password_from_settings_file) {
        gtk_entry_set_text(GTK_ENTRY(password_entry), password_from_settings_file);
        free_memory_safely(&password_from_settings_file);
    }

    // login entry
    login_entry = ci.login_entry = GTK_WIDGET(gtk_builder_get_object(builder, "login-entry"));
    //gtk_widget_set_sensitive(login_entry, !opt_manual_mode);

    //if (!opt_manual_mode) {
    gchar *user_from_settings_file = read_str_from_ini_file(paramToFileGrpoup, "username");
    if (user_from_settings_file) {
        gtk_entry_set_text(GTK_ENTRY(login_entry), user_from_settings_file);
        free_memory_safely(&user_from_settings_file);
    }
    //}

    // LDAP check button
    ci.ldap_checkbutton = ldap_checkbutton = GTK_WIDGET(gtk_builder_get_object(builder, "ldap-button"));
    gboolean is_ldap_btn_checked = read_int_from_ini_file("RemoteViewerConnect", "is_ldap_btn_checked");
    gtk_toggle_button_set_active((GtkToggleButton *)ci.ldap_checkbutton, is_ldap_btn_checked);
    gtk_widget_set_sensitive(ci.ldap_checkbutton, !opt_manual_mode);

    // Connect to prev pool check button
    ci.conn_to_prev_pool_checkbutton = GTK_WIDGET(gtk_builder_get_object(builder, "connect-to-prev-button"));
    gboolean is_conn_to_prev_pool_btn_checked =
            read_int_from_ini_file("RemoteViewerConnect", "is_conn_to_prev_pool_btn_checked");
    gtk_toggle_button_set_active((GtkToggleButton *)ci.conn_to_prev_pool_checkbutton, is_conn_to_prev_pool_btn_checked);
    gtk_widget_set_sensitive(ci.conn_to_prev_pool_checkbutton, !opt_manual_mode);

    // Remember check button
    ci.remember_checkbutton = remember_checkbutton = GTK_WIDGET(gtk_builder_get_object(builder, "remember-button"));

    // remote_protocol_type
    *remote_protocol_type = read_int_from_ini_file("General", "cur_remote_protocol_index");
    // protocol selection (we show it only in manual mode)
    ci.remote_protocol_combobox = GTK_WIDGET(gtk_builder_get_object(builder, "combobox-remote-protocol1"));
    if (!opt_manual_mode) {
        gtk_widget_destroy(ci.remote_protocol_combobox);
        ci.remote_protocol_combobox = NULL;
    }
    else
        gtk_combo_box_set_active((GtkComboBox*)ci.remote_protocol_combobox, (gint)(*remote_protocol_type));

    // Signal - callbacks connections
    g_signal_connect(window, "key-press-event", G_CALLBACK(key_pressed_cb), window);
    g_signal_connect(connect_button, "clicked", G_CALLBACK(connect_button_clicked_cb), &ci);
    g_signal_connect_swapped(window, "delete-event", G_CALLBACK(window_deleted_cb), &ci);
    g_signal_connect(address_entry, "changed", G_CALLBACK(entry_changed_cb), connect_button);
    g_signal_connect(address_entry, "icon-release", G_CALLBACK(entry_icon_release_cb), address_entry);
    g_signal_connect(G_OBJECT(port_entry), "insert-text", G_CALLBACK(on_insert_text_event), NULL);

    /* show and wait for response */
    gtk_window_set_position((GtkWindow *)window, GTK_WIN_POS_CENTER);
    gtk_widget_show_all(window);

    if (is_conn_to_prev_pool_btn_checked)
        fast_forward_connect_to_prev_pool_if_enabled(&ci);

    create_loop_and_launch(&ci.loop);

    // save data to ini file if required
    save_data_to_ini_file(&ci);

    g_object_unref(builder);
    gtk_widget_destroy(window);

    return ci.dialog_window_response;
}


