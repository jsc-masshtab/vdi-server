/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2007-2012, 2014 Red Hat, Inc.
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

#include <glib/gi18n.h>

#include <spice-client-gtk.h>

#include <usb-device-widget.h>
#include "virt-viewer-file.h"
#include "virt-viewer-file-transfer-dialog.h"
#include "virt-viewer-util.h"
#include "virt-viewer-session-spice.h"
#include "virt-viewer-display-spice.h"
#include "virt-viewer-auth.h"

gchar *m_password = NULL;

G_DEFINE_TYPE (VirtViewerSessionSpice, virt_viewer_session_spice, VIRT_VIEWER_TYPE_SESSION)


struct _VirtViewerSessionSpicePrivate {
    GtkWindow *main_window;
    SpiceSession *session;
    SpiceGtkSession *gtk_session;
    SpiceMainChannel *main_channel;
    const SpiceAudio *audio;
    int channel_count;
    int usbredir_channel_count;
    gboolean has_sw_smartcard_reader;
    guint pass_try;
    gboolean did_auto_conf;
    VirtViewerFileTransferDialog *file_transfer_dialog;

};

#define VIRT_VIEWER_SESSION_SPICE_GET_PRIVATE(o) (G_TYPE_INSTANCE_GET_PRIVATE((o), VIRT_VIEWER_TYPE_SESSION_SPICE, VirtViewerSessionSpicePrivate))

enum {
    PROP_0,
    PROP_SPICE_SESSION,
    PROP_SW_SMARTCARD_READER,
    PROP_MAIN_WINDOW
};


static void virt_viewer_session_spice_close(VirtViewerSession *session);
static gboolean virt_viewer_session_spice_open_fd(VirtViewerSession *session, int fd);
static gboolean virt_viewer_session_spice_open_host(VirtViewerSession *session, const gchar *host, const gchar *port, const gchar *tlsport);
static gboolean virt_viewer_session_spice_open_uri(VirtViewerSession *session, const gchar *uri, GError **error);
static gboolean virt_viewer_session_spice_channel_open_fd(VirtViewerSession *session, VirtViewerSessionChannel *channel, int fd);
static void virt_viewer_session_spice_usb_device_selection(VirtViewerSession *session, GtkWindow *parent);
static void virt_viewer_session_spice_channel_new(SpiceSession *s,
                                                  SpiceChannel *channel,
                                                  VirtViewerSession *session);
static void virt_viewer_session_spice_channel_destroy(SpiceSession *s,
                                                      SpiceChannel *channel,
                                                      VirtViewerSession *session);
static void virt_viewer_session_spice_smartcard_insert(VirtViewerSession *session);
static void virt_viewer_session_spice_smartcard_remove(VirtViewerSession *session);
static gboolean virt_viewer_session_spice_fullscreen_auto_conf(VirtViewerSessionSpice *self);
static void virt_viewer_session_spice_apply_monitor_geometry(VirtViewerSession *self, GHashTable *monitors);

static void virt_viewer_session_spice_clear_displays(VirtViewerSessionSpice *self)
{
    SpiceSession *session = self->priv->session;
    GList *l;
    GList *channels;

    channels = spice_session_get_channels(session);
    for (l = channels; l != NULL; l = l->next) {
        SpiceChannel *channel = SPICE_CHANNEL(l->data);

        g_object_set_data(G_OBJECT(channel), "virt-viewer-displays", NULL);
    }
    g_list_free(channels);
    virt_viewer_session_clear_displays(VIRT_VIEWER_SESSION(self));
}


static void
virt_viewer_session_spice_get_property(GObject *object, guint property_id,
                                       GValue *value, GParamSpec *pspec)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(object);
    VirtViewerSessionSpicePrivate *priv = self->priv;

    switch (property_id) {
    case PROP_SPICE_SESSION:
        g_value_set_object(value, priv->session);
        break;
    case PROP_SW_SMARTCARD_READER:
        g_value_set_boolean(value, priv->has_sw_smartcard_reader);
        break;
    case PROP_MAIN_WINDOW:
        g_value_set_object(value, self->priv->main_window);
        break;
    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
    }
}

static void
virt_viewer_session_spice_set_property(GObject *object, guint property_id,
                                       const GValue *value G_GNUC_UNUSED, GParamSpec *pspec)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(object);

    switch (property_id) {
    case PROP_MAIN_WINDOW:
        self->priv->main_window = g_value_dup_object(value);
        break;
    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
    }
}

static void
virt_viewer_session_spice_dispose(GObject *obj)
{
    VirtViewerSessionSpice *spice = VIRT_VIEWER_SESSION_SPICE(obj);

    if (spice->priv->session) {
        spice_session_disconnect(spice->priv->session);
        g_object_unref(spice->priv->session);
        spice->priv->session = NULL;
    }

    spice->priv->audio = NULL;

    g_clear_object(&spice->priv->main_window);
    if (spice->priv->file_transfer_dialog) {
        gtk_widget_destroy(GTK_WIDGET(spice->priv->file_transfer_dialog));
        spice->priv->file_transfer_dialog = NULL;
    }

    G_OBJECT_CLASS(virt_viewer_session_spice_parent_class)->dispose(obj);
}


static const gchar*
virt_viewer_session_spice_mime_type(VirtViewerSession *self G_GNUC_UNUSED)
{
    return "application/x-spice";
}

static gboolean
virt_viewer_session_spice_can_share_folder(VirtViewerSession *session)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);

    return spice_session_has_channel_type(self->priv->session, SPICE_CHANNEL_WEBDAV);
}

static gboolean
virt_viewer_session_spice_can_retry_auth(VirtViewerSession *session G_GNUC_UNUSED)
{
    return TRUE;
}

static void
create_spice_session(VirtViewerSessionSpice *self);

static void
property_notify_do_auto_conf(GObject *gobject G_GNUC_UNUSED,
                             GParamSpec *pspec G_GNUC_UNUSED,
                             VirtViewerSessionSpice *self)
{
    virt_viewer_session_spice_fullscreen_auto_conf(self);
}

static void
update_share_folder(VirtViewerSessionSpice *self)
{
    gboolean share;
    SpiceSession *session = self->priv->session;
    GList *l, *channels;

    g_object_get(self, "share-folder", &share, NULL);

    channels = spice_session_get_channels(session);
    for (l = channels; l != NULL; l = l->next) {
        SpiceChannel *channel = l->data;

        if (!SPICE_IS_WEBDAV_CHANNEL(channel))
            continue;

        if (share)
            spice_channel_connect(channel);
        else
            spice_channel_disconnect(channel, SPICE_CHANNEL_NONE);
    }

    g_list_free(channels);
}

static void
virt_viewer_session_spice_constructed(GObject *obj)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(obj);

    create_spice_session(self);

    virt_viewer_signal_connect_object(virt_viewer_session_get_app(VIRT_VIEWER_SESSION(self)),
                                      "notify::fullscreen",
                                      G_CALLBACK(property_notify_do_auto_conf),
                                      self, 0);

    virt_viewer_signal_connect_object(self, "notify::share-folder",
                                      G_CALLBACK(update_share_folder), self,
                                      G_CONNECT_SWAPPED);

    self->priv->file_transfer_dialog =
        virt_viewer_file_transfer_dialog_new(self->priv->main_window);

    G_OBJECT_CLASS(virt_viewer_session_spice_parent_class)->constructed(obj);
}

static void
virt_viewer_session_spice_class_init(VirtViewerSessionSpiceClass *klass)
{
    VirtViewerSessionClass *dclass = VIRT_VIEWER_SESSION_CLASS(klass);
    GObjectClass *oclass = G_OBJECT_CLASS(klass);

    oclass->get_property = virt_viewer_session_spice_get_property;
    oclass->set_property = virt_viewer_session_spice_set_property;
    oclass->dispose = virt_viewer_session_spice_dispose;
    oclass->constructed = virt_viewer_session_spice_constructed;

    dclass->close = virt_viewer_session_spice_close;
    dclass->open_fd = virt_viewer_session_spice_open_fd;
    dclass->open_host = virt_viewer_session_spice_open_host;
    dclass->open_uri = virt_viewer_session_spice_open_uri;
    dclass->channel_open_fd = virt_viewer_session_spice_channel_open_fd;
    dclass->usb_device_selection = virt_viewer_session_spice_usb_device_selection;
    dclass->smartcard_insert = virt_viewer_session_spice_smartcard_insert;
    dclass->smartcard_remove = virt_viewer_session_spice_smartcard_remove;
    dclass->mime_type = virt_viewer_session_spice_mime_type;
    dclass->apply_monitor_geometry = virt_viewer_session_spice_apply_monitor_geometry;
    dclass->can_share_folder = virt_viewer_session_spice_can_share_folder;
    dclass->can_retry_auth = virt_viewer_session_spice_can_retry_auth;

    g_type_class_add_private(klass, sizeof(VirtViewerSessionSpicePrivate));

    g_object_class_install_property(oclass,
                                    PROP_SPICE_SESSION,
                                    g_param_spec_object("spice-session",
                                                        "Spice session",
                                                        "Spice session",
                                                        SPICE_TYPE_SESSION,
                                                        G_PARAM_READABLE |
                                                        G_PARAM_STATIC_STRINGS));
    g_object_class_install_property(oclass,
                                    PROP_MAIN_WINDOW,
                                    g_param_spec_object("main-window",
                                                        "main window",
                                                        "Main Window",
                                                        GTK_TYPE_WINDOW,
                                                        G_PARAM_READWRITE | G_PARAM_CONSTRUCT_ONLY |
                                                        G_PARAM_STATIC_STRINGS));
    g_object_class_override_property(oclass,
                                     PROP_SW_SMARTCARD_READER,
                                     "software-smartcard-reader");
}

static void
virt_viewer_session_spice_init(VirtViewerSessionSpice *self G_GNUC_UNUSED)
{
    self->priv = VIRT_VIEWER_SESSION_SPICE_GET_PRIVATE(self);
}

static void
usb_connect_failed(GObject *object G_GNUC_UNUSED,
                   SpiceUsbDevice *device G_GNUC_UNUSED,
                   GError *error, VirtViewerSessionSpice *self)
{
    if (g_error_matches(error, G_IO_ERROR, G_IO_ERROR_CANCELLED))
        return;

    g_signal_emit_by_name(self, "session-usb-failed", error->message);
}

static void virt_viewer_session_spice_set_has_sw_reader(VirtViewerSessionSpice *session,
                                                        gboolean has_sw_reader)
{
    g_return_if_fail(VIRT_VIEWER_IS_SESSION_SPICE(session));

    if (has_sw_reader != session->priv->has_sw_smartcard_reader) {
        session->priv->has_sw_smartcard_reader = has_sw_reader;
        g_object_notify(G_OBJECT(session), "software-smartcard-reader");
    }
}

static void reader_added_cb(SpiceSmartcardManager *manager G_GNUC_UNUSED,
                            SpiceSmartcardReader *reader,
                            gpointer user_data)
{
    VirtViewerSessionSpice *session;

    session = VIRT_VIEWER_SESSION_SPICE(user_data);
    if (spice_smartcard_reader_is_software(reader)) {
        virt_viewer_session_spice_set_has_sw_reader(session, TRUE);
    }
}

static void reader_removed_cb(SpiceSmartcardManager *manager G_GNUC_UNUSED,
                              SpiceSmartcardReader *reader,
                              gpointer user_data)
{
    VirtViewerSessionSpice *session;

    session = VIRT_VIEWER_SESSION_SPICE(user_data);
    if (spice_smartcard_reader_is_software(reader)) {
        virt_viewer_session_spice_set_has_sw_reader(session, FALSE);
    }
}

#define UUID_LEN 16
static void
uuid_changed(GObject *gobject G_GNUC_UNUSED,
             GParamSpec *pspec G_GNUC_UNUSED,
             VirtViewerSessionSpice *self)
{
    guint8* uuid = NULL;
    VirtViewerApp* app = virt_viewer_session_get_app(VIRT_VIEWER_SESSION(self));

    g_object_get(self->priv->session, "uuid", &uuid, NULL);
    if (uuid) {
        int i;
        gboolean uuid_empty = TRUE;

        for (i = 0; i < UUID_LEN; i++) {
            if (uuid[i] != 0) {
                uuid_empty = FALSE;
                break;
            }
        }

        if (!uuid_empty) {
            gchar *uuid_str = spice_uuid_to_string(uuid);
            g_object_set(app, "uuid", uuid_str, NULL);
            g_free(uuid_str);
        }
    }

    virt_viewer_session_spice_fullscreen_auto_conf(self);
}

static void
name_changed(GObject *gobject G_GNUC_UNUSED,
              GParamSpec *pspec G_GNUC_UNUSED,
              VirtViewerSessionSpice *self)
{
    gchar *name = NULL;
    VirtViewerApp *app = virt_viewer_session_get_app(VIRT_VIEWER_SESSION(self));

    g_object_get(self->priv->session, "name", &name, NULL);

    g_object_set(app, "guest-name", name, NULL);
    g_free(name);
}

static void
create_spice_session(VirtViewerSessionSpice *self)
{
    SpiceUsbDeviceManager *usb_manager;
    SpiceSmartcardManager *smartcard_manager;

    g_return_if_fail(self != NULL);
    g_return_if_fail(self->priv->session == NULL);

    self->priv->session = spice_session_new();
    spice_set_session_option(self->priv->session);

    self->priv->gtk_session = spice_gtk_session_get(self->priv->session);
    g_object_set(self->priv->gtk_session, "auto-clipboard", TRUE, NULL);

    virt_viewer_signal_connect_object(self->priv->session, "channel-new",
                                      G_CALLBACK(virt_viewer_session_spice_channel_new), self, 0);
    virt_viewer_signal_connect_object(self->priv->session, "channel-destroy",
                                      G_CALLBACK(virt_viewer_session_spice_channel_destroy), self, 0);

    usb_manager = spice_usb_device_manager_get(self->priv->session, NULL);
    if (usb_manager) {
        virt_viewer_signal_connect_object(usb_manager, "auto-connect-failed",
                                          G_CALLBACK(usb_connect_failed), self, 0);
        virt_viewer_signal_connect_object(usb_manager, "device-error",
                                          G_CALLBACK(usb_connect_failed), self, 0);
    }
    g_object_bind_property(self, "auto-usbredir",
                           self->priv->gtk_session, "auto-usbredir",
                           G_BINDING_BIDIRECTIONAL | G_BINDING_SYNC_CREATE);

    smartcard_manager = spice_smartcard_manager_get();
    if (smartcard_manager) {
        GList *readers;
        GList *it;
        virt_viewer_signal_connect_object(smartcard_manager, "reader-added",
                                          G_CALLBACK(reader_added_cb), self, 0);
        virt_viewer_signal_connect_object(smartcard_manager, "reader-removed",
                                          G_CALLBACK(reader_removed_cb), self, 0);
        readers = spice_smartcard_manager_get_readers(smartcard_manager);
        for (it = readers; it != NULL; it = it->next) {
            SpiceSmartcardReader *reader;
            reader = (SpiceSmartcardReader *)it->data;
            if (spice_smartcard_reader_is_software(reader)) {
                virt_viewer_session_spice_set_has_sw_reader(self, TRUE);
            }
            g_boxed_free(SPICE_TYPE_SMARTCARD_READER, reader);
        }
        g_list_free(readers);
    }

    /* notify::uuid is guaranteed to be emitted during connection startup even
     * if the server is too old to support sending uuid */
    virt_viewer_signal_connect_object(self->priv->session, "notify::uuid",
                                      G_CALLBACK(uuid_changed), self, 0);
    virt_viewer_signal_connect_object(self->priv->session, "notify::name",
                                      G_CALLBACK(name_changed), self, 0);

    g_object_bind_property(self->priv->session, "shared-dir",
                           self, "shared-folder",
                           G_BINDING_BIDIRECTIONAL|G_BINDING_SYNC_CREATE);
    g_object_bind_property(self->priv->session, "share-dir-ro",
                           self, "share-folder-ro",
                           G_BINDING_BIDIRECTIONAL|G_BINDING_SYNC_CREATE);

}

static void
virt_viewer_session_spice_close(VirtViewerSession *session)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);

    g_return_if_fail(self != NULL);

    g_object_add_weak_pointer(G_OBJECT(self), (gpointer*)&self);

    virt_viewer_session_spice_clear_displays(self);

    if (self->priv->session) {
        spice_session_disconnect(self->priv->session);
        if (!self)
            return;

        g_object_unref(self->priv->session);
        self->priv->session = NULL;
        self->priv->gtk_session = NULL;
        self->priv->audio = NULL;
    }

    g_object_remove_weak_pointer(G_OBJECT(self), (gpointer*)&self);

    /* FIXME: version 0.7 of spice-gtk allows reuse of session */
    create_spice_session(self);
}

static gboolean
virt_viewer_session_spice_open_host(VirtViewerSession *session,
                                    const gchar *host,
                                    const gchar *port,
                                    const gchar *tlsport)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);

    g_return_val_if_fail(self != NULL, FALSE);
    g_return_val_if_fail(self->priv->session != NULL, FALSE);

    g_object_set(self->priv->session,
                 "host", host,
                 "port", port,
                 "tls-port", tlsport,
                 NULL);

    return spice_session_connect(self->priv->session);
}

static void
fill_session(VirtViewerFile *file, SpiceSession *session)
{
    g_return_if_fail(VIRT_VIEWER_IS_FILE(file));
    g_return_if_fail(SPICE_IS_SESSION(session));

    if (virt_viewer_file_is_set(file, "host")) {
        gchar *val = virt_viewer_file_get_host(file);
        g_object_set(G_OBJECT(session), "host", val, NULL);
        g_free(val);
    }

    if (virt_viewer_file_is_set(file, "port")) {
        gchar *port = g_strdup_printf("%d", virt_viewer_file_get_port(file));
        g_object_set(G_OBJECT(session), "port", port, NULL);
        g_free(port);
    }
    if (virt_viewer_file_is_set(file, "tls-port")) {
        gchar *tls_port = g_strdup_printf("%d", virt_viewer_file_get_tls_port(file));
        g_object_set(G_OBJECT(session), "tls-port", tls_port, NULL);
        g_free(tls_port);
    }

    if (virt_viewer_file_is_set(file, "username")) {
        gchar *val = virt_viewer_file_get_username(file);
        g_object_set(G_OBJECT(session), "username", val, NULL);
        g_free(val);
    }

    if (virt_viewer_file_is_set(file, "password")) {
        gchar *val = virt_viewer_file_get_password(file);
        g_object_set(G_OBJECT(session), "password", val, NULL);
        g_free(val);
    }

    if (virt_viewer_file_is_set(file, "tls-ciphers")) {
        gchar *val = virt_viewer_file_get_tls_ciphers(file);
        g_object_set(G_OBJECT(session), "ciphers", val, NULL);
        g_free(val);
    }

    if (virt_viewer_file_is_set(file, "ca")) {
        gchar *ca = virt_viewer_file_get_ca(file);
        g_return_if_fail(ca != NULL);

        GByteArray *ba = g_byte_array_new_take((guint8 *)ca, strlen(ca) + 1);
        g_object_set(G_OBJECT(session),
                     "ca", ba,
                     "ca-file", NULL,
                     NULL);
        g_byte_array_unref(ba);
    }

    if (virt_viewer_file_is_set(file, "host-subject")) {
        gchar *val = virt_viewer_file_get_host_subject(file);
        g_object_set(G_OBJECT(session), "cert-subject", val, NULL);
        g_free(val);
    }

    if (virt_viewer_file_is_set(file, "proxy")) {
        gchar *val = virt_viewer_file_get_proxy(file);
        g_object_set(G_OBJECT(session), "proxy", val, NULL);
        g_free(val);
    }

    if (virt_viewer_file_is_set(file, "enable-smartcard")) {
        g_object_set(G_OBJECT(session),
                     "enable-smartcard", virt_viewer_file_get_enable_smartcard(file), NULL);
    }

    if (virt_viewer_file_is_set(file, "enable-usbredir")) {
        g_object_set(G_OBJECT(session),
                     "enable-usbredir", virt_viewer_file_get_enable_usbredir(file), NULL);
    }

    if (virt_viewer_file_is_set(file, "color-depth")) {
        g_object_set(G_OBJECT(session),
                     "color-depth", virt_viewer_file_get_color_depth(file), NULL);
    }

    if (virt_viewer_file_is_set(file, "disable-effects")) {
        gchar **disabled = virt_viewer_file_get_disable_effects(file, NULL);
        g_object_set(G_OBJECT(session), "disable-effects", disabled, NULL);
        g_strfreev(disabled);
    }

    if (virt_viewer_file_is_set(file, "enable-usb-autoshare")) {
        gboolean enabled = virt_viewer_file_get_enable_usb_autoshare(file);
        SpiceGtkSession *gtk = spice_gtk_session_get(session);
        g_object_set(G_OBJECT(gtk), "auto-usbredir", enabled, NULL);
    }

    if (virt_viewer_file_is_set(file, "usb-filter")) {
        gchar *filterstr = virt_viewer_file_get_usb_filter(file);
        SpiceUsbDeviceManager *manager = spice_usb_device_manager_get(session,
                                                                      NULL);
        if (manager != NULL) {
            g_object_set(manager, "auto-connect-filter", filterstr, NULL);
        }
        g_free(filterstr);
    }

    if (virt_viewer_file_is_set(file, "secure-channels")) {
        gchar **channels = virt_viewer_file_get_secure_channels(file, NULL);
        g_object_set(G_OBJECT(session), "secure-channels", channels, NULL);
        g_strfreev(channels);
    }

    if (virt_viewer_file_is_set(file, "disable-channels")) {
        g_debug("FIXME: disable-channels is not supported atm");
    }
}

static gboolean
virt_viewer_session_spice_open_uri(VirtViewerSession *session,
                                   const gchar *uri, GError **error)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);
    VirtViewerFile *file = virt_viewer_session_get_file(session);
    VirtViewerApp *app = virt_viewer_session_get_app(session);

    g_return_val_if_fail(self != NULL, FALSE);
    g_return_val_if_fail(self->priv->session != NULL, FALSE);

    if (file) {
        fill_session(file, self->priv->session);
        if (!virt_viewer_file_fill_app(file, app, error))
            return FALSE;
    } else {
        g_object_set(self->priv->session, "uri", uri, NULL);
    }

    return spice_session_connect(self->priv->session);
}

static gboolean
virt_viewer_session_spice_open_fd(VirtViewerSession *session,
                                  int fd)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);

    g_return_val_if_fail(self != NULL, FALSE);

    return spice_session_open_fd(self->priv->session, fd);
}

static gboolean
virt_viewer_session_spice_channel_open_fd(VirtViewerSession *session,
                                          VirtViewerSessionChannel *channel,
                                          int fd)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);

    g_return_val_if_fail(self != NULL, FALSE);

    return spice_channel_open_fd(SPICE_CHANNEL(channel), fd);
}

static void
virt_viewer_session_spice_channel_open_fd_request(SpiceChannel *channel,
                                                  gint tls G_GNUC_UNUSED,
                                                  VirtViewerSession *session)
{
    g_signal_emit_by_name(session, "session-channel-open", channel);
}

static void
virt_viewer_session_spice_main_channel_event(SpiceChannel *channel,
                                             SpiceChannelEvent event,
                                             VirtViewerSession *session)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);
    gchar *password = NULL, *user = NULL;
    gboolean ret;
    static gboolean username_required = FALSE;

    g_return_if_fail(self != NULL);

    switch (event) {
    case SPICE_CHANNEL_OPENED:
        g_debug("main channel: opened");
        g_signal_emit_by_name(session, "session-connected");
        break;
    case SPICE_CHANNEL_CLOSED:
        g_debug("main channel: closed");
        /* Ensure the other channels get closed too */
        virt_viewer_session_spice_clear_displays(self);
        if (self->priv->session)
            spice_session_disconnect(self->priv->session);
        break;
    case SPICE_CHANNEL_SWITCHING:
        g_debug("main channel: switching host");
        break;
    case SPICE_CHANNEL_ERROR_AUTH: {
        const GError *error = NULL;
        gchar *host = NULL;
        g_debug("main channel: auth failure (wrong username/password?)");

        error = spice_channel_get_error(channel);
        username_required = g_error_matches(error,
                                            SPICE_CLIENT_ERROR,
                                            SPICE_CLIENT_ERROR_AUTH_NEEDS_PASSWORD_AND_USERNAME);

        if (self->priv->pass_try > 0)
            g_signal_emit_by_name(session, "session-auth-refused",
                                  error != NULL ? error->message : _("Invalid password"));
        self->priv->pass_try++;

        /* The username is firstly pre-filled with the username of the current
         * user and in case where some authentication error happened, the
         * username entry will be prefilled with the last username used.
         * Unfortunately, we don't have a clear way to differantiate bewteen
         * invalid username and invalid password. So, in both cases the username
         * entry will be pre-filled with the username used in the previous attempt. */
        if (username_required) {
            g_object_get(self->priv->session, "username", &user, NULL);
            if (user == NULL || *user == '\0')
                user = g_strdup(g_get_user_name());
        }

        g_object_get(self->priv->session, "host", &host, NULL);
        // Здесь забираются логин и пароль при после подключения к машинке
        printf("m_password\n");
        printf(m_password);
        printf("\n");

        // set password
        // Берем пароль с формы m_password_connect
        if (m_password) {
            password = g_strdup(m_password);
            ret = GTK_RESPONSE_OK;
        }
        // Если с формы получили неправильный пароль , то вызываем форму авторизации
        else{
            ret = virt_viewer_auth_collect_credentials(self->priv->main_window,
                                                       "SPICE",
                                                       host,
                                                       username_required ? &user : NULL,
                                                       &password);
        }

        g_free(host);
        if (!ret) {
            /* ret is false when dialog did not return GTK_RESPONSE_OK. We
             * should ignore auth error dialog if user has cancelled or closed
             * the dialog */
            self->priv->pass_try = 0;
            g_signal_emit_by_name(session, "session-cancelled");
        } else {
            gboolean openfd;

            g_object_set(self->priv->session, "username", user, NULL);
            g_object_set(self->priv->session, "password", password, NULL);
            g_object_get(self->priv->session, "client-sockets", &openfd, NULL);

            if (openfd)
                spice_session_open_fd(self->priv->session, -1);
            else
                spice_session_connect(self->priv->session);
        }
        break;
    }
    case SPICE_CHANNEL_ERROR_CONNECT:
    {
        const GError *error = spice_channel_get_error(channel);

        g_debug("main channel: failed to connect %s", error ? error->message : "");

        if (g_error_matches(error, G_IO_ERROR, G_IO_ERROR_PROXY_NEED_AUTH) ||
            g_error_matches(error, G_IO_ERROR, G_IO_ERROR_PROXY_AUTH_FAILED)) {
            SpiceURI *proxy = spice_session_get_proxy_uri(self->priv->session);
            g_warn_if_fail(proxy != NULL);

            ret = virt_viewer_auth_collect_credentials(self->priv->main_window,
                                                       "proxy", spice_uri_get_hostname(proxy),
                                                       &user, &password);
            if (!ret) {
                g_signal_emit_by_name(session, "session-cancelled");
            } else {
                spice_uri_set_user(proxy, user);
                spice_uri_set_password(proxy, password);
                spice_session_connect(self->priv->session);
            }
        } else {
            virt_viewer_session_spice_channel_destroy(NULL, channel, session);
        }
        break;
    }
    case SPICE_CHANNEL_ERROR_IO:
    case SPICE_CHANNEL_ERROR_LINK:
    case SPICE_CHANNEL_ERROR_TLS:
        virt_viewer_session_spice_channel_destroy(NULL, channel, session);
        break;
    default:
        g_warning("unhandled spice main channel event: %d", event);
        break;
    }

    if(m_password) {
        g_free(m_password);
        m_password = NULL;
    }
    g_free(password);
    g_free(user);
}

static void remove_cb(GtkContainer   *container G_GNUC_UNUSED,
                      GtkWidget      *widget G_GNUC_UNUSED,
                      void           *user_data)
{
    gtk_window_resize(GTK_WINDOW(user_data), 1, 1);
}

static void
virt_viewer_session_spice_usb_device_selection(VirtViewerSession *session,
                                               GtkWindow *parent)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);
    VirtViewerSessionSpicePrivate *priv = self->priv;
    GtkWidget *dialog, *area, *usb_device_widget;

    /* Create the widgets */
    dialog = gtk_dialog_new_with_buttons(_("Select USB devices for redirection"), parent,
                                         GTK_DIALOG_MODAL | GTK_DIALOG_DESTROY_WITH_PARENT,
                                         _("_Close"), GTK_RESPONSE_ACCEPT,
                                         NULL);
    gtk_dialog_set_default_response(GTK_DIALOG(dialog), GTK_RESPONSE_ACCEPT);
    gtk_container_set_border_width(GTK_CONTAINER(dialog), 12);
    gtk_box_set_spacing(GTK_BOX(gtk_bin_get_child(GTK_BIN(dialog))), 12);

    area = gtk_dialog_get_content_area(GTK_DIALOG(dialog));

    usb_device_widget = spice_usb_device_widget_new(priv->session,
                                                    "%s %s");
    virt_viewer_signal_connect_object(usb_device_widget, "connect-failed",
                                      G_CALLBACK(usb_connect_failed), self, 0);
    gtk_box_pack_start(GTK_BOX(area), usb_device_widget, TRUE, TRUE, 0);

    /* This shrinks the dialog when USB devices are unplugged */
    virt_viewer_signal_connect_object(usb_device_widget, "remove",
                                      G_CALLBACK(remove_cb), dialog, 0);

    /* show and run */
    gtk_widget_show_all(dialog);
    gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_destroy(dialog);
}

static void
agent_connected_changed(SpiceChannel *cmain G_GNUC_UNUSED,
                        GParamSpec *pspec G_GNUC_UNUSED,
                        VirtViewerSessionSpice *self)
{
    gboolean agent_connected;

    // this will force refresh of application menu
    g_signal_emit_by_name(self, "session-display-updated");

    g_object_get(cmain, "agent-connected", &agent_connected, NULL);
    if (agent_connected) {
        /* this will force update displays geometry when the agent has connected
         * after the application (eg: rebooting the guest) */
        virt_viewer_session_update_displays_geometry(VIRT_VIEWER_SESSION(self));
    }
}

static void
destroy_display(gpointer data)
{
    VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(data);
    VirtViewerSession *session;

    g_return_if_fail (display != NULL);

    session = virt_viewer_display_get_session(display);
    g_debug("Destroying spice display %p", display);
    virt_viewer_session_remove_display(session, display);
    g_object_unref(display);
}

static gboolean
display_is_in_fullscreen_mode(VirtViewerSessionSpice *self,
                              VirtViewerDisplay *display)
{
    gint nth = virt_viewer_display_get_nth(display);
    VirtViewerApp *app = virt_viewer_session_get_app(VIRT_VIEWER_SESSION(self));

    return virt_viewer_app_get_initial_monitor_for_display(app, nth) != -1;
}

static void
virt_viewer_session_spice_display_monitors(SpiceChannel *channel,
                                           GParamSpec *pspec G_GNUC_UNUSED,
                                           VirtViewerSessionSpice *self)
{
    GArray *monitors = NULL;
    GPtrArray *displays = NULL;
    GtkWidget *display;
    guint i, monitors_max;
    gboolean fullscreen_mode =
        virt_viewer_app_get_fullscreen(virt_viewer_session_get_app(VIRT_VIEWER_SESSION(self)));

    g_object_get(channel,
                 "monitors", &monitors,
                 "monitors-max", &monitors_max,
                 NULL);
    g_return_if_fail(monitors != NULL);
    g_return_if_fail(monitors->len <= monitors_max);

    displays = g_object_get_data(G_OBJECT(channel), "virt-viewer-displays");
    if (displays == NULL) {
        displays = g_ptr_array_new();
        g_ptr_array_set_free_func(displays, destroy_display);
        g_object_set_data_full(G_OBJECT(channel), "virt-viewer-displays",
                               displays, (GDestroyNotify)g_ptr_array_unref);
    }

    g_ptr_array_set_size(displays, monitors_max);

    for (i = 0; i < monitors_max; i++) {
        display = g_ptr_array_index(displays, i);
        if (display == NULL) {
            display = virt_viewer_display_spice_new(self, channel, i);
            if (display == NULL)
                continue;

            g_debug("creating spice display (#:%d)",
                    virt_viewer_display_get_nth(VIRT_VIEWER_DISPLAY(display)));
            g_ptr_array_index(displays, i) = g_object_ref_sink(display);
            virt_viewer_session_add_display(VIRT_VIEWER_SESSION(self),
                                            VIRT_VIEWER_DISPLAY(display));
        }
    }

    for (i = 0; i < monitors->len; i++) {
        SpiceDisplayMonitorConfig *monitor = &g_array_index(monitors, SpiceDisplayMonitorConfig, i);
        gboolean disabled = monitor->width == 0 || monitor->height == 0;
        display = g_ptr_array_index(displays, monitor->id);
        g_return_if_fail(display != NULL);

        if (!disabled && fullscreen_mode && self->priv->did_auto_conf &&
            !display_is_in_fullscreen_mode(self, VIRT_VIEWER_DISPLAY(display))) {
            g_debug("display %d should not be enabled, disabling",
                    virt_viewer_display_get_nth(VIRT_VIEWER_DISPLAY(display)) + 1);
            spice_main_set_display_enabled(virt_viewer_session_spice_get_main_channel(self),
                                           virt_viewer_display_get_nth(VIRT_VIEWER_DISPLAY(display)),
                                           FALSE);
            disabled = TRUE;
        }

        virt_viewer_display_set_enabled(VIRT_VIEWER_DISPLAY(display), !disabled);

        if (disabled)
            continue;

        virt_viewer_display_spice_set_desktop(VIRT_VIEWER_DISPLAY(display),
                                              monitor->x, monitor->y,
                                              monitor->width, monitor->height);
    }

    g_clear_pointer(&monitors, g_array_unref);

}

static void
on_new_file_transfer(SpiceMainChannel *channel G_GNUC_UNUSED,
                     SpiceFileTransferTask *task,
                     gpointer user_data)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(user_data);
    virt_viewer_file_transfer_dialog_add_task(self->priv->file_transfer_dialog,
                                              task);
}

static void
virt_viewer_session_spice_channel_new(SpiceSession *s,
                                      SpiceChannel *channel,
                                      VirtViewerSession *session)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);
    int id;

    g_return_if_fail(self != NULL);

    virt_viewer_signal_connect_object(channel, "open-fd",
                                      G_CALLBACK(virt_viewer_session_spice_channel_open_fd_request), self, 0);

    g_object_get(channel, "channel-id", &id, NULL);

    g_debug("New spice channel %p %s %d", channel, g_type_name(G_OBJECT_TYPE(channel)), id);

    if (SPICE_IS_MAIN_CHANNEL(channel)) {
        if (self->priv->main_channel != NULL)
            g_signal_handlers_disconnect_by_func(self->priv->main_channel,
                                                 virt_viewer_session_spice_main_channel_event, self);

        virt_viewer_signal_connect_object(channel, "channel-event",
                                          G_CALLBACK(virt_viewer_session_spice_main_channel_event), self, 0);
        self->priv->main_channel = SPICE_MAIN_CHANNEL(channel);
        g_object_set(G_OBJECT(channel),
                     "disable-display-position", FALSE,
                     "disable-display-align", TRUE,
                     NULL);

        virt_viewer_signal_connect_object(channel, "notify::agent-connected",
                                          G_CALLBACK(agent_connected_changed), self, 0);
        virt_viewer_signal_connect_object(channel, "new-file-transfer",
                                          G_CALLBACK(on_new_file_transfer), self, 0);
    }

    if (SPICE_IS_DISPLAY_CHANNEL(channel)) {
        g_signal_emit_by_name(session, "session-initialized");

        virt_viewer_signal_connect_object(channel, "notify::monitors",
                                          G_CALLBACK(virt_viewer_session_spice_display_monitors), self, 0);

        spice_channel_connect(channel);
    }

    if (SPICE_IS_INPUTS_CHANNEL(channel)) {
        g_debug("new inputs channel");
    }

    if (SPICE_IS_PLAYBACK_CHANNEL(channel)) {
        g_debug("new audio channel");
        if (self->priv->audio == NULL)
            self->priv->audio = spice_audio_get(s, NULL);
    }

    if (SPICE_IS_USBREDIR_CHANNEL(channel)) {
        g_debug("new usbredir channel");
        self->priv->usbredir_channel_count++;
        if (spice_usb_device_manager_get(self->priv->session, NULL))
            virt_viewer_session_set_has_usbredir(session, TRUE);
    }

    self->priv->channel_count++;
}

static gboolean
virt_viewer_session_spice_fullscreen_auto_conf(VirtViewerSessionSpice *self)
{
    GdkScreen *screen = gdk_screen_get_default();
    SpiceMainChannel* cmain = virt_viewer_session_spice_get_main_channel(self);
    VirtViewerApp *app = NULL;
    GHashTable *displays;
    GHashTableIter iter;
    gpointer key, value;
    gboolean agent_connected;
    GList *initial_displays, *l;
    guint ndisplays;

    /* only do auto-conf once at startup. Avoid repeating auto-conf later due to
     * agent disconnection/re-connection, etc */
    if (self->priv->did_auto_conf) {
        g_debug("Already did auto-conf, skipping");
        return FALSE;
    }

    app = virt_viewer_session_get_app(VIRT_VIEWER_SESSION(self));
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(app), TRUE);

    if (!virt_viewer_app_get_fullscreen(app)) {
        g_debug("app is not in full screen");
        return FALSE;
    }
    if (cmain == NULL) {
        g_debug("no main channel yet");
        return FALSE;
    }
    g_object_get(cmain, "agent-connected", &agent_connected, NULL);
    if (!agent_connected) {
        g_debug("Agent not connected, skipping autoconf");
        virt_viewer_signal_connect_object(cmain, "notify::agent-connected",
                                          G_CALLBACK(property_notify_do_auto_conf), self, 0);
        return FALSE;
    }

    spice_main_set_display_enabled(cmain, -1, FALSE);

    initial_displays = virt_viewer_app_get_initial_displays(app);
    ndisplays = g_list_length(initial_displays);
    g_debug("Performing full screen auto-conf, %u host monitors", ndisplays);
    displays = g_hash_table_new_full(g_direct_hash, g_direct_equal, NULL, g_free);

    for (l = initial_displays; l != NULL; l = l->next) {
        GdkRectangle* rect = g_new0(GdkRectangle, 1);;
        gint j = virt_viewer_app_get_initial_monitor_for_display(app, GPOINTER_TO_INT(l->data));
        if (j == -1)
            continue;

        gdk_screen_get_monitor_geometry(screen, j, rect);
        g_hash_table_insert(displays, l->data, rect);
    }

    virt_viewer_shift_monitors_to_origin(displays);

    g_hash_table_iter_init(&iter, displays);
    while (g_hash_table_iter_next(&iter, &key, &value)) {
        GdkRectangle *rect = value;
        gint j = GPOINTER_TO_INT(key);

        spice_main_set_display(cmain, j, rect->x, rect->y, rect->width, rect->height);
        spice_main_set_display_enabled(cmain, j, TRUE);
        g_debug("Set SPICE display %d to (%d,%d)-(%dx%d)",
                  j, rect->x, rect->y, rect->width, rect->height);
    }
    g_list_free(initial_displays);
    g_hash_table_unref(displays);

    spice_main_send_monitor_config(cmain);
    self->priv->did_auto_conf = TRUE;
    return TRUE;
}

static void
virt_viewer_session_spice_channel_destroy(G_GNUC_UNUSED SpiceSession *s,
                                          SpiceChannel *channel,
                                          VirtViewerSession *session)
{
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);
    int id;
    const GError *error;

    g_return_if_fail(self != NULL);

    g_object_get(channel, "channel-id", &id, NULL);
    g_debug("Destroy SPICE channel %s %d", g_type_name(G_OBJECT_TYPE(channel)), id);

    error = spice_channel_get_error(channel);

    if (SPICE_IS_MAIN_CHANNEL(channel)) {
        g_debug("zap main channel");
        if (channel == SPICE_CHANNEL(self->priv->main_channel))
            self->priv->main_channel = NULL;
    }

    if (SPICE_IS_DISPLAY_CHANNEL(channel)) {
        g_debug("zap display channel (#%d)", id);
        g_object_set_data(G_OBJECT(channel), "virt-viewer-displays", NULL);
    }

    if (SPICE_IS_PLAYBACK_CHANNEL(channel) && self->priv->audio) {
        g_debug("zap audio channel");
        self->priv->audio = NULL;
    }

    if (SPICE_IS_USBREDIR_CHANNEL(channel)) {
        g_debug("zap usbredir channel");
        self->priv->usbredir_channel_count--;
        if (self->priv->usbredir_channel_count == 0)
            virt_viewer_session_set_has_usbredir(session, FALSE);
    }

    self->priv->channel_count--;
    if (self->priv->channel_count == 0)
        g_signal_emit_by_name(self, "session-disconnected", error ? error->message : NULL);
}

VirtViewerSession *
virt_viewer_session_spice_new(VirtViewerApp *app, GtkWindow *main_window)
{
    VirtViewerSessionSpice *self;

    self = g_object_new(VIRT_VIEWER_TYPE_SESSION_SPICE,
                        "app", app,
                        "main-window", main_window,
                        NULL);
    return VIRT_VIEWER_SESSION(self);
}

SpiceMainChannel*
virt_viewer_session_spice_get_main_channel(VirtViewerSessionSpice *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_SESSION_SPICE(self), NULL);

    return self->priv->main_channel;
}

static void
virt_viewer_session_spice_smartcard_insert(VirtViewerSession *session G_GNUC_UNUSED)
{
    spice_smartcard_manager_insert_card(spice_smartcard_manager_get());
}

static void
virt_viewer_session_spice_smartcard_remove(VirtViewerSession *session G_GNUC_UNUSED)
{
    spice_smartcard_manager_remove_card(spice_smartcard_manager_get());
}

static void
virt_viewer_session_spice_apply_monitor_geometry(VirtViewerSession *session, GHashTable *monitors)
{
    GHashTableIter iter;
    gpointer key = NULL, value = NULL;
    VirtViewerSessionSpice *self = VIRT_VIEWER_SESSION_SPICE(session);

    g_hash_table_iter_init(&iter, monitors);
    while (g_hash_table_iter_next(&iter, &key, &value)) {
        gint i = GPOINTER_TO_INT(key);
        GdkRectangle* rect = value;

        spice_main_set_display(self->priv->main_channel, i, rect->x,
                               rect->y, rect->width, rect->height);
    }
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
