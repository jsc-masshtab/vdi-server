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
#include <spice-controller.h>
#include "virt-viewer-session-spice.h"
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

extern gboolean opt_manual_mode;

struct _RemoteViewerPrivate {
#ifdef HAVE_SPICE_GTK
    SpiceCtrlController *controller;
    SpiceCtrlForeignMenu *ctrl_foreign_menu;
#endif
#ifdef HAVE_OVIRT
    OvirtForeignMenu *ovirt_foreign_menu;
#endif
    gboolean open_recent_dialog;
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
static void foreign_menu_title_changed(SpiceCtrlForeignMenu *menu, GParamSpec *pspec, RemoteViewer *self);
#endif

static void
remote_viewer_dispose (GObject *object)
{
#if defined(HAVE_SPICE_GTK) || defined(HAVE_OVIRT)
    RemoteViewer *self = REMOTE_VIEWER(object);
    RemoteViewerPrivate *priv = self->priv;
#endif

#ifdef HAVE_SPICE_GTK
    if (priv->controller) {
        g_object_unref(priv->controller);
        priv->controller = NULL;
    }

    if (priv->ctrl_foreign_menu) {
        g_object_unref(priv->ctrl_foreign_menu);
        priv->ctrl_foreign_menu = NULL;
    }
#endif

#ifdef HAVE_OVIRT
    if (priv->ovirt_foreign_menu) {
        g_object_unref(priv->ovirt_foreign_menu);
        priv->ovirt_foreign_menu = NULL;
    }
#endif

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

#ifdef HAVE_SPICE_GTK
    if (opt_controller) {
        if (opt_args) {
            g_printerr(_("\nError: extra arguments given while using Spice controller\n\n"));
            ret = TRUE;
            *status = 1;
            goto end;
        }

        self->priv->controller = spice_ctrl_controller_new();
        self->priv->ctrl_foreign_menu = spice_ctrl_foreign_menu_new();

        g_object_set(self, "guest-name", "defined by Spice controller", NULL);

        g_signal_connect(self->priv->ctrl_foreign_menu, "notify::title",
                         G_CALLBACK(foreign_menu_title_changed),
                         self);
    }
#endif

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

#ifdef HAVE_SPICE_GTK
static void
foreign_menu_title_changed(SpiceCtrlForeignMenu *menu G_GNUC_UNUSED,
                           GParamSpec *pspec G_GNUC_UNUSED,
                           RemoteViewer *self)
{
    gboolean has_focus;

    g_object_get(G_OBJECT(self), "has-focus", &has_focus, NULL);
    /* FIXME: use a proper "new client connected" event
    ** a foreign menu client set the title when connecting,
    ** inform of focus state at that time.
    */
    spice_ctrl_foreign_menu_app_activated_msg(self->priv->ctrl_foreign_menu, has_focus);

    /* update menu title */
    spice_foreign_menu_updated(self);
}

static void
spice_ctrl_do_connect(SpiceCtrlController *ctrl G_GNUC_UNUSED,
                      VirtViewerApp *self)
{
    GError *error = NULL;

    if (!virt_viewer_app_initial_connect(self, &error)) {
        const gchar *msg = error ? error->message :
            _("Failed to initiate connection");
        virt_viewer_app_simple_message_dialog(self, msg);
        g_clear_error(&error);
    }
}

static void
spice_ctrl_show(SpiceCtrlController *ctrl G_GNUC_UNUSED, RemoteViewer *self)
{
    virt_viewer_app_show_display(VIRT_VIEWER_APP(self));
}

static void
spice_ctrl_hide(SpiceCtrlController *ctrl G_GNUC_UNUSED, RemoteViewer *self)
{
    virt_viewer_app_show_status(VIRT_VIEWER_APP(self), _("Display disabled by controller"));
}

static void
spice_menuitem_activate_cb(GtkMenuItem *mi, GObject *ctrl)
{
    SpiceCtrlMenuItem *menuitem = g_object_get_data(G_OBJECT(mi), "spice-menuitem");

    g_return_if_fail(menuitem != NULL);
    if (gtk_menu_item_get_submenu(mi))
        return;

    if (SPICE_CTRL_IS_CONTROLLER(ctrl))
        spice_ctrl_controller_menu_item_click_msg(SPICE_CTRL_CONTROLLER(ctrl), menuitem->id);
    else if (SPICE_CTRL_IS_FOREIGN_MENU(ctrl))
        spice_ctrl_foreign_menu_menu_item_click_msg(SPICE_CTRL_FOREIGN_MENU(ctrl), menuitem->id);
}

static GtkWidget *
ctrlmenu_to_gtkmenu (RemoteViewer *self, SpiceCtrlMenu *ctrlmenu, GObject *ctrl)
{
    GList *l;
    GtkWidget *menu = gtk_menu_new();
    guint n = 0;

    for (l = ctrlmenu->items; l != NULL; l = l->next) {
        SpiceCtrlMenuItem *menuitem = l->data;
        GtkWidget *item;
        char *s;
        if (menuitem->text == NULL) {
            g_warn_if_reached();
            continue;
        }

        for (s = menuitem->text; *s; s++)
            if (*s == '&')
                *s = '_';

        if (g_str_equal(menuitem->text, "-")) {
            item = gtk_separator_menu_item_new();
        } else if (menuitem->flags & CONTROLLER_MENU_FLAGS_CHECKED) {
            item = gtk_check_menu_item_new_with_mnemonic(menuitem->text);
            g_object_set(item, "active", TRUE, NULL);
        } else {
            item = gtk_menu_item_new_with_mnemonic(menuitem->text);
        }

        if (menuitem->flags & (CONTROLLER_MENU_FLAGS_GRAYED | CONTROLLER_MENU_FLAGS_DISABLED))
            gtk_widget_set_sensitive(item, FALSE);

        g_object_set_data_full(G_OBJECT(item), "spice-menuitem",
                               g_object_ref(menuitem), g_object_unref);
        g_signal_connect(item, "activate", G_CALLBACK(spice_menuitem_activate_cb), ctrl);
        gtk_menu_attach(GTK_MENU (menu), item, 0, 1, n, n + 1);
        n += 1;

        if (menuitem->submenu) {
            gtk_menu_item_set_submenu(GTK_MENU_ITEM(item),
                                      ctrlmenu_to_gtkmenu(self, menuitem->submenu, ctrl));
        }
    }

    if (n == 0) {
        g_object_ref_sink(menu);
        g_object_unref(menu);
        menu = NULL;
    }

    gtk_widget_show_all(menu);
    return menu;
}

static void
spice_menu_update(RemoteViewer *self, VirtViewerWindow *win)
{
    GtkWidget *menuitem = g_object_get_data(G_OBJECT(win), "spice-menu");
    SpiceCtrlMenu *menu;

    if (self->priv->controller == NULL)
        return;

    if (menuitem != NULL)
        gtk_widget_destroy(menuitem);

    {
        GtkMenuShell *shell = GTK_MENU_SHELL(gtk_builder_get_object(virt_viewer_window_get_builder(win), "top-menu"));
        menuitem = gtk_menu_item_new_with_label("Spice");
        gtk_menu_shell_append(shell, menuitem);
        g_object_set_data(G_OBJECT(win), "spice-menu", menuitem);
    }

    g_object_get(self->priv->controller, "menu", &menu, NULL);
    if (menu == NULL || g_list_length(menu->items) == 0) {
        gtk_widget_set_visible(menuitem, FALSE);
    } else {
        gtk_menu_item_set_submenu(GTK_MENU_ITEM(menuitem),
            ctrlmenu_to_gtkmenu(self, menu, G_OBJECT(self->priv->controller)));
        gtk_widget_set_visible(menuitem, TRUE);
    }

    if (menu != NULL)
        g_object_unref(menu);
}

static void
spice_menu_update_each(gpointer value,
                       gpointer user_data)
{
    spice_menu_update(REMOTE_VIEWER(user_data), VIRT_VIEWER_WINDOW(value));
}

static void
spice_ctrl_menu_updated(RemoteViewer *self)
{
    GList *windows = virt_viewer_app_get_windows(VIRT_VIEWER_APP(self));

    g_debug("Spice controller menu updated");

    g_list_foreach(windows, spice_menu_update_each, self);
}

static void
spice_foreign_menu_update(RemoteViewer *self, VirtViewerWindow *win)
{
    GtkWidget *menuitem = g_object_get_data(G_OBJECT(win), "foreign-menu");
    SpiceCtrlMenu *menu;

    if (self->priv->ctrl_foreign_menu == NULL)
        return;

    if (menuitem != NULL)
        gtk_widget_destroy(menuitem);

    {
        GtkMenuShell *shell = GTK_MENU_SHELL(gtk_builder_get_object(virt_viewer_window_get_builder(win), "top-menu"));
        const gchar *title = spice_ctrl_foreign_menu_get_title(self->priv->ctrl_foreign_menu);
        menuitem = gtk_menu_item_new_with_label(title);
        gtk_menu_shell_append(shell, menuitem);
        g_object_set_data(G_OBJECT(win), "foreign-menu", menuitem);
    }

    g_object_get(self->priv->ctrl_foreign_menu, "menu", &menu, NULL);
    if (menu == NULL || g_list_length(menu->items) == 0) {
        gtk_widget_set_visible(menuitem, FALSE);
    } else {
        gtk_menu_item_set_submenu(GTK_MENU_ITEM(menuitem),
            ctrlmenu_to_gtkmenu(self, menu, G_OBJECT(self->priv->ctrl_foreign_menu)));
        gtk_widget_set_visible(menuitem, TRUE);
    }
    g_object_unref(menu);
}

static void
spice_foreign_menu_update_each(gpointer value,
                               gpointer user_data)
{
    spice_foreign_menu_update(REMOTE_VIEWER(user_data), VIRT_VIEWER_WINDOW(value));
}

static void
spice_foreign_menu_updated(RemoteViewer *self)
{
    GList *windows = virt_viewer_app_get_windows(VIRT_VIEWER_APP(self));

    g_debug("Spice foreign menu updated");

    g_list_foreach(windows, spice_foreign_menu_update_each, self);
}

static SpiceSession *
remote_viewer_get_spice_session(RemoteViewer *self)
{
    VirtViewerSession *vsession = NULL;
    SpiceSession *session = NULL;

    g_object_get(self, "session", &vsession, NULL);
    g_return_val_if_fail(vsession != NULL, NULL);

    g_object_get(vsession, "spice-session", &session, NULL);

    g_object_unref(vsession);

    return session;
}

static void
app_notified(VirtViewerApp *app,
             GParamSpec *pspec,
             RemoteViewer *self)
{
    GValue value = G_VALUE_INIT;

    g_value_init(&value, pspec->value_type);
    g_object_get_property(G_OBJECT(app), pspec->name, &value);

    if (g_str_equal(pspec->name, "has-focus")) {
        if (self->priv->ctrl_foreign_menu)
            spice_ctrl_foreign_menu_app_activated_msg(self->priv->ctrl_foreign_menu, g_value_get_boolean(&value));
    }

    g_value_unset(&value);
}

static void
spice_ctrl_notified(SpiceCtrlController *ctrl,
                    GParamSpec *pspec,
                    RemoteViewer *self)
{
    SpiceSession *session = remote_viewer_get_spice_session(self);
    GValue value = G_VALUE_INIT;
    VirtViewerApp *app = VIRT_VIEWER_APP(self);

    g_return_if_fail(session != NULL);

    g_value_init(&value, pspec->value_type);
    g_object_get_property(G_OBJECT(ctrl), pspec->name, &value);

    if (g_str_equal(pspec->name, "host") ||
        g_str_equal(pspec->name, "port") ||
        g_str_equal(pspec->name, "password") ||
        g_str_equal(pspec->name, "ca-file") ||
        g_str_equal(pspec->name, "enable-smartcard") ||
        g_str_equal(pspec->name, "color-depth") ||
        g_str_equal(pspec->name, "disable-effects") ||
        g_str_equal(pspec->name, "enable-usbredir") ||
        g_str_equal(pspec->name, "secure-channels") ||
        g_str_equal(pspec->name, "proxy")) {
        g_object_set_property(G_OBJECT(session), pspec->name, &value);
    } else if (g_str_equal(pspec->name, "sport")) {
        g_object_set_property(G_OBJECT(session), "tls-port", &value);
    } else if (g_str_equal(pspec->name, "tls-ciphers")) {
        g_object_set_property(G_OBJECT(session), "ciphers", &value);
    } else if (g_str_equal(pspec->name, "host-subject")) {
        g_object_set_property(G_OBJECT(session), "cert-subject", &value);
    } else if (g_str_equal(pspec->name, "enable-usb-autoshare")) {
        VirtViewerSession *vsession = NULL;

        g_object_get(self, "session", &vsession, NULL);
        g_object_set_property(G_OBJECT(vsession), "auto-usbredir", &value);
        g_object_unref(G_OBJECT(vsession));
    } else if (g_str_equal(pspec->name, "usb-filter")) {
        SpiceUsbDeviceManager *manager;
        manager = spice_usb_device_manager_get(session, NULL);
        if (manager != NULL) {
            g_object_set_property(G_OBJECT(manager),
                                  "auto-connect-filter",
                                  &value);
        }
    } else if (g_str_equal(pspec->name, "title")) {
        g_object_set(app, "title", g_value_get_string(&value), NULL);
    } else if (g_str_equal(pspec->name, "display-flags")) {
        guint flags = g_value_get_uint(&value);
        gboolean fullscreen = !!(flags & CONTROLLER_SET_FULL_SCREEN);
        g_object_set(G_OBJECT(self), "fullscreen", fullscreen, NULL);
    } else if (g_str_equal(pspec->name, "menu")) {
        spice_ctrl_menu_updated(self);
    } else if (g_str_equal(pspec->name, "hotkeys")) {
        virt_viewer_app_set_hotkeys(app, g_value_get_string(&value));
    } else {
        gchar *content = g_strdup_value_contents(&value);

        g_debug("unimplemented property: %s=%s", pspec->name, content);
        g_free(content);
    }

    g_object_unref(session);
    g_value_unset(&value);
}

static void
spice_ctrl_foreign_menu_notified(SpiceCtrlForeignMenu *ctrl_foreign_menu G_GNUC_UNUSED,
                                 GParamSpec *pspec,
                                 RemoteViewer *self)
{
    if (g_str_equal(pspec->name, "menu")) {
        spice_foreign_menu_updated(self);
    }
}

static void
spice_ctrl_listen_async_cb(GObject *object,
                           GAsyncResult *res,
                           gpointer user_data)
{
    GError *error = NULL;
    VirtViewerApp *app = VIRT_VIEWER_APP(user_data);

    if (SPICE_CTRL_IS_CONTROLLER(object))
        spice_ctrl_controller_listen_finish(SPICE_CTRL_CONTROLLER(object), res, &error);
    else if (SPICE_CTRL_IS_FOREIGN_MENU(object)) {
        spice_ctrl_foreign_menu_listen_finish(SPICE_CTRL_FOREIGN_MENU(object), res, &error);
    } else
        g_warn_if_reached();

    if (error != NULL) {
        virt_viewer_app_simple_message_dialog(app,
                                              _("Controller connection failed: %s"),
                                              error->message);
        g_clear_error(&error);
        exit(EXIT_FAILURE); /* TODO: make start async? */
    }
}


static gboolean
remote_viewer_activate(VirtViewerApp *app, GError **error)
{
    RemoteViewer *self;
    gboolean ret = FALSE;

    g_return_val_if_fail(REMOTE_VIEWER_IS(app), FALSE);

    self = REMOTE_VIEWER(app);

    if (self->priv->controller) {
        SpiceSession *session = remote_viewer_get_spice_session(self);
        ret = spice_session_connect(session);
        g_object_unref(session);
    } else {
        ret = VIRT_VIEWER_APP_CLASS(remote_viewer_parent_class)->activate(app, error);
    }

    return ret;
}

static void
remote_viewer_window_added(GtkApplication *app,
                           GtkWindow *w)
{
    VirtViewerWindow *win = VIRT_VIEWER_WINDOW(
                                g_object_get_data(G_OBJECT(w), "virt-viewer-window"));
    spice_menu_update(REMOTE_VIEWER(app), win);
    spice_foreign_menu_update(REMOTE_VIEWER(app), win);

    GTK_APPLICATION_CLASS(remote_viewer_parent_class)->window_added(app, w);
}
#endif

#ifdef HAVE_OVIRT
static gboolean
parse_ovirt_uri(const gchar *uri_str, char **rest_uri, char **name, char **username)
{
    char *vm_name = NULL;
    char *rel_path;
    xmlURIPtr uri;
    gchar **path_elements;
    guint element_count;

    g_return_val_if_fail(uri_str != NULL, FALSE);
    g_return_val_if_fail(rest_uri != NULL, FALSE);
    g_return_val_if_fail(name != NULL, FALSE);

    uri = xmlParseURI(uri_str);
    g_return_val_if_fail(uri != NULL, FALSE);

    if (g_strcmp0(uri->scheme, "ovirt") != 0) {
        xmlFreeURI(uri);
        return FALSE;
    }

    if (username && uri->user)
        *username = g_strdup(uri->user);

    if (uri->path == NULL) {
        *name = NULL;
        *rest_uri = g_strdup(uri->server);
        xmlFreeURI(uri);
        return TRUE;
    }

    if (*uri->path != '/') {
        xmlFreeURI(uri);
        return FALSE;
    }

    /* extract VM name from path */
    path_elements = g_strsplit(uri->path, "/", -1);

    element_count = g_strv_length(path_elements);
    if (element_count == 0) {
        g_strfreev(path_elements);
        return FALSE;
    }
    vm_name = path_elements[element_count-1];
    path_elements[element_count-1] = NULL;

    /* build final URI */
    rel_path = g_strjoinv("/", path_elements);
    *rest_uri = g_strdup_printf("%s%s", uri->server, rel_path);
    *name = vm_name;
    g_free(rel_path);
    g_strfreev(path_elements);
    xmlFreeURI(uri);

    g_debug("oVirt base URI: %s", *rest_uri);
    g_debug("oVirt VM name: %s", *name);

    return TRUE;
}

// Функция получает логин пароль, и запихивает их в свойства
static gboolean
authenticate_cb(RestProxy *proxy, G_GNUC_UNUSED RestProxyAuth *auth,
                G_GNUC_UNUSED gboolean retrying, gpointer user_data)
{
    gchar *username = NULL;
    gchar *password = NULL;
    VirtViewerWindow *window;
    gboolean success = FALSE;
    gboolean kiosk = FALSE;

    g_object_get(proxy,
                 "username", &username,
                 NULL);

    g_object_get(G_OBJECT(user_data), "kiosk", &kiosk, NULL);

    if (username == NULL || *username == '\0')
        username = g_strdup(g_get_user_name());

    window = virt_viewer_app_get_main_window(VIRT_VIEWER_APP(user_data));
    do {
        success = virt_viewer_auth_collect_credentials(virt_viewer_window_get_window(window),
                                                       "oVirt",
                                                       NULL,
                                                       &username, &password);
    } while (kiosk && !success);

    if (success) {
        g_object_set(G_OBJECT(proxy),
                     "username", username,
                     "password", password,
                     NULL);
#ifdef HAVE_OVIRT_CANCEL
    } else {
        rest_proxy_auth_cancel(auth);
#endif
    }

    g_free(username);
    g_free(password);
    return success;
}

static void
ovirt_foreign_menu_update(GtkApplication *gtkapp, GtkWindow *gtkwin, G_GNUC_UNUSED gpointer data)
{
    RemoteViewer *self = REMOTE_VIEWER(gtkapp);
    VirtViewerWindow *win = g_object_get_data(G_OBJECT(gtkwin), "virt-viewer-window");
    GtkBuilder *builder = virt_viewer_window_get_builder(win);
    GtkWidget *menu = GTK_WIDGET(gtk_builder_get_object(builder, "menu-change-cd"));
    gtk_widget_set_visible(menu, self->priv->ovirt_foreign_menu != NULL);
}

static void
ovirt_foreign_menu_update_each(gpointer value,
                               gpointer user_data)
{
    ovirt_foreign_menu_update(GTK_APPLICATION(user_data),
                              virt_viewer_window_get_window(VIRT_VIEWER_WINDOW(value)),
                              NULL);
}

static void
ovirt_foreign_menu_updated(RemoteViewer *self)
{
    GList *windows = virt_viewer_app_get_windows(VIRT_VIEWER_APP(self));

    g_debug("Spice foreign menu updated");

    g_list_foreach(windows, ovirt_foreign_menu_update_each, self);
}

static void
virt_viewer_app_set_ovirt_foreign_menu(VirtViewerApp *app,
                                       OvirtForeignMenu *foreign_menu)
{
    RemoteViewer *self;
    g_return_if_fail(REMOTE_VIEWER_IS(app));
    g_return_if_fail(OVIRT_IS_FOREIGN_MENU(foreign_menu));

    self = REMOTE_VIEWER(app);
    g_clear_object(&self->priv->ovirt_foreign_menu);
    self->priv->ovirt_foreign_menu = foreign_menu;
    g_signal_connect(G_OBJECT(app), "window-added",
                     (GCallback)ovirt_foreign_menu_update, NULL);
    ovirt_foreign_menu_updated(self);
}


#endif /* HAVE_OVIRT */

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
    //GFile *file = NULL;
    gboolean ret = FALSE;
    gchar *guri = NULL;
    gchar *user = NULL;
    gchar *password = NULL;
    gchar *ip = NULL;
    gchar *port = NULL;
    GError *error = NULL;
    gchar *type = NULL;

#ifdef HAVE_SPICE_GTK
    g_signal_connect(app, "notify", G_CALLBACK(app_notified), self);
#endif
    switch (remoteViewerState) {
        case  AUTH_DIALOG: goto retry_dialog;
        case VDI_DIALOG: goto retry_vdi_dialog;
    }

    // remote connect dialog
retry_dialog:
    {
        VirtViewerWindow *main_window = virt_viewer_app_get_main_window(app);
        // Забираем из ui адрес и порт
        GtkResponseType dialogWindowResponse =
            remote_viewer_connect_dialog(virt_viewer_window_get_window(main_window), &guri, &user, &password,
                    &ip, &port);

        if(dialogWindowResponse == GTK_RESPONSE_CANCEL) {
            return FALSE;
        }
        else if(dialogWindowResponse == GTK_RESPONSE_CLOSE) {
            g_application_quit(G_APPLICATION(app));
            return FALSE;
        }

        if(!opt_manual_mode) {
            setVdiCredentials(user, password, ip, port);
            free_memory_safely(&guri);
            free_memory_safely(&user);
            free_memory_safely(&password);
        } else{
            g_object_set(app, "guri", guri, NULL);
        }
    }

    g_debug("Opening display to %s", guri);
    // После такого как забрали адресс с логином и паролем действуем в зависимости от opt_manual_mode
    // 1) в мануальном режиме сразу подключаемся к удаленноиу раб столу
    // 2) В дефолтном режиме вызываем vdi manager. В нем пользователь выберет машину для поодключения
retry_vdi_dialog:
    if(!opt_manual_mode){

        VirtViewerWindow *main_window = virt_viewer_app_get_main_window(app);
        GtkResponseType dialogWindowResponse =
                vdi_manager_dialog(virt_viewer_window_get_window(main_window), &guri, &user, &password);

        if(dialogWindowResponse == GTK_RESPONSE_CANCEL) {
            goto cleanup;
        }
        else if(dialogWindowResponse == GTK_RESPONSE_CLOSE) {
            g_application_quit(G_APPLICATION(app));  
            return FALSE;
        }

        g_object_set(app, "guri", guri, NULL);    
    }

    // Создание сессии
    type = g_strdup("spice");
    if (!virt_viewer_app_create_session(app, type, &error))
        goto cleanup;
    setSpiceSessionCredentials(user, password);

    g_signal_connect(virt_viewer_app_get_session(app), "session-connected",
                     G_CALLBACK(remote_viewer_session_connected), app);

    // Коннект к машине
    if (!virt_viewer_app_initial_connect(app, &error)) {
        if (error == NULL) {
            g_set_error_literal(&error,
                                VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                                _("Failed to initiate connection"));
        }
        goto cleanup;
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
    free_memory_safely(&type);

    if (!ret && priv->open_recent_dialog) {
        if (error != NULL) {
            virt_viewer_app_simple_message_dialog(app, _("Unable to connect: %s"), error->message); // -
        }
        g_clear_error(&error);
        goto retry_dialog;
    }
    if (error != NULL)
        g_propagate_error(err, error);

    return ret;
}

