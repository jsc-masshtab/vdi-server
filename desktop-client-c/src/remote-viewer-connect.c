/*
 * Veil VDI thin client
 * Based on virt-viewer and freerdp
 *
 */

#include <config.h>

#include "settingsfile.h"
//#include "virt-viewer-session-spice.h"
#include "remote-viewer-connect.h"
#include "remote-viewer-util.h"
#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>

#include <ctype.h>

#include "async.h"
#include "jsonhandler.h"
#include "remote_viewer_start_settings.h"

extern gboolean opt_manual_mode;


typedef enum
{
    AUTH_GUI_DEFAULT_STATE,
    AUTH_GUI_CONNECT_TRY_STATE

} AuthDialogState;

typedef struct
{
    GMainLoop *loop;
    GtkResponseType dialog_window_response;

    // gui elements
    GtkWidget *login_entry;
    GtkWidget *password_entry;

    GtkWidget *window;
    GtkWidget *settings_button;
    GtkWidget *connect_button;
    GtkWidget *connect_spinner;
    GtkWidget *message_display_label;
    GtkWidget *header_label;

    // remote viewer settings
    ConnectSettingsData connect_settings_data;

    // pointers to data
    gchar *current_pool_id;

    gchar **user;
    gchar **password;

    gchar **domain;
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
    case AUTH_GUI_DEFAULT_STATE: {
        // stop connect spinner
        gtk_spinner_stop((GtkSpinner *)ci->connect_spinner);

        //// enable connect button if address_entry is not empty
        //if (gtk_entry_get_text_length(GTK_ENTRY(ci->address_entry)) > 0)
        gtk_widget_set_sensitive(GTK_WIDGET(ci->connect_button), TRUE);

        break;
    }
    case AUTH_GUI_CONNECT_TRY_STATE: {
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
// header-label
static void
set_data_from_gui_in_outer_pointers(RemoteViewerData *ci)
{
    *ci->domain = g_strdup(ci->connect_settings_data.domain);
    printf("%s *ci->domain %s\n", (const char *)__func__, *ci->domain);
    *ci->ip = g_strdup(ci->connect_settings_data.ip);
    *ci->port = g_strdup_printf("%i", ci->connect_settings_data.port);
    *ci->user = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->login_entry)));
    *ci->password = g_strdup(gtk_entry_get_text(GTK_ENTRY(ci->password_entry)));

    set_current_remote_protocol(ci->connect_settings_data.remote_protocol_type);
    *ci->remote_protocol_type = get_current_remote_protocol();
}

// save data to ini file
static void
save_data_to_ini_file(RemoteViewerData *ci)
{
    const gchar *paramToFileGrpoup = opt_manual_mode ? "RemoteViewerConnectManual" : "RemoteViewerConnect";
    write_str_to_ini_file(paramToFileGrpoup, "username", gtk_entry_get_text(GTK_ENTRY(ci->login_entry)));
    write_str_to_ini_file(paramToFileGrpoup, "password", gtk_entry_get_text(GTK_ENTRY(ci->password_entry)));
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

    set_auth_dialog_state(AUTH_GUI_DEFAULT_STATE, ci);

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

    set_auth_dialog_state(AUTH_GUI_DEFAULT_STATE, ci);

    if (token_refreshed) {
        ci->dialog_window_response = GTK_RESPONSE_OK;
        set_data_from_gui_in_outer_pointers(ci);

        // redis related actions upon succesful auhtorization
        execute_async_task(vdi_api_session_connect_to_redis_and_subscribe, NULL, NULL, NULL);

        shutdown_loop(ci->loop);
    } else {
        set_error_message_to_label(GTK_LABEL(ci->message_display_label), "Не удалось авторизоваться");
    }
}

// connect to VDI server
void connect_to_vdi_server(RemoteViewerData *ci)
{
    // set credential for connection to VDI server
    set_data_from_gui_in_outer_pointers(ci);
    set_vdi_credentials(*ci->user, *ci->password, *ci->ip, *ci->port, ci->connect_settings_data.is_ldap);

    set_auth_dialog_state(AUTH_GUI_CONNECT_TRY_STATE, ci);

    // 2 варианта: подключиться к сразу к предыдущему пулу, либо перейти к vdi менеджеру для выбора пула
    *ci->is_connect_to_prev_pool_ptr  = ci->connect_settings_data.is_connect_to_prev_pool;
    if (*ci->is_connect_to_prev_pool_ptr) {

        // get pool id from settings file
        gchar *last_pool_id = read_str_from_ini_file("RemoteViewerConnect", "last_pool_id");
        if (!last_pool_id) {
            set_error_message_to_label(GTK_LABEL(ci->message_display_label), "Нет информации о предыдущем пуле");
            set_auth_dialog_state(AUTH_GUI_DEFAULT_STATE, ci);
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

static gboolean
window_deleted_cb(RemoteViewerData *ci)
{
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
settings_button_clicked_cb(GtkButton *button G_GNUC_UNUSED, gpointer data)
{
    RemoteViewerData *ci = data;

    GtkResponseType res = remote_viewer_start_settings_dialog(&ci->connect_settings_data, GTK_WINDOW(ci->window));
    (void)res;
}

static gboolean
settings_button_link_clicked_cb(GtkLinkButton *button G_GNUC_UNUSED, gpointer user_data G_GNUC_UNUSED)
{
    return TRUE;
}

static void
connect_button_clicked_cb(GtkButton *button G_GNUC_UNUSED, gpointer data)
{
    RemoteViewerData *ci = data;

    if (strlen_safely(ci->connect_settings_data.ip) > 0) {
        // In manual mode we shudown the loop.
        if (opt_manual_mode) {
            ci->dialog_window_response = GTK_RESPONSE_OK;
            set_data_from_gui_in_outer_pointers(ci);

            shutdown_loop(ci->loop);
        } else {
            connect_to_vdi_server(ci);
        }
    }
}

static void
read_data_from_ini_file(RemoteViewerData *ci)
{
    // set params save group
    const gchar *paramToFileGrpoup = opt_manual_mode ? "RemoteViewerConnectManual" : "RemoteViewerConnect";

    //password
    gchar *password_from_settings_file = read_str_from_ini_file(paramToFileGrpoup, "password");
    if (password_from_settings_file) {
        gtk_entry_set_text(GTK_ENTRY(ci->password_entry), password_from_settings_file);
        free_memory_safely(&password_from_settings_file);
    }
    // login
    gchar *user_from_settings_file = read_str_from_ini_file(paramToFileGrpoup, "username");
    if (user_from_settings_file) {
        gtk_entry_set_text(GTK_ENTRY(ci->login_entry), user_from_settings_file);
        free_memory_safely(&user_from_settings_file);
    }

    fill_connect_settings_data_from_ini_file(&ci->connect_settings_data);
}

// В этом ёба режиме сразу автоматом пытаемся подрубиться к предыдущему пулу не дожидаясь действий пользователя.
// Поступаем так только один раз при старте приложения, чтоб у пользователя была возможносмть сменить
// логин пароль
static void fast_forward_connect_to_prev_pool_if_enabled(RemoteViewerData *ci)
{
    gboolean is_fastforward_conn_to_prev_pool =
            read_int_from_ini_file("RemoteViewerConnect", "is_conn_to_prev_pool_btn_checked");

    static gboolean is_first_time = TRUE;
    if (is_fastforward_conn_to_prev_pool && is_first_time && !opt_manual_mode) {
        connect_to_vdi_server(ci);
        is_first_time = FALSE;
    }
}

/**
* remote_viewer_connect_dialog
*
* @brief Opens connect dialog for remote viewer
*/
// todo: порт передавать как число, а не строку. Передавать структуру, а не 100500 аргументов
GtkResponseType
remote_viewer_connect_dialog(gchar **user, gchar **password, gchar **domain,
                             gchar **ip, gchar **port, gboolean *is_connect_to_prev_pool,
                             gchar **vm_verbose_name, VdiVmRemoteProtocol *remote_protocol_type)
{
    GtkBuilder *builder;

    RemoteViewerData ci;
    memset(&ci, 0, sizeof(RemoteViewerData));
    ci.dialog_window_response = GTK_RESPONSE_CLOSE;

    // save pointers
    ci.user = user;
    ci.password = password;
    ci.domain = domain;
    ci.ip = ip;
    ci.port = port;
    ci.is_connect_to_prev_pool_ptr = is_connect_to_prev_pool;
    ci.vm_verbose_name = vm_verbose_name;
    ci.remote_protocol_type = remote_protocol_type;

    /* Create the widgets */
    builder = remote_viewer_util_load_ui("remote-viewer-connect_veil.ui");
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    ci.window = GTK_WIDGET(gtk_builder_get_object(builder, "remote-viewer-connection-window"));

    ci.settings_button = GTK_WIDGET(gtk_builder_get_object(builder, "btn_settings"));
    ci.connect_button = GTK_WIDGET(gtk_builder_get_object(builder, "connect-button"));
    ci.connect_spinner = GTK_WIDGET(gtk_builder_get_object(builder, "connect-spinner"));
    ci.message_display_label = GTK_WIDGET(gtk_builder_get_object(builder, "message-display-label"));
    ci.header_label = GTK_WIDGET(gtk_builder_get_object(builder, "header-label"));
    gtk_label_set_text(GTK_LABEL(ci.header_label), VERSION);

//    // Set veil image
//    veil_image = GTK_WIDGET(gtk_builder_get_object(builder, "veil-image"));
//    gtk_image_set_from_resource((GtkImage *)veil_image,
//            VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png");

    // password entry
    ci.password_entry = GTK_WIDGET(gtk_builder_get_object(builder, "password-entry"));
    // login entry
    ci.login_entry = GTK_WIDGET(gtk_builder_get_object(builder, "login-entry"));

    // Signal - callbacks connections
    g_signal_connect(ci.window, "key-press-event", G_CALLBACK(key_pressed_cb), ci.window);
    g_signal_connect_swapped(ci.window, "delete-event", G_CALLBACK(window_deleted_cb), &ci);
    g_signal_connect(ci.settings_button, "clicked", G_CALLBACK(settings_button_clicked_cb), &ci);
    g_signal_connect(ci.settings_button, "activate-link", G_CALLBACK(settings_button_link_clicked_cb), &ci);
    g_signal_connect(ci.connect_button, "clicked", G_CALLBACK(connect_button_clicked_cb), &ci);

    // read ini file
    read_data_from_ini_file(&ci);

    /* show and wait for response */
    gtk_window_set_position(GTK_WINDOW(ci.window), GTK_WIN_POS_CENTER);
    //gtk_window_resize(GTK_WINDOW(window), 340, 340);

    gtk_widget_show_all(ci.window);
    gtk_window_set_resizable(GTK_WINDOW(ci.window), FALSE);

    // connect to the prev pool if requred
    fast_forward_connect_to_prev_pool_if_enabled(&ci);

    /// temp  redis try


    create_loop_and_launch(&ci.loop);

    // save data to ini file if required
    save_data_to_ini_file(&ci);

    g_object_unref(builder);
    gtk_widget_destroy(ci.window);
    free_memory_safely(&ci.connect_settings_data.ip);
    free_memory_safely(&ci.connect_settings_data.domain);

    return ci.dialog_window_response;
}


