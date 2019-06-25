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

// extern
extern gint64 currentVmId;
extern gboolean take_extern_credentials;

typedef enum
{
    VDI_RECEIVED_RESPONSE,
    VDI_WAITING_FOR_VM_DATA,
    VDI_WAITING_FOR_VM_FROM_POOL
} VdiClientState;

static GtkWidget *gtk_flow_box = NULL;
static GtkWidget *status_label = NULL;
static GtkWidget *main_vm_spinner = NULL;

static GArray *vmWidgetArray = NULL;

static gchar **urlPtr = NULL;
static gchar **passwordPtr = NULL;
static ConnectionInfo *ciPtr = NULL;

// functions declarations
static void on_vm_start_button_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data G_GNUC_UNUSED);

/////////////////////////////////// work functions//////////////////////////////////////
static void setVdiClientState(VdiClientState vdiClientState, const gchar *message, gboolean errorMessage)
{
    switch (vdiClientState) {
        case VDI_RECEIVED_RESPONSE: {
            if(main_vm_spinner)
                gtk_widget_hide (GTK_WIDGET(main_vm_spinner));
            if(gtk_flow_box)
                gtk_widget_set_sensitive (gtk_flow_box, TRUE);
            break;
        }

        case VDI_WAITING_FOR_VM_DATA: {
            if(main_vm_spinner)
                gtk_widget_show (GTK_WIDGET(main_vm_spinner));
            if(gtk_flow_box)
                gtk_widget_set_sensitive (gtk_flow_box, FALSE);
            break;
        }

        case VDI_WAITING_FOR_VM_FROM_POOL: {
            if(gtk_flow_box)
                gtk_widget_set_sensitive (gtk_flow_box, FALSE);
            break;
        }
    }

    // message
    if(status_label) {

        if(errorMessage) {
            gchar *finalMessage = g_strdup_printf("<span color=\"red\">%s</span>", message);
            gtk_label_set_markup(GTK_LABEL (status_label), finalMessage);
            g_free(finalMessage);

        } else{
            gtk_label_set_text(GTK_LABEL(status_label), message);
        }
    }
}

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

// find a machine widget by id
VdiVmWidget getVdiVmWidgetById(gint64 searchedVmId)
{
    VdiVmWidget searchedVdiVmWidget = {};
    int i;

    if(vmWidgetArray == NULL)
        return searchedVdiVmWidget;

    for(i = 0; i < vmWidgetArray->len; ++i){
        VdiVmWidget vdiVmWidget = g_array_index(vmWidgetArray, VdiVmWidget, i);

        gint64 curId = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(vdiVmWidget.vmStartButton), "vmId"));
        if(curId == searchedVmId){
            searchedVdiVmWidget = vdiVmWidget;
            break;
        }
    }

    return searchedVdiVmWidget;
}

static void shutdown_loop(GMainLoop *loop)
{
    if (g_main_loop_is_running(loop))
        g_main_loop_quit(loop);
}

//////////////////////////////// async task callbacks//////////////////////////////////////
static void onGetVdiVmDataFinished (GObject *source_object G_GNUC_UNUSED,
                                        GAsyncResult *res,
                                        gpointer user_data G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);

    GError *error;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("%s : FAIL \n", (char *)__func__);
        setVdiClientState(VDI_RECEIVED_RESPONSE, "Не удалось получить список пулов", TRUE);
        return;
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
        for(i = jsonArrayLength - 1; i >= 0; --i){

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
    setVdiClientState(VDI_RECEIVED_RESPONSE, "Получен список пулов", FALSE);
    //
    g_object_unref (parser);
    if(ptr_res)
        g_free(ptr_res);

    return;
}

static void onGetVmDFromPoolFinished(GObject *source_object G_GNUC_UNUSED,
                                         GAsyncResult *res,
                                         gpointer user_data G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);

    VdiVmWidget vdiVmWidget = getVdiVmWidgetById(currentVmId);
    enableSpinnerVisible(&vdiVmWidget, FALSE);

    GError *error;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("%s : FAIL \n", (char *)__func__);
        setVdiClientState(VDI_RECEIVED_RESPONSE, "Не удалось получить вм из пула", TRUE);
        return;
    }

    gchar *responseBodyStr = ptr_res; // example "[{\"id\":17,\"name\":\"sad\"}]"

    // parse  data  json
    JsonParser *parser = json_parser_new ();
    JsonObject *object = getJsonObject(parser, responseBodyStr);

    const gchar *vmHost = json_object_get_string_member(object, "host");
    gint64 vmPort = json_object_get_int_member(object, "port");
    const gchar *vmPassword = json_object_get_string_member(object, "password");
    printf("vmHost %s \n", vmHost);
    printf("vmPort %ld \n", vmPort);
    printf("vmPassword %s \n", vmPassword);

    free_memory_safely(urlPtr);
    *urlPtr = g_strdup_printf("spice://%s:%ld", vmHost, vmPort);
    g_strstrip(*urlPtr);
    free_memory_safely(passwordPtr);
    *passwordPtr = g_strdup(vmPassword);
    //
    setVdiClientState(VDI_RECEIVED_RESPONSE, "Получена вм из пула", FALSE);

    //stop event loop
    ciPtr->response = TRUE;
    ciPtr->dialogWindowResponse = GTK_RESPONSE_OK;
    shutdown_loop(ciPtr->loop);

    //
    g_object_unref (parser);
    if(ptr_res)
        g_free(ptr_res);

    return;
}

/////////////////////////////////// gui elements callbacks//////////////////////////////////////
static gboolean on_window_deleted_cb(ConnectionInfo *ci)
{
    printf("%s\n", (char *)__func__);
    ci->response = FALSE;
    ci->dialogWindowResponse = GTK_RESPONSE_CLOSE;
    shutdown_loop(ci->loop);
    return TRUE;
}

static void on_button_renew_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);
    cancellPendingRequests();
    unregisterAllVm();
    setVdiClientState(VDI_WAITING_FOR_VM_DATA, "Отправлен запрос на список пулов", FALSE);
    executeAsyncTask(getVdiVmData, onGetVdiVmDataFinished, NULL);
}

static void on_button_quit_clicked(GtkButton *button G_GNUC_UNUSED, gpointer data)
{
    printf("%s\n", (char *)__func__);
    ConnectionInfo *ci = data;
    ci->response = FALSE;
    ci->dialogWindowResponse = GTK_RESPONSE_CANCEL;
    shutdown_loop(ci->loop);
}

static void on_vm_start_button_clicked(GtkButton *button, gpointer data G_GNUC_UNUSED)
{
    //ConnectionInfo *ci = data;
    currentVmId = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(button), "vmId"));
    printf("on_vm_start_button_clicked %ld \n", currentVmId);
    // start machine
    setVdiClientState(VDI_WAITING_FOR_VM_FROM_POOL, "Отправлен запрос на получение вм из пула", FALSE);
    // start spinner on vm widget
    VdiVmWidget vdiVmWidget = getVdiVmWidgetById(currentVmId);
    enableSpinnerVisible(&vdiVmWidget, TRUE);
    // luanch thread
    executeAsyncTask(getVmDFromPool, onGetVmDFromPoolFinished, NULL);
}

/////////////////////////////////// main function
GtkResponseType vdi_manager_dialog(GtkWindow *main_window, gchar **uri, gchar **user G_GNUC_UNUSED, gchar **password)
{
    printf("vdi_manager_dialog url %s \n", *uri);
    urlPtr = uri;
    //userPtr = user;
    passwordPtr = password;

    GtkWidget *window, *button_renew, *button_quit, *vm_main_box;

    GtkBuilder *builder;

    ConnectionInfo ci = {
            FALSE,
            NULL,
            NULL,
            GTK_RESPONSE_CANCEL
    };
    ciPtr = &ci;

    take_extern_credentials = TRUE;

    /* Create the widgets */
    builder = virt_viewer_util_load_ui("vdi_manager_form.ui");
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    window = GTK_WIDGET(gtk_builder_get_object(builder, "vdi-main-window"));

    gtk_window_set_transient_for(GTK_WINDOW(window), main_window);
    gtk_window_set_default_size(GTK_WINDOW(window), 500, 500);

    button_renew = GTK_WIDGET(gtk_builder_get_object(builder, "button-renew"));
    button_quit = GTK_WIDGET(gtk_builder_get_object(builder, "button-quit"));
    vm_main_box = GTK_WIDGET(gtk_builder_get_object(builder, "vm_main_box"));
    status_label = GTK_WIDGET(gtk_builder_get_object(builder, "status_label"));

    gtk_flow_box = gtk_flow_box_new ();
    gtk_flow_box_set_max_children_per_line(GTK_FLOW_BOX(gtk_flow_box), 10);
    gtk_flow_box_set_selection_mode (GTK_FLOW_BOX(gtk_flow_box), GTK_SELECTION_NONE);
    gtk_flow_box_set_column_spacing (GTK_FLOW_BOX(gtk_flow_box), 6);
    gtk_box_pack_start(GTK_BOX(vm_main_box), gtk_flow_box, FALSE, TRUE, 0);

    main_vm_spinner = GTK_WIDGET(gtk_builder_get_object(builder, "main_vm_spinner"));

    // connects
    g_signal_connect_swapped(window, "delete-event", G_CALLBACK(on_window_deleted_cb), &ci);
    g_signal_connect(button_renew, "clicked", G_CALLBACK(on_button_renew_clicked), &ci);
    g_signal_connect(button_quit, "clicked", G_CALLBACK(on_button_quit_clicked), &ci);

    gtk_window_set_position (GTK_WINDOW(window), GTK_WIN_POS_CENTER);
    gtk_widget_show_all(window);
    
    // Пытаемся соединиться с vdi и получить список машин. Получив список машин нужно сгенерить
    // соответствующие кнопки  в скрол области.
    startSession();
    // get vm data
    executeAsyncTask(getVdiVmData, onGetVdiVmDataFinished, NULL);

    // event loop
    ci.loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(ci.loop);

    if (ci.response == FALSE)
        *uri = NULL;

    // clear
    stopSession();
    unregisterAllVm();
    g_object_unref(builder);
    gtk_widget_destroy(window);
    status_label = NULL;
    gtk_flow_box = NULL;
    main_vm_spinner = NULL;

    return ci.dialogWindowResponse;
}