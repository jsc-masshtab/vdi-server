/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2017 Red Hat, Inc.
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

#ifndef __REMOTE_VIEWER_ISO_LIST_DIALOG_H__
#define __REMOTE_VIEWER_ISO_LIST_DIALOG_H__

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define REMOTE_VIEWER_TYPE_ISO_LIST_DIALOG remote_viewer_iso_list_dialog_get_type()

#define REMOTE_VIEWER_ISO_LIST_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), REMOTE_VIEWER_TYPE_ISO_LIST_DIALOG, RemoteViewerISOListDialog))
#define REMOTE_VIEWER_ISO_LIST_DIALOG_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), REMOTE_VIEWER_TYPE_ISO_LIST_DIALOG, RemoteViewerISOListDialogClass))
#define REMOTE_VIEWER_IS_ISO_LIST_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_TYPE((obj), REMOTE_VIEWER_TYPE_ISO_LIST_DIALOG))
#define REMOTE_VIEWER_IS_ISO_LIST_DIALOG_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE((klass), REMOTE_VIEWER_TYPE_ISO_LIST_DIALOG))
#define REMOTE_VIEWER_ISO_LIST_DIALOG_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS((obj), REMOTE_VIEWER_TYPE_ISO_LIST_DIALOG, RemoteViewerISOListDialogClass))

typedef struct _RemoteViewerISOListDialog RemoteViewerISOListDialog;
typedef struct _RemoteViewerISOListDialogClass RemoteViewerISOListDialogClass;
typedef struct _RemoteViewerISOListDialogPrivate RemoteViewerISOListDialogPrivate;

struct _RemoteViewerISOListDialog
{
    GtkDialog parent;

    RemoteViewerISOListDialogPrivate *priv;
};

struct _RemoteViewerISOListDialogClass
{
    GtkDialogClass parent_class;
};

GType remote_viewer_iso_list_dialog_get_type(void) G_GNUC_CONST;

GtkWidget *remote_viewer_iso_list_dialog_new(GtkWindow *parent, GObject *foreign_menu);

G_END_DECLS

#endif /* __REMOTE_VIEWER_ISO_LIST_DIALOG_H__ */
