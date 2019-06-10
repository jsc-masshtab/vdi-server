/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2007-2014 Red Hat, Inc.
 * Copyright (C) 2009-2012 Daniel P. Berrange
 * Copyright (C) 2010 Marc-André Lureau
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
 *
 * Author: Daniel P. Berrange <berrange@redhat.com>
 *         Christophe Fergeau <cfergeau@redhat.com>
 */
#ifndef _OVIRT_FOREIGN_MENU_H
#define _OVIRT_FOREIGN_MENU_H

#include <glib-object.h>
#include <govirt/govirt.h>
#include <gtk/gtk.h>

#include "virt-viewer-file.h"

G_BEGIN_DECLS

#define OVIRT_TYPE_FOREIGN_MENU ovirt_foreign_menu_get_type()

#define OVIRT_FOREIGN_MENU(obj)                                        \
    (G_TYPE_CHECK_INSTANCE_CAST ((obj), OVIRT_TYPE_FOREIGN_MENU, OvirtForeignMenu))

#define OVIRT_FOREIGN_MENU_CLASS(klass)                                \
    (G_TYPE_CHECK_CLASS_CAST ((klass), OVIRT_TYPE_FOREIGN_MENU, OvirtForeignMenuClass))

#define OVIRT_IS_FOREIGN_MENU(obj)                                \
    (G_TYPE_CHECK_INSTANCE_TYPE ((obj), OVIRT_TYPE_FOREIGN_MENU))

#define OVIRTIS_FOREIGN_MENU_CLASS(klass)                        \
    (G_TYPE_CHECK_CLASS_TYPE ((klass), OVIRT_TYPE_FOREIGN_MENU))

#define OVIRT_FOREIGN_MENU_GET_CLASS(obj)                        \
    (G_TYPE_INSTANCE_GET_CLASS ((obj), OVIRT_TYPE_FOREIGN_MENU, OvirtForeignMenuClass))

typedef struct _OvirtForeignMenu OvirtForeignMenu;
typedef struct _OvirtForeignMenuClass OvirtForeignMenuClass;
typedef struct _OvirtForeignMenuPrivate OvirtForeignMenuPrivate;

struct _OvirtForeignMenu {
    GObject parent;

    OvirtForeignMenuPrivate *priv;
};

struct _OvirtForeignMenuClass {
    GObjectClass parent_class;
};

GType ovirt_foreign_menu_get_type(void);

OvirtForeignMenu* ovirt_foreign_menu_new(OvirtProxy *proxy);
OvirtForeignMenu *ovirt_foreign_menu_new_from_file(VirtViewerFile *self);

void ovirt_foreign_menu_fetch_iso_names_async(OvirtForeignMenu *menu,
                                              GCancellable *cancellable,
                                              GAsyncReadyCallback callback,
                                              gpointer user_data);
GList *ovirt_foreign_menu_fetch_iso_names_finish(OvirtForeignMenu *foreign_menu,
                                                 GAsyncResult *result,
                                                 GError **error);

void ovirt_foreign_menu_set_current_iso_name_async(OvirtForeignMenu *foreign_menu,
                                                   const char *name,
                                                   GCancellable *cancellable,
                                                   GAsyncReadyCallback callback,
                                                   gpointer user_data);
gboolean ovirt_foreign_menu_set_current_iso_name_finish(OvirtForeignMenu *foreign_menu,
                                                        GAsyncResult *result,
                                                        GError **error);


GtkWidget *ovirt_foreign_menu_get_gtk_menu(OvirtForeignMenu *foreign_menu);
gchar *ovirt_foreign_menu_get_current_iso_name(OvirtForeignMenu *menu);
GList *ovirt_foreign_menu_get_iso_names(OvirtForeignMenu *menu);

G_END_DECLS

#endif /* _OVIRT_FOREIGN_MENU_H */
/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
