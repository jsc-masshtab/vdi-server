/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2007-2012 Red Hat, Inc.
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
 */

#include <config.h>

#include <locale.h>
#include <math.h>

#include "virt-viewer-session.h"
#include "virt-viewer-util.h"

#define VIRT_VIEWER_SESSION_GET_PRIVATE(o) (G_TYPE_INSTANCE_GET_PRIVATE((o), VIRT_VIEWER_TYPE_SESSION, VirtViewerSessionPrivate))


struct _VirtViewerSessionPrivate
{
    GList *displays;
    VirtViewerApp *app;
    gboolean auto_usbredir;
    gboolean has_usbredir;
    gchar *uri;
    VirtViewerFile *file;
    gboolean share_folder;
    gchar *shared_folder;
    gboolean share_folder_ro;
};

G_DEFINE_ABSTRACT_TYPE(VirtViewerSession, virt_viewer_session, G_TYPE_OBJECT)

enum {
    PROP_0,

    PROP_APP,
    PROP_AUTO_USBREDIR,
    PROP_HAS_USBREDIR,
    PROP_FILE,
    PROP_SW_SMARTCARD_READER,
    PROP_SHARE_FOLDER,
    PROP_SHARED_FOLDER,
    PROP_SHARE_FOLDER_RO,
};

static void
virt_viewer_session_finalize(GObject *obj)
{
    VirtViewerSession *session = VIRT_VIEWER_SESSION(obj);
    GList *tmp = session->priv->displays;

    while (tmp) {
        g_object_unref(tmp->data);
        tmp = tmp->next;
    }
    g_list_free(session->priv->displays);

    g_free(session->priv->uri);
    g_clear_object(&session->priv->file);
    g_free(session->priv->shared_folder);

    G_OBJECT_CLASS(virt_viewer_session_parent_class)->finalize(obj);
}

static void
virt_viewer_session_set_property(GObject *object,
                                 guint prop_id,
                                 const GValue *value,
                                 GParamSpec *pspec)
{
    VirtViewerSession *self = VIRT_VIEWER_SESSION(object);

    switch (prop_id) {
    case PROP_AUTO_USBREDIR:
        virt_viewer_session_set_auto_usbredir(self, g_value_get_boolean(value));
        break;

    case PROP_HAS_USBREDIR:
        self->priv->has_usbredir = g_value_get_boolean(value);
        break;

    case PROP_APP:
        self->priv->app = g_value_get_object(value);
        break;

    case PROP_FILE:
        virt_viewer_session_set_file(self, g_value_get_object(value));
        break;

    case PROP_SHARE_FOLDER:
        self->priv->share_folder = g_value_get_boolean(value);
        break;

    case PROP_SHARED_FOLDER:
        g_free(self->priv->shared_folder);
        self->priv->shared_folder = g_value_dup_string(value);
        break;

    case PROP_SHARE_FOLDER_RO:
        self->priv->share_folder_ro = g_value_get_boolean(value);
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID(object, prop_id, pspec);
        break;
    }
}

static void
virt_viewer_session_get_property(GObject *object,
                                 guint prop_id,
                                 GValue *value,
                                 GParamSpec *pspec)
{
    VirtViewerSession *self = VIRT_VIEWER_SESSION(object);

    switch (prop_id) {
    case PROP_AUTO_USBREDIR:
        g_value_set_boolean(value, virt_viewer_session_get_auto_usbredir(self));
        break;

    case PROP_HAS_USBREDIR:
        g_value_set_boolean(value, self->priv->has_usbredir);
        break;

    case PROP_APP:
        g_value_set_object(value, self->priv->app);
        break;

    case PROP_FILE:
        g_value_set_object(value, self->priv->file);
        break;

    case PROP_SW_SMARTCARD_READER:
        g_value_set_boolean(value, FALSE);
        break;

    case PROP_SHARE_FOLDER:
        g_value_set_boolean(value, self->priv->share_folder);
        break;

    case PROP_SHARED_FOLDER:
        g_value_set_string(value, self->priv->shared_folder);
        break;

    case PROP_SHARE_FOLDER_RO:
        g_value_set_boolean(value, self->priv->share_folder_ro);
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID(object, prop_id, pspec);
        break;
    }
}

static void
virt_viewer_session_class_init(VirtViewerSessionClass *class)
{
    GObjectClass *object_class = G_OBJECT_CLASS(class);

    object_class->set_property = virt_viewer_session_set_property;
    object_class->get_property = virt_viewer_session_get_property;
    object_class->finalize = virt_viewer_session_finalize;

    g_object_class_install_property(object_class,
                                    PROP_AUTO_USBREDIR,
                                    g_param_spec_boolean("auto-usbredir",
                                                         "USB redirection",
                                                         "USB redirection",
                                                         TRUE,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_CONSTRUCT |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_HAS_USBREDIR,
                                    g_param_spec_boolean("has-usbredir",
                                                         "has USB redirection",
                                                         "has USB redirection",
                                                         FALSE,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_CONSTRUCT |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_APP,
                                    g_param_spec_object("app",
                                                         "VirtViewerApp",
                                                         "VirtViewerApp",
                                                         VIRT_VIEWER_TYPE_APP,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_CONSTRUCT |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_FILE,
                                    g_param_spec_object("file",
                                                         "VirtViewerFile",
                                                         "VirtViewerFile",
                                                         VIRT_VIEWER_TYPE_FILE,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_CONSTRUCT |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_SW_SMARTCARD_READER,
                                    g_param_spec_boolean("software-smartcard-reader",
                                                         "Software smartcard reader",
                                                         "Indicates whether a software smartcard reader is available",
                                                         FALSE,
                                                         G_PARAM_READABLE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_SHARE_FOLDER,
                                    g_param_spec_boolean("share-folder",
                                                         "Share folder",
                                                         "Indicates whether to share folder",
                                                         FALSE,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_SHARED_FOLDER,
                                    g_param_spec_string("shared-folder",
                                                        "Shared folder",
                                                        "Indicates the shared folder",
                                                        g_get_user_special_dir(G_USER_DIRECTORY_PUBLIC_SHARE),
                                                        G_PARAM_READWRITE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_SHARE_FOLDER_RO,
                                    g_param_spec_boolean("share-folder-ro",
                                                         "Share folder read-only",
                                                         "Indicates whether to share folder in read-only",
                                                         FALSE,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_STATIC_STRINGS));

    g_signal_new("session-connected",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_FIRST,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_connected),
                 NULL, NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("session-initialized",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_FIRST,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_initialized),
                 NULL, NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("session-disconnected",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_FIRST,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_disconnected),
                 NULL, NULL,
                 g_cclosure_marshal_VOID__STRING,
                 G_TYPE_NONE,
                 1,
                 G_TYPE_STRING);

    g_signal_new("session-channel-open",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_FIRST,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_channel_open),
                 NULL, NULL,
                 g_cclosure_marshal_VOID__OBJECT,
                 G_TYPE_NONE,
                 1,
                 G_TYPE_OBJECT);

    g_signal_new("session-auth-refused",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_auth_refused),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__STRING,
                 G_TYPE_NONE,
                 1,
                 G_TYPE_STRING);

    g_signal_new("session-auth-unsupported",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_auth_unsupported),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__STRING,
                 G_TYPE_NONE,
                 1,
                 G_TYPE_STRING);

    g_signal_new("session-usb-failed",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_usb_failed),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__STRING,
                 G_TYPE_NONE,
                 1,
                 G_TYPE_STRING);

    g_signal_new("session-display-added",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_display_added),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__OBJECT,
                 G_TYPE_NONE,
                 1,
                 VIRT_VIEWER_TYPE_DISPLAY);

    g_signal_new("session-display-removed",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_display_removed),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__OBJECT,
                 G_TYPE_NONE,
                 1,
                 VIRT_VIEWER_TYPE_DISPLAY);

    g_signal_new("session-display-updated",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_display_updated),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("session-cut-text",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_cut_text),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__STRING,
                 G_TYPE_NONE,
                 1,
                 G_TYPE_STRING);

    g_signal_new("session-bell",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_bell),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("session-cancelled",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_FIRST,
                 G_STRUCT_OFFSET(VirtViewerSessionClass, session_cancelled),
                 NULL, NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_type_class_add_private(class, sizeof(VirtViewerSessionPrivate));
}

static void
virt_viewer_session_init(VirtViewerSession *session)
{
    session->priv = VIRT_VIEWER_SESSION_GET_PRIVATE(session);
}

static void
virt_viewer_session_on_monitor_geometry_changed(VirtViewerSession* self,
                                                VirtViewerDisplay* display G_GNUC_UNUSED)
{
    VirtViewerSessionClass *klass;
    gboolean all_fullscreen = TRUE;
    /* GHashTable<gint, GdkRectangle*> */
    GHashTable *monitors;
    GList *l;

    klass = VIRT_VIEWER_SESSION_GET_CLASS(self);
    if (!klass->apply_monitor_geometry)
        return;

    monitors = g_hash_table_new_full(g_direct_hash, g_direct_equal, NULL, g_free);

    for (l = self->priv->displays; l; l = l->next) {
        VirtViewerDisplay *d = VIRT_VIEWER_DISPLAY(l->data);
        guint nth = 0;
        GdkRectangle *rect = g_new0(GdkRectangle, 1);

        g_object_get(d, "nth-display", &nth, NULL);
        virt_viewer_display_get_preferred_monitor_geometry(d, rect);

        if (virt_viewer_display_get_enabled(d) &&
            !virt_viewer_display_get_fullscreen(d))
            all_fullscreen = FALSE;
        g_hash_table_insert(monitors, GINT_TO_POINTER(nth), rect);
    }

    if (!all_fullscreen)
        virt_viewer_align_monitors_linear(monitors);

    virt_viewer_shift_monitors_to_origin(monitors);

    klass->apply_monitor_geometry(self, monitors);
    g_hash_table_unref(monitors);
}

void virt_viewer_session_add_display(VirtViewerSession *session,
                                     VirtViewerDisplay *display)
{
    if (g_list_find(session->priv->displays, display))
        return;

    session->priv->displays = g_list_append(session->priv->displays, display);
    g_object_ref(display);
    g_signal_emit_by_name(session, "session-display-added", display);

    virt_viewer_signal_connect_object(display, "monitor-geometry-changed",
                                      G_CALLBACK(virt_viewer_session_on_monitor_geometry_changed), session,
                                      G_CONNECT_SWAPPED);
}


void virt_viewer_session_remove_display(VirtViewerSession *session,
                                        VirtViewerDisplay *display)
{
    if (!g_list_find(session->priv->displays, display))
        return;

    session->priv->displays = g_list_remove(session->priv->displays, display);
    g_signal_emit_by_name(session, "session-display-removed", display);
    g_object_unref(display);
}

void virt_viewer_session_clear_displays(VirtViewerSession *session)
{
    GList *tmp = session->priv->displays;

    while (tmp) {
        VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(tmp->data);
        g_signal_emit_by_name(session, "session-display-removed", display);
        virt_viewer_display_close(display);
        g_object_unref(display);
        tmp = tmp->next;
    }
    g_list_free(session->priv->displays);
    session->priv->displays = NULL;
}

void virt_viewer_session_update_displays_geometry(VirtViewerSession *session)
{
    virt_viewer_session_on_monitor_geometry_changed(session, NULL);
}


void virt_viewer_session_close(VirtViewerSession *session)
{
    g_return_if_fail(VIRT_VIEWER_IS_SESSION(session));

    VIRT_VIEWER_SESSION_GET_CLASS(session)->close(session);
}

gboolean virt_viewer_session_open_fd(VirtViewerSession *session, int fd)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(session), FALSE);

    return VIRT_VIEWER_SESSION_GET_CLASS(session)->open_fd(session, fd);
}

gboolean virt_viewer_session_open_host(VirtViewerSession *session, const gchar *host, const gchar *port, const gchar *tlsport)
{
    VirtViewerSessionClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(session), FALSE);

    klass = VIRT_VIEWER_SESSION_GET_CLASS(session);
    return klass->open_host(session, host, port, tlsport);
}

gboolean virt_viewer_session_open_uri(VirtViewerSession *session, const gchar *uri, GError **error)
{
    VirtViewerSessionClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(session), FALSE);

    klass = VIRT_VIEWER_SESSION_GET_CLASS(session);
    g_return_val_if_fail(klass->open_uri != NULL, FALSE);

    session->priv->uri = g_strdup(uri);

    return klass->open_uri(session, uri, error);
}

const gchar* virt_viewer_session_mime_type(VirtViewerSession *self)
{
    VirtViewerSessionClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), FALSE);

    if (self->priv->file)
        return "application/x-virt-viewer";

    klass = VIRT_VIEWER_SESSION_GET_CLASS(self);
    g_return_val_if_fail(klass->mime_type != NULL, FALSE);

    return klass->mime_type(self);
}

gboolean virt_viewer_session_channel_open_fd(VirtViewerSession *session,
                                             VirtViewerSessionChannel *channel, int fd)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(session), FALSE);

    return VIRT_VIEWER_SESSION_GET_CLASS(session)->channel_open_fd(session, channel, fd);
}

void virt_viewer_session_set_auto_usbredir(VirtViewerSession *self, gboolean auto_usbredir)
{
    g_return_if_fail(VIRT_VIEWER_IS_SESSION(self));

    if (self->priv->auto_usbredir == auto_usbredir)
        return;

    self->priv->auto_usbredir = auto_usbredir;
    g_object_notify(G_OBJECT(self), "auto-usbredir");
}

gboolean virt_viewer_session_get_auto_usbredir(VirtViewerSession *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), FALSE);

    return self->priv->auto_usbredir;
}

void virt_viewer_session_set_has_usbredir(VirtViewerSession *self, gboolean has_usbredir)
{
    g_return_if_fail(VIRT_VIEWER_IS_SESSION(self));

    if (self->priv->has_usbredir == has_usbredir)
        return;

    self->priv->has_usbredir = has_usbredir;
    g_object_notify(G_OBJECT(self), "has-usbredir");
}

gboolean virt_viewer_session_get_has_usbredir(VirtViewerSession *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), FALSE);

    return self->priv->has_usbredir;
}

void virt_viewer_session_usb_device_selection(VirtViewerSession   *self,
                                              GtkWindow           *parent)
{
    VirtViewerSessionClass *klass;

    g_return_if_fail(VIRT_VIEWER_IS_SESSION(self));

    klass = VIRT_VIEWER_SESSION_GET_CLASS(self);
    g_return_if_fail(klass->usb_device_selection != NULL);

    klass->usb_device_selection(self, parent);
}

void virt_viewer_session_smartcard_insert(VirtViewerSession *self)
{
    VirtViewerSessionClass *klass;

    g_return_if_fail(VIRT_VIEWER_IS_SESSION(self));

    klass = VIRT_VIEWER_SESSION_GET_CLASS(self);
    if (klass->smartcard_insert == NULL) {
        g_debug("No session smartcard support");
        return;
    }

    klass->smartcard_insert(self);
}

void virt_viewer_session_smartcard_remove(VirtViewerSession *self)
{
    VirtViewerSessionClass *klass;

    g_return_if_fail(VIRT_VIEWER_IS_SESSION(self));

    klass = VIRT_VIEWER_SESSION_GET_CLASS(self);
    if (klass->smartcard_remove == NULL) {
        g_debug("No session smartcard support");
        return;
    }

    klass->smartcard_remove(self);
}

VirtViewerApp* virt_viewer_session_get_app(VirtViewerSession *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), NULL);

    return self->priv->app;
}

gchar* virt_viewer_session_get_uri(VirtViewerSession *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), FALSE);

    return g_strdup(self->priv->uri);
}

void virt_viewer_session_set_file(VirtViewerSession *self, VirtViewerFile *file)
{
    g_return_if_fail(VIRT_VIEWER_IS_SESSION(self));

    g_clear_object(&self->priv->file);
    if (file)
        self->priv->file = g_object_ref(file);
}

VirtViewerFile* virt_viewer_session_get_file(VirtViewerSession *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), NULL);

    return self->priv->file;
}

gboolean virt_viewer_session_can_share_folder(VirtViewerSession *self)
{
    VirtViewerSessionClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), FALSE);

    klass = VIRT_VIEWER_SESSION_GET_CLASS(self);

    return klass->can_share_folder ? klass->can_share_folder(self) : FALSE;
}

gboolean virt_viewer_session_can_retry_auth(VirtViewerSession *self)
{
    VirtViewerSessionClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION(self), FALSE);

    klass = VIRT_VIEWER_SESSION_GET_CLASS(self);

    return klass->can_retry_auth ? klass->can_retry_auth(self) : FALSE;
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
