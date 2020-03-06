/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2016 Red Hat, Inc.
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

#include "virt-viewer-file-transfer-dialog.h"
#include "remote-viewer-util.h"
#include <glib/gi18n.h>

struct _VirtViewerFileTransferDialogPrivate
{
    GSList *file_transfers;
    GSList *failed;
    guint timer_show_src;
    guint timer_hide_src;
    guint num_files;
    guint64 total_transfer_size;
    guint64 completed_transfer_size;
    GtkWidget *transfer_summary;
    GtkWidget *progressbar;
};

G_DEFINE_TYPE_WITH_PRIVATE(VirtViewerFileTransferDialog, virt_viewer_file_transfer_dialog, GTK_TYPE_DIALOG)

#define FILE_TRANSFER_DIALOG_PRIVATE(o) \
        (G_TYPE_INSTANCE_GET_PRIVATE((o), VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG, VirtViewerFileTransferDialogPrivate))


static void
virt_viewer_file_transfer_dialog_dispose(GObject *object)
{
    VirtViewerFileTransferDialog *self = VIRT_VIEWER_FILE_TRANSFER_DIALOG(object);

    if (self->priv->file_transfers) {
        g_slist_free_full(self->priv->file_transfers, g_object_unref);
        self->priv->file_transfers = NULL;
    }

    G_OBJECT_CLASS(virt_viewer_file_transfer_dialog_parent_class)->dispose(object);
}

static void
virt_viewer_file_transfer_dialog_class_init(VirtViewerFileTransferDialogClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS(klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS(klass);

    gtk_widget_class_set_template_from_resource(widget_class,
                                                VIRT_VIEWER_RESOURCE_PREFIX "/ui/virt-viewer-file-transfer-dialog.ui");
    gtk_widget_class_bind_template_child_private(widget_class,
                                                 VirtViewerFileTransferDialog,
                                                 transfer_summary);
    gtk_widget_class_bind_template_child_private(widget_class,
                                                 VirtViewerFileTransferDialog,
                                                 progressbar);

    object_class->dispose = virt_viewer_file_transfer_dialog_dispose;
}

static void
dialog_response(GtkDialog *dialog,
                gint response_id,
                gpointer user_data G_GNUC_UNUSED)
{
    VirtViewerFileTransferDialog *self = VIRT_VIEWER_FILE_TRANSFER_DIALOG(dialog);
    GSList *slist;

    switch (response_id) {
        case GTK_RESPONSE_CANCEL:
            /* cancel all current tasks */
            for (slist = self->priv->file_transfers; slist != NULL; slist = g_slist_next(slist)) {
                spice_file_transfer_task_cancel(SPICE_FILE_TRANSFER_TASK(slist->data));
            }
            self->priv->num_files = 0;
            self->priv->total_transfer_size = 0;
            self->priv->completed_transfer_size = 0;
            break;
        case GTK_RESPONSE_DELETE_EVENT:
            /* silently ignore */
            break;
        default:
            g_warn_if_reached();
    }
}

static gboolean delete_event(GtkWidget *widget,
                             GdkEvent *event G_GNUC_UNUSED,
                             gpointer user_data G_GNUC_UNUSED)
{
    /* don't allow window to be deleted, just process the response signal,
     * which may result in the window being hidden */
    gtk_dialog_response(GTK_DIALOG(widget), GTK_RESPONSE_CANCEL);
    return TRUE;
}

static void
virt_viewer_file_transfer_dialog_init(VirtViewerFileTransferDialog *self)
{
    gtk_widget_init_template(GTK_WIDGET(self));

    self->priv = FILE_TRANSFER_DIALOG_PRIVATE(self);

    g_signal_connect(self, "response", G_CALLBACK(dialog_response), NULL);
    g_signal_connect(self, "delete-event", G_CALLBACK(delete_event), NULL);
}

VirtViewerFileTransferDialog *
virt_viewer_file_transfer_dialog_new(GtkWindow *parent)
{
    return g_object_new(VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG,
                        "title", _("File Transfers"),
                        "transient-for", parent,
                        "resizable", FALSE,
                        NULL);
}

static void update_global_progress(VirtViewerFileTransferDialog *self)
{
    GSList *slist;
    guint64 transferred = 0;
    gchar *message = NULL;
    guint n_files = 0;
    gdouble fraction = 1.0;

    for (slist = self->priv->file_transfers; slist != NULL; slist = g_slist_next(slist)) {
        SpiceFileTransferTask *task = slist->data;
        transferred += spice_file_transfer_task_get_transferred_bytes(task);
        n_files++;
    }

    if (n_files > 0) {
        transferred += self->priv->completed_transfer_size;
        fraction = (gdouble)transferred / self->priv->total_transfer_size;
    }

    if (self->priv->num_files == 1) {
        message = g_strdup(_("Transferring 1 file..."));
    } else {
        message = g_strdup_printf(ngettext("Transferring %d file of %d...",
                                           "Transferring %d files of %d...", n_files),
                                  n_files, self->priv->num_files);
    }
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(self->priv->progressbar), fraction);
    gtk_label_set_text(GTK_LABEL(self->priv->transfer_summary), message);
    g_free(message);
}

static void task_progress_notify(GObject *object G_GNUC_UNUSED,
                                 GParamSpec *pspec G_GNUC_UNUSED,
                                 gpointer user_data)
{
    VirtViewerFileTransferDialog *self = VIRT_VIEWER_FILE_TRANSFER_DIALOG(user_data);

    update_global_progress(self);
}

static void task_total_bytes_notify(GObject *object,
                                    GParamSpec *pspec G_GNUC_UNUSED,
                                    gpointer user_data)
{
    VirtViewerFileTransferDialog *self = VIRT_VIEWER_FILE_TRANSFER_DIALOG(user_data);
    SpiceFileTransferTask *task = SPICE_FILE_TRANSFER_TASK(object);

    self->priv->total_transfer_size += spice_file_transfer_task_get_total_bytes(task);
    self->priv->num_files++;
    update_global_progress(self);
}


static void
error_dialog_response(GtkDialog *dialog,
                      gint response_id G_GNUC_UNUSED,
                      gpointer user_data G_GNUC_UNUSED)
{
    gtk_widget_destroy(GTK_WIDGET(dialog));
}

static gboolean hide_transfer_dialog(gpointer data)
{
    VirtViewerFileTransferDialog *self = data;
    gtk_widget_hide(GTK_WIDGET(self));
    gtk_dialog_set_response_sensitive(GTK_DIALOG(self),
                                      GTK_RESPONSE_CANCEL, FALSE);
    self->priv->timer_hide_src = 0;

    /* When all ongoing file transfers are finished, show errors */
    if (self->priv->failed) {
        GSList *sl;
        GString *msg = g_string_new("");
        GtkWidget *dialog;

        for (sl = self->priv->failed; sl != NULL; sl = g_slist_next(sl)) {
            SpiceFileTransferTask *failed_task = sl->data;
            gchar *filename = spice_file_transfer_task_get_filename(failed_task);
            if (filename == NULL) {
                guint id;

                g_object_get(failed_task, "id", &id, NULL);
                g_warning("Unable to get filename of failed transfer");
                filename = g_strdup_printf("(task #%u)", id);
            }

            g_string_append_printf(msg, "\n%s", filename);
            g_free(filename);
        }
        g_slist_free_full(self->priv->failed, g_object_unref);
        self->priv->failed = NULL;

        dialog = gtk_message_dialog_new(GTK_WINDOW(self), 0, GTK_MESSAGE_ERROR,
                                        GTK_BUTTONS_OK,
                                        _("An error caused the following file transfers to fail:%s"),
                                        msg->str);
        g_string_free(msg, TRUE);
        g_signal_connect(dialog, "response", G_CALLBACK(error_dialog_response), NULL);
        gtk_widget_show(dialog);
    }

    return G_SOURCE_REMOVE;
}

static void task_finished(SpiceFileTransferTask *task,
                          GError *error,
                          gpointer user_data)
{
    VirtViewerFileTransferDialog *self = VIRT_VIEWER_FILE_TRANSFER_DIALOG(user_data);

    if (error && !g_error_matches(error, G_IO_ERROR, G_IO_ERROR_CANCELLED)) {
        self->priv->failed = g_slist_prepend(self->priv->failed, g_object_ref(task));
        g_warning("File transfer task %p failed: %s", task, error->message);
    }

    self->priv->file_transfers = g_slist_remove(self->priv->file_transfers, task);
    self->priv->completed_transfer_size += spice_file_transfer_task_get_total_bytes(task);
    g_object_unref(task);
    update_global_progress(self);

    /* if this is the last transfer, close the dialog */
    if (self->priv->file_transfers == NULL) {
        self->priv->num_files = 0;
        self->priv->total_transfer_size = 0;
        self->priv->completed_transfer_size = 0;
        /* cancel any pending 'show' operations if all tasks complete before
         * the dialog can be shown */
        if (self->priv->timer_show_src) {
            g_source_remove(self->priv->timer_show_src);
            self->priv->timer_show_src = 0;
        }
        self->priv->timer_hide_src = g_timeout_add(500, hide_transfer_dialog,
                                                   self);
    }
}

static gboolean show_transfer_dialog_delayed(gpointer user_data)
{
    VirtViewerFileTransferDialog *self = user_data;

    self->priv->timer_show_src = 0;
    update_global_progress(self);
    gtk_widget_show(GTK_WIDGET(self));

    return G_SOURCE_REMOVE;
}

static void show_transfer_dialog(VirtViewerFileTransferDialog *self)
{
    /* if there's a pending 'hide', cancel it */
    if (self->priv->timer_hide_src) {
        g_source_remove(self->priv->timer_hide_src);
        self->priv->timer_hide_src = 0;
    }

    /* don't show the dialog immediately. For very quick transfers, it doesn't
     * make sense to show a dialog and immediately hide it. But if there's
     * already a pending 'show' operation, don't trigger another one */
    if (self->priv->timer_show_src == 0)
        self->priv->timer_show_src = g_timeout_add(250,
                                                   show_transfer_dialog_delayed,
                                                   self);

    gtk_dialog_set_response_sensitive(GTK_DIALOG(self),
                                      GTK_RESPONSE_CANCEL, TRUE);
}

void virt_viewer_file_transfer_dialog_add_task(VirtViewerFileTransferDialog *self,
                                               SpiceFileTransferTask *task)
{
    self->priv->file_transfers = g_slist_prepend(self->priv->file_transfers, g_object_ref(task));
    g_signal_connect(task, "notify::progress", G_CALLBACK(task_progress_notify), self);
    g_signal_connect(task, "notify::total-bytes", G_CALLBACK(task_total_bytes_notify), self);
    g_signal_connect(task, "finished", G_CALLBACK(task_finished), self);

    show_transfer_dialog(self);
}
