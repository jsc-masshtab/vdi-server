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

#ifndef __VIRT_VIEWER_FILE_TRANSFER_DIALOG_H__
#define __VIRT_VIEWER_FILE_TRANSFER_DIALOG_H__

#include <gtk/gtk.h>
#include <spice-client.h>

G_BEGIN_DECLS

#define VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG virt_viewer_file_transfer_dialog_get_type()

#define VIRT_VIEWER_FILE_TRANSFER_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG, VirtViewerFileTransferDialog))
#define VIRT_VIEWER_FILE_TRANSFER_DIALOG_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG, VirtViewerFileTransferDialogClass))
#define VIRT_VIEWER_IS_FILE_TRANSFER_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_TYPE((obj), VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG))
#define VIRT_VIEWER_IS_FILE_TRANSFER_DIALOG_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE((klass), VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG))
#define VIRT_VIEWER_FILE_TRANSFER_DIALOG_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS((obj), VIRT_VIEWER_TYPE_FILE_TRANSFER_DIALOG, VirtViewerFileTransferDialogClass))

typedef struct _VirtViewerFileTransferDialog VirtViewerFileTransferDialog;
typedef struct _VirtViewerFileTransferDialogClass VirtViewerFileTransferDialogClass;
typedef struct _VirtViewerFileTransferDialogPrivate VirtViewerFileTransferDialogPrivate;

struct _VirtViewerFileTransferDialog
{
    GtkDialog parent;

    VirtViewerFileTransferDialogPrivate *priv;
};

struct _VirtViewerFileTransferDialogClass
{
    GtkDialogClass parent_class;
};

GType virt_viewer_file_transfer_dialog_get_type(void) G_GNUC_CONST;

VirtViewerFileTransferDialog *virt_viewer_file_transfer_dialog_new(GtkWindow *parent);
void virt_viewer_file_transfer_dialog_add_task(VirtViewerFileTransferDialog *self,
                                               SpiceFileTransferTask *task);

G_END_DECLS

#endif /* __VIRT_VIEWER_FILE_TRANSFER_DIALOG_H__ */
