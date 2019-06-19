//
// Created by Solomin on 13.06.19.
//

#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>
#include <libsoup/soup-session.h>

#include "virt-viewer-util.h"
#include "vdi_manager.h"
#include "vdi_api_session.h"
#include "vdi_vm_widget.h"

#define MAX_VM_NUMBER 150

static GtkWidget *gtk_flow_box = NULL;
static GArray *vmWidgetArray = NULL;

// extern
extern gint64 currentVmId;

// declarations
static void on_vm_start_button_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data G_GNUC_UNUSED);

/////////////////////////////////// work functions
static void unregisterAllVm()
{
    if(vmWidgetArray){
        int i;
        for(i = 0; i < vmWidgetArray->len; ++i){
            VdiVmWidget vdiVmWidget = g_array_index(vmWidgetArray, VdiVmWidget, i);
            destroyVdiVmWidget(&vdiVmWidget);
        }

        g_array_free (vmWidgetArray, TRUE);
        vmWidgetArray = NULL;
    }
}

static void registerVm(gint64 vmId, const gchar *vmName)
{
    // create array if required
    if(vmWidgetArray == NULL)
        vmWidgetArray = g_array_new (FALSE, FALSE, sizeof (VdiVmWidget));

    // add element
    VdiVmWidget vdiVmWidget = buildVmWidget(vmId, vmName, gtk_flow_box);
    g_array_append_val (vmWidgetArray, vdiVmWidget);
    // connect start button to callback
    g_signal_connect(vdiVmWidget.vmStartButton, "clicked", G_CALLBACK(on_vm_start_button_clicked), NULL);
}

static void shutdown_loop(GMainLoop *loop)
{
    if (g_main_loop_is_running(loop))
        g_main_loop_quit(loop);
}

//////////////////////////////// async task callbacks
static gboolean onGetVdiVmDataFinished (GObject *source_object G_GNUC_UNUSED,
                                        GAsyncResult *res,
                                        gpointer user_data G_GNUC_UNUSED)
{
    printf("onGetVdiVmDataFinished\n");

    GError *error;

    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("onGetVdiVmDataFinished: fail\n");
        return G_SOURCE_REMOVE;
    }

    gchar *responseBodyStr = ptr_res; // example "[{\"id\":17,\"name\":\"sad\"}]"
    // parse vm data  json
    JsonParser *parser = json_parser_new ();
    JsonArray *jsonArray = getJsonArray(parser, responseBodyStr);

    // prepare  vmWidgetArray
    unregisterAllVm();

    // parse json data and fill vmWidgetArray
    if(jsonArray){

        guint jsonArrayLength = MIN( json_array_get_length(jsonArray), MAX_VM_NUMBER );
        printf("Number of machines: %i\n", jsonArrayLength);

        int i;
        for(i = 0; i < jsonArrayLength; ++i){

            JsonNode *jsonNode = json_array_get_element (jsonArray, i);
            JsonObject *object = json_node_get_object (jsonNode);

            gint64 vmId = json_object_get_int_member(object, "id");
            const gchar *vmName = json_object_get_string_member(object, "name");
            //printf("vmId %i\n", vmId);
            //printf("vmName %s\n", vmName);

            registerVm(vmId, vmName);
        }
    }
    //
    g_object_unref (parser);
    if(ptr_res)
        g_free(ptr_res);

    return G_SOURCE_REMOVE;
}

static gboolean onGetVmDFromPoolFinished(GObject *source_object G_GNUC_UNUSED,
                                         GAsyncResult *res,
                                         gpointer user_data G_GNUC_UNUSED)
{
    printf("onGetVmDFromPoolFinished\n");

    GError *error;

    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("onGetVmDFromPoolFinished: fail\n");
        return G_SOURCE_REMOVE;
    }

    gchar *responseBodyStr = ptr_res; // example "[{\"id\":17,\"name\":\"sad\"}]"

    // parse  data  json
    JsonParser *parser = json_parser_new ();
    JsonObject *object = getJsonObject(parser, responseBodyStr);

    const gchar *vmHost = json_object_get_string_member(object, "host");
    gint64 vmPort = json_object_get_int_member(object, "port");
    const gchar *vmPassword = json_object_get_string_member(object, "password");
    printf("vmHost %s \n", vmHost);
    printf("vmPort %i \n", vmPort);
    printf("vmPassword %s \n", vmPassword);
    //
    g_object_unref (parser);
    if(ptr_res)
        g_free(ptr_res);

    return G_SOURCE_REMOVE;
}

////////////////////////////////////// gui elements callbacks
static gboolean on_window_deleted_cb(ConnectionInfo *ci)
{
    ci->response = FALSE;
    shutdown_loop(ci->loop);
    return TRUE;
}

static void on_button_renew_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data G_GNUC_UNUSED)
{
    printf("on_button_renew_clicked\n");
    unregisterAllVm();
    executeAsyncTask(getVdiVmData, onGetVdiVmDataFinished, NULL);
}

static void on_vm_start_button_clicked(GtkButton *button, gpointer data G_GNUC_UNUSED)
{
    //ConnectionInfo *ci = data;
    currentVmId = GPOINTER_TO_INT(g_object_get_data(button, "vmId"));
    printf("on_vm_start_button_clicked %i \n", currentVmId);
    // start machine
    executeAsyncTask(getVmDFromPool, onGetVmDFromPoolFinished, NULL);
}

/////////////////////////////////// main function
gboolean
vdi_manager_dialog(GtkWindow *main_window, gchar **uri){

    printf("vdi_manager_dialog url %s \n", *uri);

    GtkWidget *window, *button_renew, *button_quit, *vm_main_view_port, *vm_main_box;

    GtkBuilder *builder;

    ConnectionInfo ci = {
            FALSE,
            NULL,
            NULL
    };

    /* Create the widgets */
    builder = virt_viewer_util_load_ui("vdi_manager_form.ui");
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    window = GTK_WIDGET(gtk_builder_get_object(builder, "vdi-main-window"));
    gtk_window_set_transient_for(GTK_WINDOW(window), main_window);
    gtk_window_set_default_size(GTK_WINDOW(window), 500, 400);

    button_renew = GTK_WIDGET(gtk_builder_get_object(builder, "button-renew"));
    button_quit = GTK_WIDGET(gtk_builder_get_object(builder, "button-quit"));

    vm_main_box = GTK_WIDGET(gtk_builder_get_object(builder, "vm_main_box"));

    gtk_flow_box = gtk_flow_box_new ();
    gtk_flow_box_set_max_children_per_line(gtk_flow_box, 10);
    gtk_flow_box_set_selection_mode (gtk_flow_box, GTK_SELECTION_NONE);
    gtk_flow_box_set_column_spacing (gtk_flow_box, 6);
    gtk_box_pack_start(vm_main_box, gtk_flow_box, FALSE, TRUE, 0);

    // connects
    g_signal_connect_swapped(window, "delete-event", G_CALLBACK(on_window_deleted_cb), &ci);
    g_signal_connect(button_renew, "clicked", G_CALLBACK(on_button_renew_clicked), &ci);

    gtk_widget_show_all(window);

    // Пытаемся соединиться с vdi и получить список машин. Получив список машин нужно сгенерить
    // соответствующие кнопки  в скрол области. Показывать только первые скажем 200 машин?
    startSession();
    // get vm data
    executeAsyncTask(getVdiVmData, onGetVdiVmDataFinished, NULL);

    // event loop
    ci.loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(ci.loop);

    const gchar *ip_str = NULL; // ip выбранной на gui машины получить с api
    const gchar *port_str = NULL; // порт  получить с api

    // Сформировать url по которому подключемся
    if(*uri)
        g_free(*uri);
    if (ci.response == TRUE) {
        *uri = g_strconcat("spice://", ip_str, ":", port_str, NULL);
        g_strstrip(*uri);

    } else {
        *uri = NULL;
    }

    // clear
    stopSession();
    unregisterAllVm();
    g_object_unref(builder);
    gtk_widget_destroy(window);

    return ci.response;
}