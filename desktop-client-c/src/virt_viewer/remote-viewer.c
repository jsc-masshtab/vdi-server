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
 * Author: Marc-André Lureau <marcandre.lureau@redhat.com>
 *
 * Modified by Solomin <a.solomin@mashtab.org>
 */



#include <config.h>
#include <gio/gio.h>
#include <gtk/gtk.h>
#include <glib/gprintf.h>
#include <glib/gi18n.h>
#include <libxml/uri.h>

#ifdef HAVE_OVIRT
#include <govirt/govirt.h>
#include "ovirt-foreign-menu.h"
#include "virt-viewer-vm-connection.h"
#endif

#ifdef HAVE_SPICE_GTK
#include "virt-viewer-session-spice.h"
#endif

#ifdef HAVE_SPICE_CONTROLLER
#include <spice-controller.h>
#endif

#include "virt-viewer-app.h"
#include "virt-viewer-auth.h"
#include "virt-viewer-file.h"
#include "virt-viewer-session.h"
#include "virt-viewer-util.h"
#include "remote-viewer.h"
#include "remote-viewer-connect.h"
#include "vdi_manager.h"
#include "vdi_api_session.h"

#define RECONNECT_TIMEOUT 1000

extern gboolean opt_manual_mode;

struct _RemoteViewerPrivate {
    gboolean open_recent_dialog;
    guint reconnect_poll; // id for reconnect timer
};

G_DEFINE_TYPE (RemoteViewer, remote_viewer, VIRT_VIEWER_TYPE_APP)
#define GET_PRIVATE(o)                                                        \
    (G_TYPE_INSTANCE_GET_PRIVATE ((o), REMOTE_VIEWER_TYPE, RemoteViewerPrivate))

enum RemoteViewerProperties {
    PROP_0,
#ifdef HAVE_OVIRT
    PROP_OVIRT_FOREIGN_MENU,
#endif
};

#ifdef HAVE_OVIRT
#endif

static gboolean remote_viewer_start(VirtViewerApp *self, GError **error, RemoteViewerState remoteViewerState);
#ifdef HAVE_SPICE_GTK
static gboolean remote_viewer_activate(VirtViewerApp *self, GError **error);
static void remote_viewer_window_added(GtkApplication *app, GtkWindow *w);
static void spice_foreign_menu_updated(RemoteViewer *self);
#endif

#ifdef HAVE_SPICE_CONTROLLER
static void foreign_menu_title_changed(SpiceCtrlForeignMenu *menu, GParamSpec *pspec, RemoteViewer *self);
#endif

// reconnect timer functions
static gboolean
virt_viewer_connect_timer(RemoteViewer *self)
{
    VirtViewerApp *app = VIRT_VIEWER_APP(self);
    // stop polling if app->is_polling is false. it happens when spice session connected
    if (!app->is_polling){
        virt_viewer_stop_reconnect_poll(self);
        return FALSE;
    }

    g_debug("Connect timer fired");
    // if app is not active then trying to connect
    gboolean created = FALSE;
    gboolean is_connected = FALSE;

    created = virt_viewer_app_create_session(app, "spice", NULL);
    if (!created)
        return TRUE;

    is_connected = virt_viewer_app_initial_connect(app, NULL);

    printf("%s active %i created %i is_connected %i \n",
           (const char *)__func__, virt_viewer_app_is_active(app), created, is_connected);

    return TRUE;
}

void
virt_viewer_start_reconnect_poll(RemoteViewer *self)
{
    VirtViewerApp *app = VIRT_VIEWER_APP(self);
    if (virt_viewer_app_is_active(app))
        return;

    RemoteViewerPrivate *priv = self->priv;

    g_debug("reconnect_poll: %d", priv->reconnect_poll);

    if (priv->reconnect_poll != 0)
        return;

    app->is_polling = TRUE;
    priv->reconnect_poll = g_timeout_add(RECONNECT_TIMEOUT, (GSourceFunc)virt_viewer_connect_timer, self);
}

void
virt_viewer_stop_reconnect_poll(RemoteViewer *self)
{
    VirtViewerApp *app = VIRT_VIEWER_APP(self);
    app->is_polling = FALSE;

    RemoteViewerPrivate *priv = self->priv;

    g_debug("reconnect_poll: %d", priv->reconnect_poll);

    if (priv->reconnect_poll == 0)
        return;

    g_source_remove(priv->reconnect_poll);
    priv->reconnect_poll = 0;
}

static void
remote_viewer_dispose (GObject *object)
{
    G_OBJECT_CLASS(remote_viewer_parent_class)->dispose (object);
}

static void
remote_viewer_deactivated(VirtViewerApp *app, gboolean connect_error)
{
    RemoteViewer *self = REMOTE_VIEWER(app);
    RemoteViewerPrivate *priv = self->priv;

    if (connect_error && priv->open_recent_dialog) {
        RemoteViewerState remoteViewerState = opt_manual_mode ? AUTH_DIALOG : VDI_DIALOG;
        if (virt_viewer_app_start(app, NULL, remoteViewerState)) {
            return;
        }
    }

    VIRT_VIEWER_APP_CLASS(remote_viewer_parent_class)->deactivated(app, connect_error);
}

static gchar **opt_args = NULL;
static char *opt_title = NULL;
static gboolean opt_controller = FALSE;

static void
remote_viewer_add_option_entries(VirtViewerApp *self, GOptionContext *context, GOptionGroup *group)
{
    static const GOptionEntry options[] = {
        { "title", 't', 0, G_OPTION_ARG_STRING, &opt_title,
          N_("Set window title"), NULL },
#ifdef HAVE_SPICE_GTK
        { "spice-controller", '\0', 0, G_OPTION_ARG_NONE, &opt_controller,
          N_("Open connection using Spice controller communication"), NULL },
#endif
        { G_OPTION_REMAINING, '\0', 0, G_OPTION_ARG_STRING_ARRAY, &opt_args,
          NULL, "URI|VV-FILE" },
        { NULL, 0, 0, G_OPTION_ARG_NONE, NULL, NULL, NULL }
    };

    VIRT_VIEWER_APP_CLASS(remote_viewer_parent_class)->add_option_entries(self, context, group);
    g_option_context_set_summary(context, _("Remote viewer client"));
    g_option_group_add_entries(group, options);

#ifdef HAVE_OVIRT
    g_option_context_add_group (context, ovirt_get_option_group ());
#endif
}

static gboolean
remote_viewer_local_command_line (GApplication   *gapp,
                                  gchar        ***args,
                                  int            *status)
{
    gboolean ret = FALSE;
    VirtViewerApp *app = VIRT_VIEWER_APP(gapp);
    RemoteViewer *self = REMOTE_VIEWER(app);

    ret = G_APPLICATION_CLASS(remote_viewer_parent_class)->local_command_line(gapp, args, status);
    if (ret)
        goto end;

    if (!opt_args) {
        self->priv->open_recent_dialog = TRUE;
    } else {
        if (g_strv_length(opt_args) > 1) {
            g_printerr(_("\nError: can't handle multiple URIs\n\n"));
            ret = TRUE;
            *status = 1;
            goto end;
        }

        g_object_set(app, "guri", opt_args[0], NULL);
    }

    if (opt_title && !opt_controller)
        g_object_set(app, "title", opt_title, NULL);

end:
    if (ret && *status)
        g_printerr(_("Run '%s --help' to see a full list of available command line options\n"), g_get_prgname());

    g_strfreev(opt_args);
    return ret;
}

static void
remote_viewer_get_property(GObject *object, guint property_id,
                           GValue *value G_GNUC_UNUSED,
                           GParamSpec *pspec)
{
#ifdef HAVE_OVIRT
    RemoteViewer *self = REMOTE_VIEWER(object);
    RemoteViewerPrivate *priv = self->priv;
#endif

    switch (property_id) {
#ifdef HAVE_OVIRT
    case PROP_OVIRT_FOREIGN_MENU:
        g_value_set_object(value, priv->ovirt_foreign_menu);
        break;
#endif

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
    }
}

static void
remote_viewer_class_init (RemoteViewerClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkApplicationClass *gtk_app_class = GTK_APPLICATION_CLASS(klass);
    VirtViewerAppClass *app_class = VIRT_VIEWER_APP_CLASS (klass);
    GApplicationClass *g_app_class = G_APPLICATION_CLASS(klass);

    g_type_class_add_private (klass, sizeof (RemoteViewerPrivate));

    object_class->get_property = remote_viewer_get_property;
    object_class->dispose = remote_viewer_dispose;

    g_app_class->local_command_line = remote_viewer_local_command_line;

    app_class->start = remote_viewer_start;
    app_class->deactivated = remote_viewer_deactivated;
    app_class->add_option_entries = remote_viewer_add_option_entries;
#ifdef HAVE_SPICE_GTK
    app_class->activate = remote_viewer_activate;
    gtk_app_class->window_added = remote_viewer_window_added;
#else
    (void) gtk_app_class;
#endif

#ifdef HAVE_OVIRT
    g_object_class_install_property(object_class,
                                    PROP_OVIRT_FOREIGN_MENU,
                                    g_param_spec_object("ovirt-foreign-menu",
                                                        "oVirt Foreign Menu",
                                                        "Object which is used as interface to oVirt",
                                                        OVIRT_TYPE_FOREIGN_MENU,
                                                        G_PARAM_READABLE | G_PARAM_STATIC_STRINGS));
#endif
}

static void
remote_viewer_init(RemoteViewer *self)
{
    self->priv = GET_PRIVATE(self);
}

RemoteViewer *
remote_viewer_new(void)
{
    return g_object_new(REMOTE_VIEWER_TYPE,
                        "application-id", "org.virt-manager.remote-viewer",
                        "flags", G_APPLICATION_NON_UNIQUE,
                        NULL);
}

static gboolean
remote_viewer_activate(VirtViewerApp *app, GError **error)
{
    gboolean ret = FALSE;

    g_return_val_if_fail(REMOTE_VIEWER_IS(app), FALSE);

    ret = VIRT_VIEWER_APP_CLASS(remote_viewer_parent_class)->activate(app, error);
    return ret;
}

static void
remote_viewer_window_added(GtkApplication *app,
                           GtkWindow *w)
{
    GTK_APPLICATION_CLASS(remote_viewer_parent_class)->window_added(app, w);
}

static void
remote_viewer_recent_add(gchar *uri, const gchar *mime_type)
{
    GtkRecentManager *recent;
    GtkRecentData meta = {
        .app_name     = (char*)"remote-viewer",
        .app_exec     = (char*)"remote-viewer %u",
        .mime_type    = (char*)mime_type,
    };

    if (uri == NULL)
        return;

    recent = gtk_recent_manager_get_default();
    meta.display_name = uri;
    if (!gtk_recent_manager_add_full(recent, uri, &meta))
        g_warning("Recent item couldn't be added");
}

static void
remote_viewer_session_connected(VirtViewerSession *session,
                                VirtViewerApp *self G_GNUC_UNUSED)
{
    gchar *uri = virt_viewer_session_get_uri(session);
    const gchar *mime = virt_viewer_session_mime_type(session);

    remote_viewer_recent_add(uri, mime);
    g_free(uri);
}

static gboolean
remote_viewer_start(VirtViewerApp *app, GError **err, RemoteViewerState remoteViewerState)
{
    printf("remote_viewer_start\n");
    g_return_val_if_fail(REMOTE_VIEWER_IS(app), FALSE);

    RemoteViewer *self = REMOTE_VIEWER(app);
    RemoteViewerPrivate *priv = self->priv;
    gboolean ret = FALSE;
    gchar *guri = NULL;
    gchar *user = NULL;
    gchar *password = NULL;
    gchar *ip = NULL;
    gchar *port = NULL;
    gboolean is_connect_to_prev_pool = FALSE;
    GError *error = NULL;

#ifdef HAVE_SPICE_CONTROLLER
    //g_signal_connect(app, "notify", G_CALLBACK(app_notified), self);
#endif
    switch (remoteViewerState) {
        case  AUTH_DIALOG:
            goto retry_auth;
        case VDI_DIALOG:
            goto retry_connnect_to_vm;
    }

    // remote connect dialog
retry_auth:
    {
        // Забираем из ui адрес и порт
        GtkResponseType dialog_window_response =
            remote_viewer_connect_dialog(&guri, &user, &password, &ip, &port, &is_connect_to_prev_pool);
        //printf("%s: is_connect_to_prev_pool %i\n", (const char *)__func__, is_connect_to_prev_pool);
        if (dialog_window_response == GTK_RESPONSE_CANCEL) {
            return FALSE;
        }
        else if (dialog_window_response == GTK_RESPONSE_CLOSE) {
            g_application_quit(G_APPLICATION(app));
            return FALSE;
        }
    }

    g_debug("Opening display to %s", guri);
    // После такого как забрали адресс с логином и паролем действуем в зависимости от opt_manual_mode
    // 1) в мануальном режиме сразу подключаемся к удаленноиу раб столу
    // 2) В дефолтном режиме вызываем vdi manager. В нем пользователь выберет машину для подключения
retry_connnect_to_vm:
    // instant connect attempt
    if (opt_manual_mode) {
        // credentials
        g_object_set(app, "guri", guri, NULL);

        setSpiceSessionCredentials(user, password);
        // Создание сессии
        if (!virt_viewer_app_create_session(app, "spice", &error))
            goto cleanup;

        g_signal_connect(virt_viewer_app_get_session(app), "session-connected",
                         G_CALLBACK(remote_viewer_session_connected), app);

        // Коннект к машине/*
        if (!virt_viewer_app_initial_connect(app, &error)) {
            if (error == NULL) {
                g_set_error_literal(&error,
                                    VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                                    _("Failed to initiate connection"));
            }
            goto cleanup;
        }

    } else {
        //Если is_connect_to_prev_pool true, то подключение к пред. запомненому пулу,
        // минуя vdi manager window
        if (!is_connect_to_prev_pool) {
            free_memory_safely(&guri);
            free_memory_safely(&user);
            free_memory_safely(&password);

            // show VDI manager window
            VirtViewerWindow *main_window = virt_viewer_app_get_main_window(app);
            GtkResponseType vdi_dialog_window_response =
                    vdi_manager_dialog(virt_viewer_window_get_window(main_window), &guri, &user, &password);

            if(vdi_dialog_window_response == GTK_RESPONSE_CANCEL) {
                goto cleanup;
            }
            else if(vdi_dialog_window_response == GTK_RESPONSE_CLOSE) {
                g_application_quit(G_APPLICATION(app));
                return FALSE;
            }
        }

        g_object_set(app, "guri", guri, NULL);
        setSpiceSessionCredentials(user, password);

        // start connect attempt timer
        virt_viewer_start_reconnect_poll(self);
    }
    // Показывается окно virt viewer // virt_viewer_app_default_start
    ret = VIRT_VIEWER_APP_CLASS(remote_viewer_parent_class)->start(app, &error, AUTH_DIALOG);

cleanup:
    //g_clear_object(&file);
    free_memory_safely(&guri);
    free_memory_safely(&user);
    free_memory_safely(&password);
    free_memory_safely(&ip);
    free_memory_safely(&port);

    if (!ret && priv->open_recent_dialog) {
        if (error != NULL) {
            virt_viewer_app_simple_message_dialog(app, _("Unable to connect: %s"), error->message); // -
        }
        g_clear_error(&error);
        goto retry_auth;
    }
    if (error != NULL)
        g_propagate_error(err, error);

    return ret;
}
