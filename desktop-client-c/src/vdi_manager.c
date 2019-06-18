//
// Created by Solomin on 13.06.19.
//

#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>
#include <libsoup/soup-session.h>

#include "virt-viewer-util.h"
#include "vdi_manager.h"
#include "vdi_api_session.h"

#define MAX_VM_NUMBER 150
//static GMainLoop *mainLoop;


static void shutdown_loop(GMainLoop *loop)
{
    if (g_main_loop_is_running(loop))
        g_main_loop_quit(loop);
}

static gboolean on_window_deleted_cb(ConnectionInfo *ci)
{
    ci->response = FALSE;
    shutdown_loop(ci->loop);
    return TRUE;
}

static registerVM(gint64 vmId, const gchar *vmName)
{

}

static void on_vm_chosen(GtkButton *button G_GNUC_UNUSED, gpointer data){

    ConnectionInfo *ci = data;
};

static gboolean
onGetVdiVmDataFinished (GObject *source_object G_GNUC_UNUSED,
           GAsyncResult *res,
           gpointer user_data G_GNUC_UNUSED)
{
    printf("onGetVdiVmDataFinished\n");
    //printf("got_value thread %i \n", g_thread_self());

    GError *error;
    //G_TASK (res)->result_set;
    gpointer  ptr_res =  g_task_propagate_pointer (G_TASK (res), &error); // take ownership
    if(ptr_res == NULL){
        printf("onGetVdiVmDataFinished: fail\n");
        return G_SOURCE_REMOVE;
    }

    gchar *responseBodyStr = ptr_res; // example "[{\"id\":17,\"name\":\"sad\"}]"
    // parse vm data  json
    JsonParser *parser = json_parser_new ();
    JsonArray *jsonArray = getJsonArray(parser, responseBodyStr);

    if(jsonArray){
        // parse and construct gui
        guint jsonArrayLength = MIN( json_array_get_length(jsonArray), MAX_VM_NUMBER );
        printf("Number of machines: %i\n", jsonArrayLength);
        int i;
        for(i = 0; i < jsonArrayLength; ++i){

            JsonNode *jsonNode = json_array_get_element (jsonArray, i);
            JsonObject *object = json_node_get_object (jsonNode);

            gint64 vmId = json_object_get_int_member(object, "id");
            const gchar *vmName = json_object_get_string_member(object, "name");
            printf("vmId %i\n", vmId);
            printf("vmName %s\n", vmName);

            registerVM(vmId, vmName);
        }
    }

    g_object_unref (parser);
    if(ptr_res)
        g_free(ptr_res);

    return G_SOURCE_REMOVE;
}

static gboolean onGetVmDFromPoolFinished(GObject *source_object G_GNUC_UNUSED,
                                         GAsyncResult *res,
                                         gpointer user_data G_GNUC_UNUSED)
{

}

gboolean
vdi_manager_dialog(GtkWindow *main_window, gchar **uri){

    printf(*uri); printf("\n");

    GtkWidget *window, *button_renew, *button_quit;

    GtkBuilder *builder;

    ConnectionInfo ci = {
            FALSE,
            NULL,
            NULL
    };

    /* Create the widgets */
    builder = virt_viewer_util_load_ui("vdi_manager_form.ui"); // remote-viewer-connect_veil.ui
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    window = GTK_WIDGET(gtk_builder_get_object(builder, "vdi-main-window"));
    gtk_window_set_transient_for(GTK_WINDOW(window), main_window);
    gtk_window_set_default_size(GTK_WINDOW(window), 500, 400);

    button_renew = GTK_WIDGET(gtk_builder_get_object(builder, "button-renew"));

    button_quit = GTK_WIDGET(gtk_builder_get_object(builder, "button-quit"));

    // connects
    g_signal_connect_swapped(window, "delete-event", G_CALLBACK(on_window_deleted_cb), &ci);

    gtk_widget_show_all(window);


    // Пытаемся соединиться с vdi и получить список машин. Получив список машин нужно сгенерить
    // соответствующие кнопки  в скрол области. Показывать только первые скажем 200 машин?
    // Start session here
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
    g_object_unref(builder);
    gtk_widget_destroy(window);

    return ci.response;
}