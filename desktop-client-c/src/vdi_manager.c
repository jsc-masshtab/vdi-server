//
// Created by Solomin on 13.06.19.
//

#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>

#include "virt-viewer-util.h"
#include "vdi_manager.h"

static GMainLoop *mainLoop;

static void
shutdown_loop(GMainLoop *loop)
{
    if (g_main_loop_is_running(loop))
        g_main_loop_quit(loop);
}

static gboolean
window_deleted_cb()
{
    shutdown_loop(mainLoop);
    return TRUE;
}

gboolean
vdi_manager_dialog(GtkWindow *main_window){

    GtkWidget *window;
    GtkBuilder *builder;


    /* Create the widgets */
    builder = virt_viewer_util_load_ui("vdi_manager_from.ui"); // remote-viewer-connect_veil.ui
    g_return_val_if_fail(builder != NULL, GTK_RESPONSE_NONE);

    window = GTK_WIDGET(gtk_builder_get_object(builder, "vdi-manager-dialog"));
    gtk_window_set_transient_for(GTK_WINDOW(window), main_window);

    gtk_widget_show_all(window);

    mainLoop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(mainLoop);

    // connects
    g_signal_connect_swapped(window, "delete-event", G_CALLBACK(window_deleted_cb), NULL);
}