/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2014 Red Hat, Inc.
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

#include <glib.h>
#include <glib/gi18n.h>

#include "virt-viewer-vm-connection.h"
#include "remote-viewer-util.h"

static void
treeview_row_activated_cb(GtkTreeView *treeview G_GNUC_UNUSED,
                          GtkTreePath *path G_GNUC_UNUSED,
                          GtkTreeViewColumn *col G_GNUC_UNUSED,
                          gpointer userdata)
{
    gtk_widget_activate(GTK_WIDGET(userdata));
}

static void
treeselection_changed_cb(GtkTreeSelection *selection, gpointer userdata)
{
    gtk_widget_set_sensitive(GTK_WIDGET(userdata),
                             gtk_tree_selection_count_selected_rows(selection) == 1);
}

gchar*
virt_viewer_vm_connection_choose_name_dialog(GtkWindow *main_window,
                                             GtkTreeModel *model,
                                             GError **error)
{
    GtkBuilder *vm_connection;
    GtkWidget *dialog;
    GtkButton *button_connect;
    GtkTreeView *treeview;
    GtkTreeSelection *selection;
    GtkTreeIter iter;
    int dialog_response;
    gchar *vm_name = NULL;

    g_return_val_if_fail(model != NULL, NULL);

    if (!gtk_tree_model_get_iter_first(model, &iter)) {
        g_set_error_literal(error,
                            VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                            _("No virtual machine found"));
        return NULL;
    }

    vm_connection = remote_viewer_util_load_ui("virt-viewer-vm-connection.ui");
    g_return_val_if_fail(vm_connection != NULL, NULL);

    dialog = GTK_WIDGET(gtk_builder_get_object(vm_connection, "vm-connection-dialog"));
    gtk_window_set_transient_for(GTK_WINDOW(dialog), main_window);
    button_connect = GTK_BUTTON(gtk_builder_get_object(vm_connection, "button-connect"));
    treeview = GTK_TREE_VIEW(gtk_builder_get_object(vm_connection, "treeview"));
    selection = GTK_TREE_SELECTION(gtk_builder_get_object(vm_connection, "treeview-selection"));
    gtk_tree_view_set_model(treeview, model);

    g_signal_connect(treeview, "row-activated",
                     G_CALLBACK(treeview_row_activated_cb), button_connect);
    g_signal_connect(selection, "changed",
                     G_CALLBACK(treeselection_changed_cb), button_connect);

    gtk_widget_show_all(dialog);
    dialog_response = gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_hide(dialog);

    if (dialog_response == GTK_RESPONSE_ACCEPT &&
        gtk_tree_selection_get_selected(selection, &model, &iter)) {
        gtk_tree_model_get(model, &iter, 0, &vm_name, -1);
    } else {
        g_set_error_literal(error,
                            VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_CANCELLED,
                            _("No virtual machine was chosen"));
    }

    gtk_widget_destroy(dialog);
    g_object_unref(G_OBJECT(vm_connection));

    return vm_name;
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
