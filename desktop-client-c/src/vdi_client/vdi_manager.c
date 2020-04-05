//
// Created by Solomin on 13.06.19.
//

#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>
#include <cairo-features.h>
#include <libsoup/soup-session.h>

#include "remote-viewer-util.h"
#include "vdi_manager.h"
#include "vdi_ws_client.h"
#include "vdi_pool_widget.h"
#include "jsonhandler.h"
#include "settingsfile.h"

#define MAX_POOL_NUMBER 150


typedef enum
{
    VDI_RECEIVED_RESPONSE,
    VDI_WAITING_FOR_POOL_DATA,
    VDI_WAITING_FOR_VM_FROM_POOL
} VdiClientState;

typedef struct{

    GtkBuilder *builder;

    GtkWidget *window;
    GtkWidget *button_quit;
    GtkWidget *vm_main_box;
    GtkWidget *button_renew;
    GtkWidget *gtk_flow_box;
    GtkWidget *status_label;
    GtkWidget *main_vm_spinner;
    GtkWidget *image_label_vdi_online;
    GtkWidget *combobox_remote_protocol;

    GArray *pool_widgets_array;

    gchar **ip_ptr;
    gchar **port_ptr;
    gchar **password_ptr;
    gchar **vm_verbose_name_ptr;
    VdiVmRemoteProtocol *remote_protocol_type_ptr;

    ConnectionInfo ci;
} VdiManager;

// todo: Когда-нибудь в будущем избавлюсь от этих переменных уровня единицы трансляции.
// Но пока это никак не мешает, а лишь облегчает работу. Иначе надо жонглировать указателем между потоками.
static VdiManager vdi_manager;
static VdiWsClient vdi_ws_client;

// functions declarations
static void set_init_values(void);
static void set_vdi_client_state(VdiClientState vdi_client_state, const gchar *message, gboolean error_message);
static void refresh_vdi_pool_data_async(void);
static void unregister_all_pools(void);
static void register_pool(const gchar *pool_id, const gchar *pool_name, const gchar *os_type, const gchar *status);
static VdiPoolWidget get_vdi_pool_widget_by_id(const gchar *searched_id);

static void on_get_vdi_pool_data_finished(GObject *source_object, GAsyncResult *res, gpointer user_data);
static void on_get_vm_from_pool_finished(GObject *source_object, GAsyncResult *res, gpointer user_data);
static gboolean on_ws_data_from_vdi_received(gboolean is_vdi_online);

static gboolean on_window_deleted_cb(ConnectionInfo *ci);
static void on_button_renew_clicked(GtkButton *button, gpointer data);
static void on_button_quit_clicked(GtkButton *button, gpointer data);
static void on_vm_start_button_clicked(GtkButton *button , gpointer data);


/////////////////////////////////// work functions//////////////////////////////////////
//  set init values for  VdiManager structure
static void set_init_values()
{
    vdi_manager.builder = NULL;

    vdi_manager.window = NULL;
    vdi_manager.button_quit = NULL;
    vdi_manager.vm_main_box = NULL;
    vdi_manager.button_renew = NULL;
    vdi_manager.gtk_flow_box = NULL;
    vdi_manager.status_label = NULL;
    vdi_manager.main_vm_spinner = NULL;
    vdi_manager.image_label_vdi_online = NULL;
    vdi_manager.combobox_remote_protocol = NULL;

    vdi_manager.pool_widgets_array = NULL;

    vdi_manager.ip_ptr = NULL;
    vdi_manager.port_ptr = NULL;
    vdi_manager.password_ptr = NULL;
    vdi_manager.vm_verbose_name_ptr = NULL;
    vdi_manager.remote_protocol_type_ptr = NULL;
}

// Set GUI state
static void set_vdi_client_state(VdiClientState vdi_client_state, const gchar *message, gboolean error_message)
{
    gboolean controls_blocked = FALSE;

    switch (vdi_client_state) {
        case VDI_RECEIVED_RESPONSE: {
            if (vdi_manager.main_vm_spinner)
                gtk_widget_hide (GTK_WIDGET(vdi_manager.main_vm_spinner));
            controls_blocked = TRUE;
            break;
        }

        case VDI_WAITING_FOR_POOL_DATA: {
            if (vdi_manager.main_vm_spinner)
                gtk_widget_show (GTK_WIDGET(vdi_manager.main_vm_spinner));
            controls_blocked = FALSE;
            break;
        }

        case VDI_WAITING_FOR_VM_FROM_POOL: {
            controls_blocked = FALSE;
            break;
        }
    }

    // control widgets state
    if (vdi_manager.gtk_flow_box)
        gtk_widget_set_sensitive(vdi_manager.gtk_flow_box, controls_blocked);
    if (vdi_manager.button_renew)
        gtk_widget_set_sensitive(vdi_manager.button_renew, controls_blocked);
    if (vdi_manager.button_quit)
        gtk_widget_set_sensitive(vdi_manager.button_quit, controls_blocked);

    // message
    if (vdi_manager.status_label) {

        if (error_message) {
            gchar *finalMessage = g_strdup_printf("<span color=\"red\">%s</span>", message);
            gtk_label_set_markup(GTK_LABEL (vdi_manager.status_label), finalMessage);
            g_free(finalMessage);

        } else {
            gtk_label_set_text(GTK_LABEL(vdi_manager.status_label), message);
        }
    }
}
// start asynchronous task to get vm data from vdi
static void refresh_vdi_pool_data_async()
{
    set_vdi_client_state(VDI_WAITING_FOR_POOL_DATA, "Отправлен запрос на список пулов", FALSE);
    execute_async_task(get_vdi_pool_data, on_get_vdi_pool_data_finished, NULL, NULL);
}
// clear array of virtual machine widgets
static void unregister_all_pools()
{
    if (vdi_manager.pool_widgets_array) {
        guint i;
        for (i = 0; i < vdi_manager.pool_widgets_array->len; ++i) {
            VdiPoolWidget vdi_pool_widget = g_array_index(vdi_manager.pool_widgets_array, VdiPoolWidget, i);
            destroy_vdi_pool_widget(&vdi_pool_widget);
        }

        g_array_free(vdi_manager.pool_widgets_array, TRUE);
        vdi_manager.pool_widgets_array = NULL;
    }
}
// create virtual machine widget and add to GUI
static void register_pool(const gchar *pool_id, const gchar *pool_name, const gchar *os_type, const gchar *status)
{
    // create array if required
    if (vdi_manager.pool_widgets_array == NULL)
        vdi_manager.pool_widgets_array = g_array_new (FALSE, FALSE, sizeof (VdiPoolWidget));

    // add element
    VdiPoolWidget vdi_pool_widget = build_pool_widget(pool_id, pool_name, os_type, status, vdi_manager.gtk_flow_box);
    g_array_append_val (vdi_manager.pool_widgets_array, vdi_pool_widget);
    // connect start button to callback
    g_signal_connect(vdi_pool_widget.vm_start_button, "clicked", G_CALLBACK(on_vm_start_button_clicked), NULL);
}

// find a virtual machine widget by id
static VdiPoolWidget get_vdi_pool_widget_by_id(const gchar *searched_id)
{
    VdiPoolWidget searched_vdi_pool_widget;
    memset(&searched_vdi_pool_widget, 0, sizeof(VdiPoolWidget));
    guint i;

    if (vdi_manager.pool_widgets_array == NULL)
        return searched_vdi_pool_widget;

    for (i = 0; i < vdi_manager.pool_widgets_array->len; ++i) {
        VdiPoolWidget vdi_pool_widget = g_array_index(vdi_manager.pool_widgets_array, VdiPoolWidget, i);

        if (g_strcmp0(searched_id, vdi_pool_widget.pool_id) == 0) {
            searched_vdi_pool_widget = vdi_pool_widget;
            break;
        }
    }

    return searched_vdi_pool_widget;
}

//////////////////////////////// async task callbacks//////////////////////////////////////
// callback which is invoked when pool data request finished
static void on_get_vdi_pool_data_finished(GObject *source_object G_GNUC_UNUSED,
                                        GAsyncResult *res,
                                        gpointer user_data G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);

    GError *error;
    gpointer  ptr_res = g_task_propagate_pointer(G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Не удалось получить список пулов", TRUE);
        return;
    }

    gchar *response_body_str = ptr_res; // example "[{\"id\":17,\"name\":\"sad\"}]"
    printf("%s : %s\n", (const char *)__func__, response_body_str);

    // parse vm data  json
    JsonParser *parser = json_parser_new();
    JsonObject *root_object = get_root_json_object(parser, response_body_str);

    JsonNode *data_member = NULL;
    if (root_object)
        data_member = json_object_get_member(root_object, "data");

    JsonArray *jsonArray = NULL;
    if (data_member)
        jsonArray = json_node_get_array(data_member);

    if (!jsonArray) {
        g_object_unref(parser);
        g_free(ptr_res);
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Не удалось получить список пулов", TRUE);
        return;
    }

    // prepare  pool_widgets_array
    unregister_all_pools();

    // fill pool_widgets_array
    guint jsonArrayLength = MIN(json_array_get_length(jsonArray), MAX_POOL_NUMBER);
    printf("Number of vm pools: %i\n", jsonArrayLength);

    int i;
    for(i = (int)jsonArrayLength - 1; i >= 0; --i){

        JsonNode *jsonNode = json_array_get_element (jsonArray, (guint)i);
        JsonObject *object = json_node_get_object (jsonNode);

        const gchar *pool_id = json_object_get_string_member_safely(object, "id");
        const gchar *pool_name = json_object_get_string_member_safely(object, "name");
        const gchar *os_type = json_object_get_string_member_safely(object, "os_type");
        const gchar *status = json_object_get_string_member_safely(object, "status");
        //printf("os_type %s\n", os_type);
        //printf("pool_name %s\n", pool_name);
        register_pool(pool_id, pool_name, os_type, status);
    }

    //
    set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Получен список пулов", FALSE);
    //
    g_object_unref(parser);
    if(ptr_res)
        g_free(ptr_res);
}

// callback which is invoked when vm start request finished
static void on_get_vm_from_pool_finished(GObject *source_object G_GNUC_UNUSED,
                                         GAsyncResult *res,
                                         gpointer user_data G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);

    VdiPoolWidget vdi_pool_widget = get_vdi_pool_widget_by_id(get_current_pool_id());
    enable_spinner_visible(&vdi_pool_widget, FALSE);

    GError *error = NULL;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("%s : FAIL \n", (const char *)__func__);
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Не удалось получить вм из пула", TRUE);
        return;
    }

    VdiVmData *vdi_vm_data = ptr_res;

    // if port == 0 it means VDI server can not provide a vm
    if (vdi_vm_data->vm_port == 0) {
        const gchar *user_message = vdi_vm_data->message ? vdi_vm_data->message : "Не удалось получить вм из пула";
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, user_message, TRUE);
    } else {
        // save to settings file the last pool we connected to
        write_str_to_ini_file("RemoteViewerConnect", "last_pool_id", get_current_pool_id());

        free_memory_safely(vdi_manager.ip_ptr);
        *vdi_manager.ip_ptr = g_strdup(vdi_vm_data->vm_host);
        free_memory_safely(vdi_manager.port_ptr);
        *vdi_manager.port_ptr = g_strdup_printf("%ld", vdi_vm_data->vm_port);

        free_memory_safely(vdi_manager.password_ptr);
        *vdi_manager.password_ptr = g_strdup(vdi_vm_data->vm_password);

        free_memory_safely(vdi_manager.vm_verbose_name_ptr);
        *vdi_manager.vm_verbose_name_ptr = g_strdup(vdi_vm_data->vm_verbose_name);

        // get current remote protocol from gui
        *vdi_manager.remote_protocol_type_ptr =
            gtk_combo_box_get_active((GtkComboBox*)vdi_manager.combobox_remote_protocol);
        //
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Получена вм из пула", FALSE);

        //stop event loop
        vdi_manager.ci.response = TRUE;
        vdi_manager.ci.dialog_window_response = GTK_RESPONSE_OK;
        shutdown_loop(vdi_manager.ci.loop);
    }
    //
    free_vdi_vm_data(vdi_vm_data);
}

// ws data callback    "<span color=\"red\">%s</span>"
static gboolean on_ws_data_from_vdi_received(gboolean is_vdi_online)
{
    //printf("In %s :thread id = %lu\n", (const char *)__func__, pthread_self());
//    gchar *message;
//    if (vdi_manager.label_vdi_online){
//        if (is_vdi_online){
//            message = g_strdup("<span background=\"green\" color=\"white\">  Сервер доступен  </span>");
//        }
//        else{
//            message = g_strdup("<span background=\"red\" color=\"white\">  Сервер недоступен  </span>");
//        }

//        gtk_label_set_markup(GTK_LABEL (vdi_manager.label_vdi_online), message);
//        g_free(message);
//    }

    if (vdi_manager.image_label_vdi_online) {

        gchar *resource_path;
        if (is_vdi_online)
            resource_path = g_strdup(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/green_circle.png");
        else
            resource_path = g_strdup(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/red_circle.png");

        gtk_image_set_from_resource((GtkImage *)vdi_manager.image_label_vdi_online, resource_path);
        g_free(resource_path);
    }

    return FALSE;
}

/////////////////////////////////// gui elements callbacks//////////////////////////////////////
//// windows show callback
//static gboolean mapped_user_function(GtkWidget *widget,GdkEvent  *event, gpointer   user_data)
//{
//    printf("%s\n", (const char *)__func__);
//    return TRUE;
//}
// window close callback
static gboolean on_window_deleted_cb(ConnectionInfo *ci)
{
    printf("%s\n", (const char *)__func__);
    ci->response = FALSE;
    ci->dialog_window_response = GTK_RESPONSE_CLOSE;
    shutdown_loop(ci->loop);
    return TRUE;
}
// refresh button pressed callback
static void on_button_renew_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data G_GNUC_UNUSED) {

    printf("%s\n", (const char *)__func__);
    vdi_api_cancell_pending_requests();
    unregister_all_pools();
    refresh_vdi_pool_data_async();
}
// quit button pressed callback
static void on_button_quit_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data)
{
    printf("%s\n", (const char *)__func__);

    // logout
    vdi_api_session_logout();

    ConnectionInfo *ci = data;
    ci->response = FALSE;
    ci->dialog_window_response = GTK_RESPONSE_CANCEL;
    shutdown_loop(ci->loop);
}
// vm start button pressed callback
static void on_vm_start_button_clicked(GtkButton *button, gpointer data G_GNUC_UNUSED)
{
    const gchar *pool_id = g_object_get_data(G_OBJECT(button), "pool_id");
    set_current_pool_id(pool_id);
    printf("%s  %s\n", (const char *)__func__, pool_id);
    // start machine
    set_vdi_client_state(VDI_WAITING_FOR_VM_FROM_POOL, "Отправлен запрос на получение вм из пула", FALSE);
    // start spinner on vm widget
    VdiPoolWidget vdi_pool_widget = get_vdi_pool_widget_by_id(pool_id);
    enable_spinner_visible(&vdi_pool_widget, TRUE);

    // take from gui currect remote protocol
    gint remote_protocol_index = gtk_combo_box_get_active((GtkComboBox*)vdi_manager.combobox_remote_protocol);
    set_current_remote_protocol((VdiVmRemoteProtocol)remote_protocol_index);
    // execute task
    execute_async_task(get_vm_from_pool, on_get_vm_from_pool_finished, NULL, NULL);
}

static void
read_data_from_ini_file()
{
    gint cur_remote_protocol_index = read_int_from_ini_file("General", "cur_remote_protocol_index");
    gtk_combo_box_set_active((GtkComboBox*)vdi_manager.combobox_remote_protocol, cur_remote_protocol_index);
}

static void
save_data_to_ini_file()
{
    gint cur_remote_protocol_index =
            gtk_combo_box_get_active((GtkComboBox*)vdi_manager.combobox_remote_protocol);
    write_int_to_ini_file("General", "cur_remote_protocol_index", cur_remote_protocol_index);
}

/////////////////////////////////// main function
GtkResponseType vdi_manager_dialog(GtkWindow *main_window G_GNUC_UNUSED, gchar **ip, gchar **port,
                                   gchar **password, gchar **vm_verbose_name, VdiVmRemoteProtocol *remote_protocol_type)
{
    set_init_values();
    vdi_manager.ci.response = FALSE;
    vdi_manager.ci.loop = NULL;
    vdi_manager.ci.dialog_window_response = GTK_RESPONSE_CANCEL;
    vdi_manager.ip_ptr = ip;
    vdi_manager.port_ptr = port;
    vdi_manager.password_ptr = password;
    vdi_manager.vm_verbose_name_ptr = vm_verbose_name;
    vdi_manager.remote_protocol_type_ptr = remote_protocol_type;

    /* Create the widgets */
    vdi_manager.builder = remote_viewer_util_load_ui("vdi_manager_form.ui");
    g_return_val_if_fail(vdi_manager.builder != NULL, GTK_RESPONSE_NONE);

    vdi_manager.window = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "vdi-main-window"));
    vdi_manager.button_renew = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "button-renew"));

    vdi_manager.button_quit = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "button-quit"));
    vdi_manager.vm_main_box = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "vm_main_box"));
    vdi_manager.status_label = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "status_label"));

    vdi_manager.gtk_flow_box = gtk_flow_box_new();
    gtk_flow_box_set_max_children_per_line(GTK_FLOW_BOX(vdi_manager.gtk_flow_box), 10);
    gtk_flow_box_set_selection_mode (GTK_FLOW_BOX(vdi_manager.gtk_flow_box), GTK_SELECTION_NONE);
    gtk_flow_box_set_column_spacing (GTK_FLOW_BOX(vdi_manager.gtk_flow_box), 6);
    gtk_box_pack_start(GTK_BOX(vdi_manager.vm_main_box), vdi_manager.gtk_flow_box, FALSE, TRUE, 0);

    vdi_manager.main_vm_spinner = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "main_vm_spinner"));
    vdi_manager.combobox_remote_protocol =
            GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "combobox-remote-protocol"));

    vdi_manager.image_label_vdi_online = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "image_label_vdi_online"));

    // connects
    //g_signal_connect_swapped(vdi_manager.window, "map-event", G_CALLBACK(mapped_user_function), &vdi_manager.ci);
    g_signal_connect_swapped(vdi_manager.window, "delete-event", G_CALLBACK(on_window_deleted_cb), &vdi_manager.ci);
    g_signal_connect(vdi_manager.button_renew, "clicked", G_CALLBACK(on_button_renew_clicked), &vdi_manager.ci);
    g_signal_connect(vdi_manager.button_quit, "clicked", G_CALLBACK(on_button_quit_clicked), &vdi_manager.ci);

    read_data_from_ini_file();

    // show window
    gtk_window_set_position (GTK_WINDOW(vdi_manager.window), GTK_WIN_POS_CENTER);
    gtk_window_set_default_size(GTK_WINDOW(vdi_manager.window), 650, 500);
    gtk_widget_show_all(vdi_manager.window);

    // start polling if vdi is online
    start_vdi_ws_polling(&vdi_ws_client, get_vdi_ip(), get_vdi_port(), on_ws_data_from_vdi_received);
    // Пытаемся соединиться с vdi и получить список пулов. Получив список пулов нужно сгенерить
    // соответствующие кнопки  в скрол области.
    // get pool data
    refresh_vdi_pool_data_async();
    // event loop
    create_loop_and_launch(&vdi_manager.ci.loop);

    // clear
    vdi_api_cancell_pending_requests();
    stop_vdi_ws_polling(&vdi_ws_client);

    // save data to ini file
    save_data_to_ini_file();

    unregister_all_pools();
    g_object_unref(vdi_manager.builder);
    gtk_widget_destroy(vdi_manager.window);
    set_init_values();

    return vdi_manager.ci.dialog_window_response;
}
