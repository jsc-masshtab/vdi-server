//
// Created by Solomin on 13.06.19.
//

#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>
#include <libsoup/soup-session.h>

#include "virt-viewer-util.h"
#include "vdi_manager.h"
#include "vdi_api_session.h"
#include "vdi_pool_widget.h"
#include "jsonhandler.h"

#define MAX_VM_NUMBER 150

// extern
extern gboolean take_extern_credentials;

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

    GArray *pool_widgets_array;

    gchar **url_ptr;
    gchar **password_ptr;

    ConnectionInfo ci;
} VdiManager;

static VdiManager vdi_manager;

// functions declarations
static void set_init_values(VdiManager *vdi_manager_ptr);
static void set_vdi_client_state(VdiClientState vdi_client_state, const gchar *message, gboolean error_message);
static void refresh_vdi_pool_data_async();
static void unregister_all_pools();
static void register_pool(gint64 pool_id, const gchar *pool_name);
static VdiPoolWidget get_vdi_pool_widget_by_id(gint64 searched_id);
static void shutdown_loop(GMainLoop *loop);

static void on_get_vdi_pool_data_finished(GObject *source_object, GAsyncResult *res, gpointer user_data);
static void on_get_vm_from_pool_finished(GObject *source_object, GAsyncResult *res, gpointer user_data);

static gboolean on_window_deleted_cb(ConnectionInfo *ci);
static void on_button_renew_clicked(GtkButton *button, gpointer data);
static void on_button_quit_clicked(GtkButton *button, gpointer data);
static void on_vm_start_button_clicked(GtkButton *button , gpointer data);


/////////////////////////////////// work functions//////////////////////////////////////
//  set init values for  VdiManager structure
static void set_init_values(VdiManager *vdi_manager_ptr)
{
    vdi_manager_ptr->builder = NULL;

    vdi_manager_ptr->window = NULL;  
    vdi_manager_ptr->button_quit = NULL;
    vdi_manager_ptr->vm_main_box = NULL;
    vdi_manager_ptr->button_renew = NULL;
    vdi_manager_ptr->gtk_flow_box = NULL;
    vdi_manager_ptr->status_label = NULL;
    vdi_manager_ptr->main_vm_spinner = NULL;

    vdi_manager_ptr->pool_widgets_array = NULL;

    vdi_manager_ptr->url_ptr = NULL;
    vdi_manager_ptr->password_ptr = NULL;

    vdi_manager_ptr->ci.response = FALSE;
    vdi_manager_ptr->ci.loop = NULL;
    vdi_manager_ptr->ci.entry = NULL;
    vdi_manager_ptr->ci.dialog_window_response = GTK_RESPONSE_CANCEL;
}
// Set GUI state
static void set_vdi_client_state(VdiClientState vdi_client_state, const gchar *message, gboolean error_message)
{
    switch (vdi_client_state) {
        case VDI_RECEIVED_RESPONSE: {
            if (vdi_manager.main_vm_spinner)
                gtk_widget_hide (GTK_WIDGET(vdi_manager.main_vm_spinner));
            if (vdi_manager.gtk_flow_box)
                gtk_widget_set_sensitive (vdi_manager.gtk_flow_box, TRUE);
            if (vdi_manager.button_renew)
                gtk_widget_set_sensitive (vdi_manager.button_renew, TRUE);
            break;
        }

        case VDI_WAITING_FOR_POOL_DATA: {
            if (vdi_manager.main_vm_spinner)
                gtk_widget_show (GTK_WIDGET(vdi_manager.main_vm_spinner));
            if (vdi_manager.gtk_flow_box)
                gtk_widget_set_sensitive(vdi_manager.gtk_flow_box, FALSE);
            if (vdi_manager.button_renew)
                gtk_widget_set_sensitive(vdi_manager.button_renew, FALSE);
            break;
        }

        case VDI_WAITING_FOR_VM_FROM_POOL: {
            if (vdi_manager.gtk_flow_box)
                gtk_widget_set_sensitive(vdi_manager.gtk_flow_box, FALSE);
            if (vdi_manager.button_renew)
                gtk_widget_set_sensitive(vdi_manager.button_renew, FALSE);
            break;
        }
    }

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
    execute_async_task(get_vdi_vm_data, on_get_vdi_pool_data_finished, NULL);
}
// clear array of virtual machine widgets
static void unregister_all_pools()
{
    if (vdi_manager.pool_widgets_array) {
        int i;
        for (i = 0; i < vdi_manager.pool_widgets_array->len; ++i) {
            VdiPoolWidget vdi_pool_widget = g_array_index(vdi_manager.pool_widgets_array, VdiPoolWidget, i);
            destroy_vdi_pool_widget(&vdi_pool_widget);
        }

        g_array_free(vdi_manager.pool_widgets_array, TRUE);
        vdi_manager.pool_widgets_array = NULL;
    }
}
// create virtual machine widget and add to GUI
static void register_pool(gint64 pool_id, const gchar *pool_name)
{
    // create array if required
    if (vdi_manager.pool_widgets_array == NULL)
        vdi_manager.pool_widgets_array = g_array_new (FALSE, FALSE, sizeof (VdiPoolWidget));

    // add element
    VdiPoolWidget vdi_pool_widget = build_pool_widget(pool_id, pool_name, vdi_manager.gtk_flow_box);
    g_array_append_val (vdi_manager.pool_widgets_array, vdi_pool_widget);
    // connect start button to callback
    g_signal_connect(vdi_pool_widget.vm_start_button, "clicked", G_CALLBACK(on_vm_start_button_clicked), NULL);
}

// find a virtual machine widget by id
static VdiPoolWidget get_vdi_pool_widget_by_id(gint64 searched_id)
{
    VdiPoolWidget searchedVdiPoolWidget = {};
    int i;

    if (vdi_manager.pool_widgets_array == NULL)
        return searchedVdiPoolWidget;

    for (i = 0; i < vdi_manager.pool_widgets_array->len; ++i) {
        VdiPoolWidget vdi_pool_widget = g_array_index(vdi_manager.pool_widgets_array, VdiPoolWidget, i);

        gint64 curId = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(vdi_pool_widget.vm_start_button), "pool_id"));
        if(curId == searched_id){
            searchedVdiPoolWidget = vdi_pool_widget;
            break;
        }
    }

    return searchedVdiPoolWidget;
}
// stop GMainLoop
static void shutdown_loop(GMainLoop *loop)
{
    if (g_main_loop_is_running(loop))
        g_main_loop_quit(loop);
}

//////////////////////////////// async task callbacks//////////////////////////////////////
// callback which is invoked when pool data request finished
static void on_get_vdi_pool_data_finished (GObject *source_object G_GNUC_UNUSED,
                                        GAsyncResult *res,
                                        gpointer user_data G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);

    GError *error;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("%s : FAIL \n", (char *)__func__);
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Не удалось получить список пулов", TRUE);
        return;
    }

    gchar *response_body_str = ptr_res; // example "[{\"id\":17,\"name\":\"sad\"}]"
    // parse vm data  json
    JsonParser *parser = json_parser_new ();
    JsonArray *jsonArray = get_json_array(parser, response_body_str);

    // prepare  pool_widgets_array
    unregister_all_pools();

    // parse json data and fill pool_widgets_array
    if(jsonArray){

        guint jsonArrayLength = MIN( json_array_get_length(jsonArray), MAX_VM_NUMBER );
        printf("Number of vm pools: %i\n", jsonArrayLength);

        int i;
        for(i = jsonArrayLength - 1; i >= 0; --i){

            JsonNode *jsonNode = json_array_get_element (jsonArray, i);
            JsonObject *object = json_node_get_object (jsonNode);

            gint64 pool_id = json_object_get_int_member(object, "id");
            const gchar *pool_name = json_object_get_string_member(object, "name");
            //printf("pool_id %i\n", pool_id);
            //printf("pool_name %s\n", pool_name);
            register_pool(pool_id, pool_name);
        }
    }
    //
    set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Получен список пулов", FALSE);
    //
    g_object_unref (parser);
    if(ptr_res)
        g_free(ptr_res);
}
// callback which is invoked when vm start request finished
static void on_get_vm_from_pool_finished(GObject *source_object G_GNUC_UNUSED,
                                         GAsyncResult *res,
                                         gpointer user_data G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);

    VdiPoolWidget vdi_pool_widget = get_vdi_pool_widget_by_id(get_current_vm_id());
    enable_spinner_visible(&vdi_pool_widget, FALSE);

    GError *error;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("%s : FAIL \n", (char *)__func__);
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Не удалось получить вм из пула", TRUE);
        return;
    }

    gchar *response_body_str = ptr_res; // example "[{\"id\":17,\"name\":\"sad\"}]"

    // parse  data  json
    JsonParser *parser = json_parser_new ();
    JsonObject *object = get_json_object(parser, response_body_str);

    const gchar *vm_host = json_object_get_string_member_safely(object, "host");
    gint64 vm_port = json_object_get_int_member_safely(object, "port");
    const gchar *vm_password = json_object_get_string_member_safely(object, "password");
    const gchar *message = json_object_get_string_member_safely(object, "message");
    printf("vm_host %s \n", vm_host);
    printf("vm_port %ld \n", vm_port);
    printf("vm_password %s \n", vm_password);
    // if port == 0 it means VDI server can not provide a vm
    if (vm_port == 0) {
        const gchar *user_message = message ? message : "Не удалось получить вм из пула";
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, user_message, TRUE);
    } else {

        free_memory_safely(vdi_manager.url_ptr);
        *vdi_manager.url_ptr = g_strdup_printf("spice://%s:%ld", vm_host, vm_port);
        g_strstrip(*vdi_manager.url_ptr);
        free_memory_safely(vdi_manager.password_ptr);
        *vdi_manager.password_ptr = g_strdup(vm_password);
        //
        set_vdi_client_state(VDI_RECEIVED_RESPONSE, "Получена вм из пула", FALSE);

        //stop event loop
        vdi_manager.ci.response = TRUE;
        vdi_manager.ci.dialog_window_response = GTK_RESPONSE_OK;
        shutdown_loop(vdi_manager.ci.loop);
    }
    //
    g_object_unref (parser);
    if(ptr_res)
        g_free(ptr_res);
}

/////////////////////////////////// gui elements callbacks//////////////////////////////////////
// window close callback
static gboolean on_window_deleted_cb(ConnectionInfo *ci)
{
    printf("%s\n", (char *)__func__);
    ci->response = FALSE;
    ci->dialog_window_response = GTK_RESPONSE_CLOSE;
    shutdown_loop(ci->loop);
    return TRUE;
}
// refresh button pressed callback
static void on_button_renew_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data G_GNUC_UNUSED) {

    printf("%s\n", (char *) __func__);
    cancell_pending_requests();
    unregister_all_pools();
    refresh_vdi_pool_data_async();
}
// quit button pressed callback
static void on_button_quit_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data)
{
    printf("%s\n", (char *)__func__);
    ConnectionInfo *ci = data;
    ci->response = FALSE;
    ci->dialog_window_response = GTK_RESPONSE_CANCEL;
    shutdown_loop(ci->loop);
}
// vm start button pressed callback
static void on_vm_start_button_clicked(GtkButton *button, gpointer data G_GNUC_UNUSED)
{
    //ConnectionInfo *ci = data;
    set_current_vm_id( GPOINTER_TO_INT(g_object_get_data(G_OBJECT(button), "pool_id")) );
    printf("%s  %ld\n", (char *) __func__, get_current_vm_id());
    // start machine
    set_vdi_client_state(VDI_WAITING_FOR_VM_FROM_POOL, "Отправлен запрос на получение вм из пула", FALSE);
    // start spinner on vm widget
    VdiPoolWidget vdi_pool_widget = get_vdi_pool_widget_by_id(get_current_vm_id());
    enable_spinner_visible(&vdi_pool_widget, TRUE);
    // execute task
    execute_async_task(get_vm_from_pool, on_get_vm_from_pool_finished, NULL);
}

/////////////////////////////////// main function
GtkResponseType vdi_manager_dialog(GtkWindow *main_window, gchar **uri, gchar **user G_GNUC_UNUSED, gchar **password)
{
    printf("vdi_manager_dialog url %s \n", *uri);
    set_init_values(&vdi_manager);
    vdi_manager.url_ptr = uri;
    vdi_manager.password_ptr = password;
    take_extern_credentials = TRUE;

    /* Create the widgets */
    vdi_manager.builder = virt_viewer_util_load_ui("vdi_manager_form.ui");
    g_return_val_if_fail(vdi_manager.builder != NULL, GTK_RESPONSE_NONE);

    vdi_manager.window = GTK_WIDGET(gtk_builder_get_object(vdi_manager.builder, "vdi-main-window"));

    //gtk_window_set_transient_for(GTK_WINDOW(vdi_manager.window), main_window);
    gtk_window_set_default_size(GTK_WINDOW(vdi_manager.window), 500, 500);

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

    // connects
    g_signal_connect_swapped(vdi_manager.window, "delete-event", G_CALLBACK(on_window_deleted_cb), &vdi_manager.ci);
    g_signal_connect(vdi_manager.button_renew, "clicked", G_CALLBACK(on_button_renew_clicked), &vdi_manager.ci);
    g_signal_connect(vdi_manager.button_quit, "clicked", G_CALLBACK(on_button_quit_clicked), &vdi_manager.ci);

    gtk_window_set_position (GTK_WINDOW(vdi_manager.window), GTK_WIN_POS_CENTER);
    gtk_widget_show_all(vdi_manager.window);
    
    // Пытаемся соединиться с vdi и получить список пулов. Получив список пулов нужно сгенерить
    // соответствующие кнопки  в скрол области.
    // get pool data
    refresh_vdi_pool_data_async();

    // event loop
    vdi_manager.ci.loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(vdi_manager.ci.loop);

    if (vdi_manager.ci.response == FALSE)
        *uri = NULL;

    // clear
    cancell_pending_requests();
    unregister_all_pools();
    g_object_unref(vdi_manager.builder);
    gtk_widget_destroy(vdi_manager.window);

    vdi_manager.button_renew = NULL;
    vdi_manager.gtk_flow_box = NULL;
    vdi_manager.status_label = NULL;
    vdi_manager.main_vm_spinner = NULL;

    return vdi_manager.ci.dialog_window_response;
}
