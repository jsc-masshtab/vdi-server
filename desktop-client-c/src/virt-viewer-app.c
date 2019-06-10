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

#include <gdk/gdkkeysyms.h>
#include <gtk/gtk.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <locale.h>
#include <gio/gio.h>
#include <glib/gprintf.h>
#include <glib/gi18n.h>
#include <errno.h>

#ifdef HAVE_SYS_SOCKET_H
#include <sys/socket.h>
#endif

#ifdef HAVE_SYS_UN_H
#include <sys/un.h>
#endif

#ifdef HAVE_WINDOWS_H
#include <windows.h>
#endif

#include "virt-viewer-app.h"
#include "virt-viewer-resources.h"
#include "virt-viewer-auth.h"
#include "virt-viewer-window.h"
#include "virt-viewer-session.h"
#include "virt-viewer-util.h"
#ifdef HAVE_GTK_VNC
#include "virt-viewer-session-vnc.h"
#endif
#ifdef HAVE_SPICE_GTK
#include "virt-viewer-session-spice.h"
#endif

gboolean doDebug = FALSE;

/* Signal handlers for about dialog */
void virt_viewer_app_about_close(GtkWidget *dialog, VirtViewerApp *self);
void virt_viewer_app_about_delete(GtkWidget *dialog, void *dummy, VirtViewerApp *self);


/* Internal methods */
static void virt_viewer_app_connected(VirtViewerSession *session,
                                      VirtViewerApp *self);
static void virt_viewer_app_initialized(VirtViewerSession *session,
                                        VirtViewerApp *self);
static void virt_viewer_app_disconnected(VirtViewerSession *session,
                                         const gchar *msg,
                                         VirtViewerApp *self);
static void virt_viewer_app_auth_refused(VirtViewerSession *session,
                                         const char *msg,
                                         VirtViewerApp *self);
static void virt_viewer_app_auth_unsupported(VirtViewerSession *session,
                                             const char *msg,
                                        VirtViewerApp *self);
static void virt_viewer_app_usb_failed(VirtViewerSession *session,
                                       const char *msg,
                                       VirtViewerApp *self);

static void virt_viewer_app_server_cut_text(VirtViewerSession *session,
                                            const gchar *text,
                                            VirtViewerApp *self);
static void virt_viewer_app_bell(VirtViewerSession *session,
                                 VirtViewerApp *self);

static void virt_viewer_app_cancelled(VirtViewerSession *session,
                                      VirtViewerApp *self);

static void virt_viewer_app_channel_open(VirtViewerSession *session,
                                         VirtViewerSessionChannel *channel,
                                         VirtViewerApp *self);
static void virt_viewer_app_update_pretty_address(VirtViewerApp *self);
static void virt_viewer_app_set_fullscreen(VirtViewerApp *self, gboolean fullscreen);
static void virt_viewer_app_update_menu_displays(VirtViewerApp *self);
static void virt_viewer_update_smartcard_accels(VirtViewerApp *self);
static void virt_viewer_app_add_option_entries(VirtViewerApp *self, GOptionContext *context, GOptionGroup *group);


struct _VirtViewerAppPrivate {
    VirtViewerWindow *main_window;
    GtkWidget *main_notebook;
    GList *windows;
    GHashTable *displays;
    GHashTable *initial_display_map;
    gchar *clipboard;
    GtkWidget *preferences;
    GtkFileChooser *preferences_shared_folder;
    GResource *resource;
    gboolean direct;
    gboolean verbose;
    gboolean enable_accel;
    gboolean authretry;
    gboolean started;
    gboolean fullscreen;
    gboolean attach;
    gboolean quitting;
    gboolean kiosk;

    VirtViewerSession *session;
    gboolean active;
    gboolean connected;
    gboolean cancelled;
    char *unixsock;
    char *guri; /* prefered over ghost:gport */
    char *ghost;
    char *gport;
    char *gtlsport;
    char *host; /* ssh */
    int port;/* ssh */
    char *user; /* ssh */
    char *transport;
    char *pretty_address;
    gchar *guest_name;
    gboolean grabbed;
    char *title;
    char *uuid;

    gint focused;
    GKeyFile *config;
    gchar *config_file;

    guint insert_smartcard_accel_key;
    GdkModifierType insert_smartcard_accel_mods;
    guint remove_smartcard_accel_key;
    GdkModifierType remove_smartcard_accel_mods;
    gboolean quit_on_disconnect;
};


G_DEFINE_ABSTRACT_TYPE(VirtViewerApp, virt_viewer_app, GTK_TYPE_APPLICATION)
#define GET_PRIVATE(o)                                                        \
    (G_TYPE_INSTANCE_GET_PRIVATE ((o), VIRT_VIEWER_TYPE_APP, VirtViewerAppPrivate))

enum {
    PROP_0,
    PROP_VERBOSE,
    PROP_SESSION,
    PROP_GUEST_NAME,
    PROP_GURI,
    PROP_FULLSCREEN,
    PROP_TITLE,
    PROP_ENABLE_ACCEL,
    PROP_HAS_FOCUS,
    PROP_KIOSK,
    PROP_QUIT_ON_DISCONNECT,
    PROP_UUID,
};

void
virt_viewer_app_set_debug(gboolean debug)
{
    if (debug) {
        const gchar *doms = g_getenv("G_MESSAGES_DEBUG");
        if (!doms) {
            g_setenv("G_MESSAGES_DEBUG", G_LOG_DOMAIN, 1);
        } else if (!g_str_equal(doms, "all") &&
                   !strstr(doms, G_LOG_DOMAIN)) {
            gchar *newdoms = g_strdup_printf("%s %s", doms, G_LOG_DOMAIN);
            g_setenv("G_MESSAGES_DEBUG", newdoms, 1);
            g_free(newdoms);
        }
    }
    doDebug = debug;
}

static GtkWidget*
virt_viewer_app_make_message_dialog(VirtViewerApp *self,
                                    const char *fmt, ...)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), NULL);
    GtkWindow *window = GTK_WINDOW(virt_viewer_window_get_window(self->priv->main_window));
    GtkWidget *dialog;
    char *msg;
    va_list vargs;

    va_start(vargs, fmt);
    msg = g_strdup_vprintf(fmt, vargs);
    va_end(vargs);

    dialog = gtk_message_dialog_new(window,
                                    GTK_DIALOG_MODAL |
                                    GTK_DIALOG_DESTROY_WITH_PARENT,
                                    GTK_MESSAGE_ERROR,
                                    GTK_BUTTONS_OK,
                                    "%s",
                                    msg);

    g_free(msg);

    return dialog;
}

void
virt_viewer_app_simple_message_dialog(VirtViewerApp *self,
                                      const char *fmt, ...)
{
    GtkWidget *dialog;
    char *msg;
    va_list vargs;

    va_start(vargs, fmt);
    msg = g_strdup_vprintf(fmt, vargs);
    va_end(vargs);

    dialog = virt_viewer_app_make_message_dialog(self, msg);
    gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_destroy(dialog);

    g_free(msg);
}

static void
virt_viewer_app_save_config(VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv = self->priv;
    GError *error = NULL;
    gchar *dir, *data;

    dir = g_path_get_dirname(priv->config_file);
    if (g_mkdir_with_parents(dir, S_IRWXU) == -1)
        g_warning("failed to create config directory");
    g_free(dir);

    if (priv->uuid && priv->guest_name && g_key_file_has_group(priv->config, priv->uuid)) {
        // if there's no comment for this uuid settings group, add a comment
        // with the vm name so user can make sense of it later.
        gchar *comment = g_key_file_get_comment(priv->config, priv->uuid, NULL, &error);
        if (error) {
            g_debug("Unable to get comment from key file: %s", error->message);
            g_clear_error(&error);
        } else {
            if (!comment || *comment == '\0')
                g_key_file_set_comment(priv->config, priv->uuid, NULL, priv->guest_name, NULL);
        }
        g_free(comment);
    }

    if ((data = g_key_file_to_data(priv->config, NULL, &error)) == NULL ||
        !g_file_set_contents(priv->config_file, data, -1, &error)) {
        g_warning("Couldn't save configuration: %s", error->message);
        g_clear_error(&error);
    }
    g_free(data);
}

static void
virt_viewer_app_quit(VirtViewerApp *self)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(self));
    g_return_if_fail(!self->priv->kiosk);
    VirtViewerAppPrivate *priv = self->priv;

    virt_viewer_app_save_config(self);

    if (priv->session) {
        virt_viewer_session_close(VIRT_VIEWER_SESSION(priv->session));
        if (priv->connected) {
            priv->quitting = TRUE;
            return;
        }
    }

    g_application_quit(G_APPLICATION(self));
}

static gint
get_n_client_monitors()
{
    return gdk_screen_get_n_monitors(gdk_screen_get_default());
}

GList* virt_viewer_app_get_initial_displays(VirtViewerApp* self)
{
    if (!self->priv->initial_display_map) {
        GList *l = NULL;
        gint i;
        gint n = get_n_client_monitors();

        for (i = 0; i < n; i++) {
            l = g_list_append(l, GINT_TO_POINTER(i));
        }
        return l;
    }
    return g_hash_table_get_keys(self->priv->initial_display_map);
}

static gint virt_viewer_app_get_first_monitor(VirtViewerApp *self)
{
    if (self->priv->fullscreen && self->priv->initial_display_map) {
        gint first = G_MAXINT;
        GHashTableIter iter;
        gpointer key, value;
        g_hash_table_iter_init(&iter, self->priv->initial_display_map);
        while (g_hash_table_iter_next(&iter, &key, &value)) {
            gint monitor = GPOINTER_TO_INT(key);
            first = MIN(first, monitor);
        }
        return first;
    }
    return 0;
}

gint virt_viewer_app_get_initial_monitor_for_display(VirtViewerApp* self, gint display)
{
    gint monitor = display;

    if (self->priv->initial_display_map) {
        gpointer value = NULL;
        if (g_hash_table_lookup_extended(self->priv->initial_display_map, GINT_TO_POINTER(display), NULL, &value)) {
            monitor = GPOINTER_TO_INT(value);
        } else {
            monitor = -1;
        }
    }
    if (monitor >= get_n_client_monitors()) {
        g_debug("monitor for display %d does not exist", display);
        monitor = -1;
    }

    return monitor;
}

static void
app_window_try_fullscreen(VirtViewerApp *self G_GNUC_UNUSED,
                          VirtViewerWindow *win, gint nth)
{
    gint monitor = virt_viewer_app_get_initial_monitor_for_display(self, nth);
    if (monitor == -1) {
        g_debug("skipping fullscreen for display %d", nth);
        return;
    }

    virt_viewer_window_enter_fullscreen(win, monitor);
}

static GHashTable*
virt_viewer_app_get_monitor_mapping_for_section(VirtViewerApp *self, const gchar *section)
{
    GError *error = NULL;
    gsize nmappings = 0;
    gchar **mappings = NULL;
    GHashTable *mapping = NULL;

    mappings = g_key_file_get_string_list(self->priv->config,
                                          section, "monitor-mapping", &nmappings, &error);
    if (error) {
        if (error->code != G_KEY_FILE_ERROR_GROUP_NOT_FOUND
            && error->code != G_KEY_FILE_ERROR_KEY_NOT_FOUND)
            g_warning("Error reading monitor assignments for %s: %s", section, error->message);
        g_clear_error(&error);
    } else {
        mapping = virt_viewer_parse_monitor_mappings(mappings, nmappings, get_n_client_monitors());
    }
    g_strfreev(mappings);

    return mapping;
}

static
void virt_viewer_app_apply_monitor_mapping(VirtViewerApp *self)
{
    GHashTable *mapping = NULL;

    // apply mapping only in fullscreen
    if (!virt_viewer_app_get_fullscreen(self))
        return;

    mapping = virt_viewer_app_get_monitor_mapping_for_section(self, self->priv->uuid);
    if (!mapping) {
        g_debug("No guest-specific fullscreen config, using fallback");
        mapping = virt_viewer_app_get_monitor_mapping_for_section(self, "fallback");
    }

    if (self->priv->initial_display_map)
        g_hash_table_unref(self->priv->initial_display_map);

    self->priv->initial_display_map = mapping;

    // if we're changing our initial display map, move any existing windows to
    // the appropriate monitors according to the per-vm configuration
    if (mapping) {
        GList *l;
        gint i = 0;

        for (l = self->priv->windows; l; l = l->next) {
            app_window_try_fullscreen(self, VIRT_VIEWER_WINDOW(l->data), i);
            i++;
        }
    }
}

static
void virt_viewer_app_set_uuid_string(VirtViewerApp *self, const gchar *uuid_string)
{
    if (g_strcmp0(self->priv->uuid, uuid_string) == 0)
        return;

    g_debug("%s: UUID changed to %s", G_STRFUNC, uuid_string);

    g_free(self->priv->uuid);
    self->priv->uuid = g_strdup(uuid_string);

    virt_viewer_app_apply_monitor_mapping(self);
}

void
virt_viewer_app_maybe_quit(VirtViewerApp *self, VirtViewerWindow *window)
{
    GError *error = NULL;

    if (self->priv->kiosk) {
        g_warning("The app is in kiosk mode and can't quit");
        return;
    }

    gboolean ask = g_key_file_get_boolean(self->priv->config,
                                          "virt-viewer", "ask-quit", &error);
    if (error) {
        ask = TRUE;
        g_clear_error(&error);
    }

    if (ask) {
        GtkWidget *dialog =
            gtk_message_dialog_new (virt_viewer_window_get_window(window),
                    GTK_DIALOG_DESTROY_WITH_PARENT,
                    GTK_MESSAGE_QUESTION,
                    GTK_BUTTONS_OK_CANCEL,
                    _("Do you want to close the session?"));

        GtkWidget *check = gtk_check_button_new_with_label(_("Do not ask me again"));
        gtk_container_add(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dialog))), check);
        gtk_widget_show(check);

        gtk_dialog_set_default_response (GTK_DIALOG(dialog), GTK_RESPONSE_CANCEL);
        gint result = gtk_dialog_run(GTK_DIALOG(dialog));

        gboolean dont_ask = FALSE;
        g_object_get(check, "active", &dont_ask, NULL);
        g_key_file_set_boolean(self->priv->config,
                    "virt-viewer", "ask-quit", !dont_ask);

        gtk_widget_destroy(dialog);
        switch (result) {
            case GTK_RESPONSE_OK:
                virt_viewer_app_quit(self);
                break;
            default:
                break;
        }
    } else {
        virt_viewer_app_quit(self);
    }

}

static void count_window_visible(gpointer value,
                                 gpointer user_data)
{
    GtkWindow *win = virt_viewer_window_get_window(VIRT_VIEWER_WINDOW(value));
    guint *n = (guint*)user_data;

    if (gtk_widget_get_visible(GTK_WIDGET(win)))
        *n += 1;
}

static guint
virt_viewer_app_get_n_windows_visible(VirtViewerApp *self)
{
    guint n = 0;
    g_list_foreach(self->priv->windows, count_window_visible, &n);
    return n;
}

gboolean
virt_viewer_app_window_set_visible(VirtViewerApp *self,
                                   VirtViewerWindow *window,
                                   gboolean visible)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);
    g_return_val_if_fail(VIRT_VIEWER_IS_WINDOW(window), FALSE);

    if (visible) {
        virt_viewer_window_show(window);
        return TRUE;
    } else {
        if (virt_viewer_app_get_n_windows_visible(self) > 1) {
            virt_viewer_window_hide(window);
            return FALSE;
        }

        virt_viewer_app_maybe_quit(self, window);
    }

    return FALSE;
}

static void hide_one_window(gpointer value,
                            gpointer user_data G_GNUC_UNUSED)
{
    VirtViewerApp* self = VIRT_VIEWER_APP(user_data);
    VirtViewerAppPrivate *priv = self->priv;
    gboolean connect_error = !priv->connected && !priv->cancelled;

    if (connect_error || self->priv->main_window != value)
        virt_viewer_window_hide(VIRT_VIEWER_WINDOW(value));
}

static void
virt_viewer_app_hide_all_windows(VirtViewerApp *app)
{
    g_list_foreach(app->priv->windows, hide_one_window, app);
}

G_MODULE_EXPORT void
virt_viewer_app_about_close(GtkWidget *dialog,
                            VirtViewerApp *self G_GNUC_UNUSED)
{
    gtk_widget_hide(dialog);
    gtk_widget_destroy(dialog);
}

G_MODULE_EXPORT void
virt_viewer_app_about_delete(GtkWidget *dialog,
                             void *dummy G_GNUC_UNUSED,
                             VirtViewerApp *self G_GNUC_UNUSED)
{
    gtk_widget_hide(dialog);
    gtk_widget_destroy(dialog);
}

#if defined(HAVE_SOCKETPAIR) && defined(HAVE_FORK)

static int
virt_viewer_app_open_tunnel(const char **cmd)
{
    int fd[2];
    pid_t pid;

    if (socketpair(PF_UNIX, SOCK_STREAM, 0, fd) < 0)
        return -1;

    pid = fork();
    if (pid == -1) {
        close(fd[0]);
        close(fd[1]);
        return -1;
    }

    if (pid == 0) { /* child */
        close(fd[0]);
        close(0);
        close(1);
        if (dup(fd[1]) < 0)
            _exit(1);
        if (dup(fd[1]) < 0)
            _exit(1);
        close(fd[1]);
        execvp("ssh", (char *const*)cmd);
        _exit(1);
    }
    close(fd[1]);
    return fd[0];
}


static int
virt_viewer_app_open_tunnel_ssh(const char *sshhost,
                                int sshport,
                                const char *sshuser,
                                const char *host,
                                const char *port,
                                const char *unixsock)
{
    const char *cmd[10];
    char portstr[50];
    int n = 0;
    GString *cat;

    cmd[n++] = "ssh";
    if (sshport) {
        cmd[n++] = "-p";
        sprintf(portstr, "%d", sshport);
        cmd[n++] = portstr;
    }
    if (sshuser) {
        cmd[n++] = "-l";
        cmd[n++] = sshuser;
    }
    cmd[n++] = sshhost;

    cat = g_string_new("if (command -v socat) >/dev/null 2>&1");

    g_string_append(cat, "; then socat - ");
    if (port)
        g_string_append_printf(cat, "TCP:%s:%s", host, port);
    else
        g_string_append_printf(cat, "UNIX-CONNECT:%s", unixsock);

    g_string_append(cat, "; else nc ");
    if (port)
        g_string_append_printf(cat, "%s %s", host, port);
    else
        g_string_append_printf(cat, "-U %s", unixsock);

    g_string_append(cat, "; fi");

    cmd[n++] = cat->str;
    cmd[n++] = NULL;

    n = virt_viewer_app_open_tunnel(cmd);
    g_string_free(cat, TRUE);

    return n;
}

static int
virt_viewer_app_open_unix_sock(const char *unixsock, GError **error)
{
    struct sockaddr_un addr;
    int fd;

    if (strlen(unixsock) + 1 > sizeof(addr.sun_path)) {
        g_set_error(error, VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Address is too long for unix socket_path: %s"), unixsock);
        return -1;
    }

    memset(&addr, 0, sizeof addr);
    addr.sun_family = AF_UNIX;
    strcpy(addr.sun_path, unixsock);

    if ((fd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
        g_set_error(error, VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Creating unix socket failed: %s"), g_strerror(errno));
        return -1;
    }

    if (connect(fd, (struct sockaddr *)&addr, sizeof addr) < 0) {
        g_set_error(error, VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Connecting to unix socket failed: %s"), g_strerror(errno));
        close(fd);
        return -1;
    }

    return fd;
}

#endif /* defined(HAVE_SOCKETPAIR) && defined(HAVE_FORK) */

void
virt_viewer_app_trace(VirtViewerApp *self,
                      const char *fmt, ...)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(self));
    va_list ap;
    VirtViewerAppPrivate *priv = self->priv;

    if (doDebug) {
        va_start(ap, fmt);
        g_logv(G_LOG_DOMAIN, G_LOG_LEVEL_DEBUG, fmt, ap);
        va_end(ap);
    }

    if (priv->verbose) {
        va_start(ap, fmt);
        g_vprintf(fmt, ap);
        va_end(ap);
        g_print("\n");
    }
}

static const gchar*
virt_viewer_app_get_title(VirtViewerApp *self)
{
    const gchar *title;
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), NULL);

    title = self->priv->title;
    if (!title)
        title = self->priv->guest_name;
    if (!title)
        title = self->priv->guri;

    return title;
}

static void
virt_viewer_app_set_window_subtitle(VirtViewerApp *app,
                                    VirtViewerWindow *window,
                                    int nth)
{
    gchar *subtitle = NULL;
    const gchar *title = virt_viewer_app_get_title(app);

    if (title != NULL) {
        gchar *d = strstr(title, "%d");
        if (d != NULL) {
            *d = '\0';
            subtitle = g_strdup_printf("%s%d%s", title, nth + 1, d + 2);
            *d = '%';
        } else
            subtitle = g_strdup_printf("%s (%d)", title, nth + 1);
    }

    g_object_set(window, "subtitle", subtitle, NULL);
    g_free(subtitle);
}

static void
set_title(gpointer value,
          gpointer user_data)
{
    VirtViewerApp *app = user_data;
    VirtViewerWindow *window = value;
    VirtViewerDisplay *display = virt_viewer_window_get_display(window);

    if (!display)
        return;

    virt_viewer_app_set_window_subtitle(app, window,
                                        virt_viewer_display_get_nth(display));
}

static void
virt_viewer_app_set_all_window_subtitles(VirtViewerApp *app)
{
    g_list_foreach(app->priv->windows, set_title, app);
}

static void update_title(gpointer value,
                         gpointer user_data G_GNUC_UNUSED)
{
    virt_viewer_window_update_title(VIRT_VIEWER_WINDOW(value));
}

static void
virt_viewer_app_update_title(VirtViewerApp *self)
{
    g_list_foreach(self->priv->windows, update_title, NULL);
}

static void set_usb_options_sensitive(gpointer value,
                                      gpointer user_data)
{
    virt_viewer_window_set_usb_options_sensitive(VIRT_VIEWER_WINDOW(value),
                                                 GPOINTER_TO_INT(user_data));
}

static void
virt_viewer_app_set_usb_options_sensitive(VirtViewerApp *self, gboolean sensitive)
{
    g_list_foreach(self->priv->windows, set_usb_options_sensitive,
                   GINT_TO_POINTER(sensitive));
}

static void
set_menus_sensitive(gpointer value, gpointer user_data)
{
    virt_viewer_window_set_menus_sensitive(VIRT_VIEWER_WINDOW(value),
                                           GPOINTER_TO_INT(user_data));
}

void
virt_viewer_app_set_menus_sensitive(VirtViewerApp *self, gboolean sensitive)
{
    g_list_foreach(self->priv->windows, set_menus_sensitive, GINT_TO_POINTER(sensitive));
}

static VirtViewerWindow *
virt_viewer_app_get_nth_window(VirtViewerApp *self, gint nth)
{
    GList *l;
    for (l = self->priv->windows; l; l = l->next) {
        VirtViewerDisplay *display = virt_viewer_window_get_display(l->data);
        if (display
            && (virt_viewer_display_get_nth(display) == nth)) {
            return l->data;
        }
    }
    return NULL;
}

static void
viewer_window_visible_cb(GtkWidget *widget G_GNUC_UNUSED,
                         gpointer user_data)
{
    virt_viewer_app_update_menu_displays(VIRT_VIEWER_APP(user_data));
}

static gboolean
viewer_window_focus_in_cb(GtkWindow *window G_GNUC_UNUSED,
                          GdkEvent *event G_GNUC_UNUSED,
                          VirtViewerApp *self)
{
    self->priv->focused += 1;

    if (self->priv->focused == 1)
        g_object_notify(G_OBJECT(self), "has-focus");

    return FALSE;
}

static gboolean
viewer_window_focus_out_cb(GtkWindow *window G_GNUC_UNUSED,
                           GdkEvent *event G_GNUC_UNUSED,
                           VirtViewerApp *self)
{
    self->priv->focused -= 1;
    g_warn_if_fail(self->priv->focused >= 0);

    if (self->priv->focused <= 0)
        g_object_notify(G_OBJECT(self), "has-focus");

    return FALSE;
}

static gboolean
virt_viewer_app_has_usbredir(VirtViewerApp *self)
{
    return virt_viewer_app_has_session(self) &&
           virt_viewer_session_get_has_usbredir(virt_viewer_app_get_session(self));
}

static VirtViewerWindow*
virt_viewer_app_window_new(VirtViewerApp *self, gint nth)
{
    VirtViewerWindow* window;
    GtkWindow *w;

    window = virt_viewer_app_get_nth_window(self, nth);
    if (window)
        return window;

    window = g_object_new(VIRT_VIEWER_TYPE_WINDOW, "app", self, NULL);
    virt_viewer_window_set_kiosk(window, self->priv->kiosk);
    if (self->priv->main_window)
        virt_viewer_window_set_zoom_level(window, virt_viewer_window_get_zoom_level(self->priv->main_window));

    self->priv->windows = g_list_append(self->priv->windows, window);
    virt_viewer_app_set_window_subtitle(self, window, nth);
    virt_viewer_app_update_menu_displays(self);
    virt_viewer_window_set_usb_options_sensitive(window, virt_viewer_app_has_usbredir(self));

    w = virt_viewer_window_get_window(window);
    g_object_set_data(G_OBJECT(w), "virt-viewer-window", window);
    gtk_application_add_window(GTK_APPLICATION(self), w);

    if (self->priv->fullscreen)
        app_window_try_fullscreen(self, window, nth);

    g_signal_connect(w, "hide", G_CALLBACK(viewer_window_visible_cb), self);
    g_signal_connect(w, "show", G_CALLBACK(viewer_window_visible_cb), self);
    g_signal_connect(w, "focus-in-event", G_CALLBACK(viewer_window_focus_in_cb), self);
    g_signal_connect(w, "focus-out-event", G_CALLBACK(viewer_window_focus_out_cb), self);
    return window;
}

static VirtViewerWindow *
ensure_window_for_display(VirtViewerApp *self, VirtViewerDisplay *display)
{
    gint nth = virt_viewer_display_get_nth(display);
    VirtViewerWindow *win = virt_viewer_app_get_nth_window(self, nth);
    if (win == NULL) {
        GList *l = self->priv->windows;

        /* There should always be at least a main window created at startup */
        g_return_val_if_fail(l != NULL, NULL);
        /* if there's a window that doesn't yet have an associated display, use
         * that window */
        for (; l; l = l->next) {
            if (virt_viewer_window_get_display(VIRT_VIEWER_WINDOW(l->data)) == NULL)
                break;
        }
        if (l && virt_viewer_window_get_display(VIRT_VIEWER_WINDOW(l->data)) == NULL) {
            win = VIRT_VIEWER_WINDOW(l->data);
            g_debug("Found a window without a display, reusing for display #%d", nth);
            if (self->priv->fullscreen && !self->priv->kiosk)
                app_window_try_fullscreen(self, win, nth);
        } else {
            win = virt_viewer_app_window_new(self, nth);
        }

        virt_viewer_window_set_display(win, display);
    }
    virt_viewer_app_set_window_subtitle(self, win, nth);

    return win;
}

static void
display_show_hint(VirtViewerDisplay *display,
                  GParamSpec *pspec G_GNUC_UNUSED,
                  gpointer user_data G_GNUC_UNUSED)
{
    VirtViewerApp *self = virt_viewer_session_get_app(virt_viewer_display_get_session(display));
    VirtViewerNotebook *nb;
    VirtViewerWindow *win;
    gint nth;
    guint hint;

    g_object_get(display,
                 "nth-display", &nth,
                 "show-hint", &hint,
                 NULL);

    win = virt_viewer_app_get_nth_window(self, nth);

    if (self->priv->fullscreen &&
        nth >= get_n_client_monitors()) {
        if (win)
            virt_viewer_window_hide(win);
    } else if (hint & VIRT_VIEWER_DISPLAY_SHOW_HINT_DISABLED) {
        if (win)
            virt_viewer_window_hide(win);
    } else {
        if (hint & VIRT_VIEWER_DISPLAY_SHOW_HINT_READY) {
            win = ensure_window_for_display(self, display);
            nb = virt_viewer_window_get_notebook(win);
            virt_viewer_notebook_show_display(nb);
            virt_viewer_window_show(win);
        } else {
            if (!self->priv->kiosk && win) {
                nb = virt_viewer_window_get_notebook(win);
                virt_viewer_notebook_show_status(nb, _("Waiting for display %d..."), nth + 1);
            }
        }
    }
    virt_viewer_app_update_menu_displays(self);
}

static void
virt_viewer_app_display_added(VirtViewerSession *session G_GNUC_UNUSED,
                              VirtViewerDisplay *display,
                              VirtViewerApp *self)
{
    gint nth;

    g_object_get(display, "nth-display", &nth, NULL);

    g_debug("Insert display %d %p", nth, display);
    g_hash_table_insert(self->priv->displays, GINT_TO_POINTER(nth), g_object_ref(display));

    g_signal_connect(display, "notify::show-hint",
                     G_CALLBACK(display_show_hint), NULL);
    g_object_notify(G_OBJECT(display), "show-hint"); /* call display_show_hint */
}


static void virt_viewer_app_remove_nth_window(VirtViewerApp *self,
                                              gint nth)
{
    VirtViewerWindow *win = virt_viewer_app_get_nth_window(self, nth);
    if (!win)
        return;
    virt_viewer_window_set_display(win, NULL);
    if (win == self->priv->main_window) {
        g_debug("Not removing main window %d %p", nth, win);
        return;
    }
    virt_viewer_window_hide(win);

    g_debug("Remove window %d %p", nth, win);
    self->priv->windows = g_list_remove(self->priv->windows, win);

    g_object_unref(win);
}

static void
virt_viewer_app_display_removed(VirtViewerSession *session G_GNUC_UNUSED,
                                VirtViewerDisplay *display,
                                VirtViewerApp *self)
{
    gint nth;

    g_object_get(display, "nth-display", &nth, NULL);
    virt_viewer_app_remove_nth_window(self, nth);
    g_hash_table_remove(self->priv->displays, GINT_TO_POINTER(nth));
    virt_viewer_app_update_menu_displays(self);
}

static void
virt_viewer_app_display_updated(VirtViewerSession *session G_GNUC_UNUSED,
                                VirtViewerApp *self)
{
    virt_viewer_app_update_menu_displays(self);
}

static void
virt_viewer_app_has_usbredir_updated(VirtViewerSession *session,
                                     GParamSpec *pspec G_GNUC_UNUSED,
                                     VirtViewerApp *self)
{
    virt_viewer_app_set_usb_options_sensitive(self,
                    virt_viewer_session_get_has_usbredir(session));
}

static void notify_software_reader_cb(GObject    *gobject G_GNUC_UNUSED,
                                      GParamSpec *pspec G_GNUC_UNUSED,
                                      gpointer    user_data)
{
    virt_viewer_update_smartcard_accels(VIRT_VIEWER_APP(user_data));
}

gboolean
virt_viewer_app_create_session(VirtViewerApp *self, const gchar *type, GError **error)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);
    VirtViewerAppPrivate *priv = self->priv;
    g_return_val_if_fail(priv->session == NULL, FALSE);
    g_return_val_if_fail(type != NULL, FALSE);

#ifdef HAVE_GTK_VNC
    if (g_ascii_strcasecmp(type, "vnc") == 0) {
        GtkWindow *window = virt_viewer_window_get_window(priv->main_window);
        virt_viewer_app_trace(self, "Guest %s has a %s display",
                              priv->guest_name, type);
        priv->session = virt_viewer_session_vnc_new(self, window);
    } else
#endif
#ifdef HAVE_SPICE_GTK
    if (g_ascii_strcasecmp(type, "spice") == 0) {
        GtkWindow *window = virt_viewer_window_get_window(priv->main_window);
        virt_viewer_app_trace(self, "Guest %s has a %s display",
                              priv->guest_name, type);
        priv->session = virt_viewer_session_spice_new(self, window);
    } else
#endif
    {
        g_set_error(error,
                    VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Unsupported graphic type '%s'"), type);

        virt_viewer_app_trace(self, "Guest %s has unsupported %s display type",
                              priv->guest_name, type);
        return FALSE;
    }

    g_signal_connect(priv->session, "session-initialized",
                     G_CALLBACK(virt_viewer_app_initialized), self);
    g_signal_connect(priv->session, "session-connected",
                     G_CALLBACK(virt_viewer_app_connected), self);
    g_signal_connect(priv->session, "session-disconnected",
                     G_CALLBACK(virt_viewer_app_disconnected), self);
    g_signal_connect(priv->session, "session-channel-open",
                     G_CALLBACK(virt_viewer_app_channel_open), self);
    g_signal_connect(priv->session, "session-auth-refused",
                     G_CALLBACK(virt_viewer_app_auth_refused), self);
    g_signal_connect(priv->session, "session-auth-unsupported",
                     G_CALLBACK(virt_viewer_app_auth_unsupported), self);
    g_signal_connect(priv->session, "session-usb-failed",
                     G_CALLBACK(virt_viewer_app_usb_failed), self);
    g_signal_connect(priv->session, "session-display-added",
                     G_CALLBACK(virt_viewer_app_display_added), self);
    g_signal_connect(priv->session, "session-display-removed",
                     G_CALLBACK(virt_viewer_app_display_removed), self);
    g_signal_connect(priv->session, "session-display-updated",
                     G_CALLBACK(virt_viewer_app_display_updated), self);
    g_signal_connect(priv->session, "notify::has-usbredir",
                     G_CALLBACK(virt_viewer_app_has_usbredir_updated), self);

    g_signal_connect(priv->session, "session-cut-text",
                     G_CALLBACK(virt_viewer_app_server_cut_text), self);
    g_signal_connect(priv->session, "session-bell",
                     G_CALLBACK(virt_viewer_app_bell), self);
    g_signal_connect(priv->session, "session-cancelled",
                     G_CALLBACK(virt_viewer_app_cancelled), self);

    g_signal_connect(priv->session, "notify::software-smartcard-reader",
                     (GCallback)notify_software_reader_cb, self);
    return TRUE;
}

static gboolean
virt_viewer_app_default_open_connection(VirtViewerApp *self G_GNUC_UNUSED, int *fd)
{
    *fd = -1;
    return TRUE;
}


static int
virt_viewer_app_open_connection(VirtViewerApp *self, int *fd)
{
    VirtViewerAppClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), -1);
    klass = VIRT_VIEWER_APP_GET_CLASS(self);

    return klass->open_connection(self, fd);
}


#if defined(HAVE_SOCKETPAIR) && defined(HAVE_FORK)
static void
virt_viewer_app_channel_open(VirtViewerSession *session,
                             VirtViewerSessionChannel *channel,
                             VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv;
    int fd = -1;
    gchar *error_message = NULL;

    g_return_if_fail(self != NULL);

    if (!virt_viewer_app_open_connection(self, &fd))
        return;

    g_debug("After open connection callback fd=%d", fd);

    priv = self->priv;
    if (priv->transport && g_ascii_strcasecmp(priv->transport, "ssh") == 0 &&
        !priv->direct && fd == -1) {
        if ((fd = virt_viewer_app_open_tunnel_ssh(priv->host, priv->port, priv->user,
                                                  priv->ghost, priv->gport, priv->unixsock)) < 0) {
            error_message = g_strdup(_("Connect to ssh failed."));
            g_debug("channel open ssh tunnel: %s", error_message);
        }
    }
    if (fd < 0 && priv->unixsock) {
        GError *error = NULL;
        if ((fd = virt_viewer_app_open_unix_sock(priv->unixsock, &error)) < 0) {
            g_free(error_message);
            error_message = g_strdup(error->message);
            g_debug("channel open unix socket: %s", error_message);
        }
        g_clear_error(&error);
    }

    if (fd < 0) {
        virt_viewer_app_simple_message_dialog(self, _("Can't connect to channel: %s"),
                                              (error_message != NULL) ? error_message :
                                              _("only SSH or unix socket connection supported."));
        g_free(error_message);
        return;
    }

    virt_viewer_session_channel_open_fd(session, channel, fd);
}
#else
static void
virt_viewer_app_channel_open(VirtViewerSession *session G_GNUC_UNUSED,
                             VirtViewerSessionChannel *channel G_GNUC_UNUSED,
                             VirtViewerApp *self)
{
    virt_viewer_app_simple_message_dialog(self, _("Connect to channel unsupported."));
}
#endif

static gboolean
virt_viewer_app_default_activate(VirtViewerApp *self, GError **error)
{
    VirtViewerAppPrivate *priv = self->priv;
    int fd = -1;

    if (!virt_viewer_app_open_connection(self, &fd))
        return FALSE;

    g_debug("After open connection callback fd=%d", fd);

#if defined(HAVE_SOCKETPAIR) && defined(HAVE_FORK)
    if (priv->transport &&
        g_ascii_strcasecmp(priv->transport, "ssh") == 0 &&
        !priv->direct &&
        fd == -1) {
        gchar *p = NULL;

        if (priv->gport) {
            virt_viewer_app_trace(self, "Opening indirect TCP connection to display at %s:%s",
                                  priv->ghost, priv->gport);
        } else {
            virt_viewer_app_trace(self, "Opening indirect UNIX connection to display at %s",
                                  priv->unixsock);
        }
        if (priv->port)
            p = g_strdup_printf(":%d", priv->port);

        virt_viewer_app_trace(self, "Setting up SSH tunnel via %s%s%s%s",
                              priv->user ? priv->user : "",
                              priv->user ? "@" : "",
                              priv->host, p ? p : "");
        g_free(p);

        if ((fd = virt_viewer_app_open_tunnel_ssh(priv->host, priv->port,
                                                  priv->user, priv->ghost,
                                                  priv->gport, priv->unixsock)) < 0)
            return FALSE;
    } else if (priv->unixsock && fd == -1) {
        virt_viewer_app_trace(self, "Opening direct UNIX connection to display at %s",
                              priv->unixsock);
        if ((fd = virt_viewer_app_open_unix_sock(priv->unixsock, error)) < 0)
            return FALSE;
    }
#endif

    if (fd >= 0) {
        return virt_viewer_session_open_fd(VIRT_VIEWER_SESSION(priv->session), fd);
    } else if (priv->guri) {
        virt_viewer_app_trace(self, "Opening connection to display at %s", priv->guri);
        return virt_viewer_session_open_uri(VIRT_VIEWER_SESSION(priv->session), priv->guri, error);
    } else if (priv->ghost) {
        virt_viewer_app_trace(self, "Opening direct TCP connection to display at %s:%s:%s",
                              priv->ghost, priv->gport, priv->gtlsport ? priv->gtlsport : "-1");
        return virt_viewer_session_open_host(VIRT_VIEWER_SESSION(priv->session),
                                             priv->ghost, priv->gport, priv->gtlsport);
    } else {
        g_set_error_literal(error, VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                            _("Display can only be attached through libvirt with --attach"));
   }

    return FALSE;
}

gboolean
virt_viewer_app_activate(VirtViewerApp *self, GError **error)
{
    VirtViewerAppPrivate *priv;
    gboolean ret;

    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    priv = self->priv;
    if (priv->active)
        return FALSE;

    ret = VIRT_VIEWER_APP_GET_CLASS(self)->activate(self, error);

    if (ret == FALSE) {
        if(error != NULL && *error != NULL)
            virt_viewer_app_show_status(self, (*error)->message);
        priv->connected = FALSE;
    } else {
        virt_viewer_app_show_status(self, _("Connecting to graphic server"));
        priv->cancelled = FALSE;
        priv->active = TRUE;
    }

    priv->grabbed = FALSE;
    virt_viewer_app_update_title(self);

    return ret;
}

/* text was actually requested */
static void
virt_viewer_app_clipboard_copy(GtkClipboard *clipboard G_GNUC_UNUSED,
                               GtkSelectionData *data,
                               guint info G_GNUC_UNUSED,
                               VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv = self->priv;

    gtk_selection_data_set_text(data, priv->clipboard, -1);
}

static void
virt_viewer_app_server_cut_text(VirtViewerSession *session G_GNUC_UNUSED,
                                const gchar *text,
                                VirtViewerApp *self)
{
    GtkClipboard *cb;
    gsize a, b;
    VirtViewerAppPrivate *priv = self->priv;
    GtkTargetEntry targets[] = {
        {g_strdup("UTF8_STRING"), 0, 0},
        {g_strdup("COMPOUND_TEXT"), 0, 0},
        {g_strdup("TEXT"), 0, 0},
        {g_strdup("STRING"), 0, 0},
    };

    if (!text)
        return;

    g_free (priv->clipboard);
    priv->clipboard = g_convert (text, -1, "utf-8", "iso8859-1", &a, &b, NULL);

    if (priv->clipboard) {
        cb = gtk_clipboard_get (GDK_SELECTION_CLIPBOARD);

        gtk_clipboard_set_with_owner (cb,
                                      targets,
                                      G_N_ELEMENTS(targets),
                                      (GtkClipboardGetFunc)virt_viewer_app_clipboard_copy,
                                      NULL,
                                      G_OBJECT (self));
    }
}


static void virt_viewer_app_bell(VirtViewerSession *session G_GNUC_UNUSED,
                                 VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv = self->priv;

    gdk_window_beep(gtk_widget_get_window(GTK_WIDGET(virt_viewer_window_get_window(priv->main_window))));
}


static gboolean
virt_viewer_app_default_initial_connect(VirtViewerApp *self, GError **error)
{
    return virt_viewer_app_activate(self, error);
}

gboolean
virt_viewer_app_initial_connect(VirtViewerApp *self, GError **error)
{
    VirtViewerAppClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);
    klass = VIRT_VIEWER_APP_GET_CLASS(self);

    return klass->initial_connect(self, error);
}

static gboolean
virt_viewer_app_retryauth(gpointer opaque)
{
    VirtViewerApp *self = opaque;

    virt_viewer_app_initial_connect(self, NULL);

    return FALSE;
}

static void
virt_viewer_app_default_deactivated(VirtViewerApp *self, gboolean connect_error)
{
    VirtViewerAppPrivate *priv = self->priv;

    if (!connect_error) {
        virt_viewer_app_show_status(self, _("Guest domain has shutdown"));
        virt_viewer_app_trace(self, "Guest %s display has disconnected, shutting down",
                              priv->guest_name);
    }

    if (self->priv->quit_on_disconnect)
        g_application_quit(G_APPLICATION(self));
}

static void
virt_viewer_app_deactivated(VirtViewerApp *self, gboolean connect_error)
{
    VirtViewerAppClass *klass;
    klass = VIRT_VIEWER_APP_GET_CLASS(self);

    klass->deactivated(self, connect_error);
}

static void
virt_viewer_app_deactivate(VirtViewerApp *self, gboolean connect_error)
{
    VirtViewerAppPrivate *priv = self->priv;

    if (!priv->active)
        return;

    if (priv->session) {
        virt_viewer_session_close(VIRT_VIEWER_SESSION(priv->session));
    }

    priv->connected = FALSE;
    priv->active = FALSE;
    priv->started = FALSE;
#if 0
    g_free(priv->pretty_address);
    priv->pretty_address = NULL;
#endif
    priv->grabbed = FALSE;
    virt_viewer_app_update_title(self);

    if (priv->authretry) {
        priv->authretry = FALSE;
        g_idle_add(virt_viewer_app_retryauth, self);
    } else {
        g_clear_object(&priv->session);
        virt_viewer_app_deactivated(self, connect_error);
    }

}

static void
virt_viewer_app_connected(VirtViewerSession *session G_GNUC_UNUSED,
                          VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv = self->priv;

    priv->connected = TRUE;

    if (self->priv->kiosk)
        virt_viewer_app_show_status(self, "");
    else
        virt_viewer_app_show_status(self, _("Connected to graphic server"));
}



static void
virt_viewer_app_initialized(VirtViewerSession *session G_GNUC_UNUSED,
                            VirtViewerApp *self)
{
    virt_viewer_app_update_title(self);
}

static void
virt_viewer_app_disconnected(VirtViewerSession *session G_GNUC_UNUSED, const gchar *msg,
                             VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv = self->priv;
    gboolean connect_error = !priv->connected && !priv->cancelled;

    if (!priv->kiosk)
        virt_viewer_app_hide_all_windows(self);
    else if (priv->cancelled)
        priv->authretry = TRUE;

    if (priv->quitting)
        g_application_quit(G_APPLICATION(self));

    if (connect_error) {
        GtkWidget *dialog = virt_viewer_app_make_message_dialog(self,
            _("Unable to connect to the graphic server %s"), priv->pretty_address);

        g_object_set(dialog, "secondary-text", msg, NULL);
        gtk_dialog_run(GTK_DIALOG(dialog));
        gtk_widget_destroy(dialog);
    }
    virt_viewer_app_set_usb_options_sensitive(self, FALSE);
    virt_viewer_app_deactivate(self, connect_error);
}

static void virt_viewer_app_cancelled(VirtViewerSession *session,
                                      VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv = self->priv;
    priv->cancelled = TRUE;
    virt_viewer_app_disconnected(session, NULL, self);
}


static void virt_viewer_app_auth_refused(VirtViewerSession *session,
                                         const char *msg,
                                         VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv = self->priv;

    virt_viewer_app_simple_message_dialog(self,
                                          _("Unable to authenticate with remote desktop server at %s: %s\n"),
                                          priv->pretty_address, msg);

    /* if the session implementation cannot retry auth automatically, the
     * VirtViewerApp needs to schedule a new connection to retry */
    priv->authretry = (!virt_viewer_session_can_retry_auth(session) &&
                       !virt_viewer_session_get_file(session));
}

static void virt_viewer_app_auth_unsupported(VirtViewerSession *session G_GNUC_UNUSED,
                                        const char *msg,
                                        VirtViewerApp *self)
{
    virt_viewer_app_simple_message_dialog(self,
                                          _("Unable to authenticate with remote desktop server: %s"),
                                          msg);
}

static void virt_viewer_app_usb_failed(VirtViewerSession *session G_GNUC_UNUSED,
                                       const gchar *msg,
                                       VirtViewerApp *self)
{
    virt_viewer_app_simple_message_dialog(self, _("USB redirection error: %s"), msg);
}

static void
virt_viewer_app_set_kiosk(VirtViewerApp *self, gboolean enabled)
{
    int i;
    GList *l;

    self->priv->kiosk = enabled;
    if (!enabled)
        return;

    virt_viewer_app_set_fullscreen(self, enabled);

    /* create windows for each client monitor */
    for (i = g_list_length(self->priv->windows);
         i < get_n_client_monitors(); i++) {
        virt_viewer_app_window_new(self, i);
    }

    for (l = self->priv->windows; l != NULL; l = l ->next) {
        VirtViewerWindow *win = l->data;

        virt_viewer_window_show(win);
        virt_viewer_window_set_kiosk(win, enabled);
    }
}


static void
virt_viewer_app_get_property (GObject *object, guint property_id,
                              GValue *value G_GNUC_UNUSED, GParamSpec *pspec)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(object));
    VirtViewerApp *self = VIRT_VIEWER_APP(object);
    VirtViewerAppPrivate *priv = self->priv;

    switch (property_id) {
    case PROP_VERBOSE:
        g_value_set_boolean(value, priv->verbose);
        break;

    case PROP_SESSION:
        g_value_set_object(value, priv->session);
        break;

    case PROP_GUEST_NAME:
        g_value_set_string(value, priv->guest_name);
        break;

    case PROP_GURI:
        g_value_set_string(value, priv->guri);
        break;

    case PROP_FULLSCREEN:
        g_value_set_boolean(value, priv->fullscreen);
        break;

    case PROP_TITLE:
        g_value_set_string(value, virt_viewer_app_get_title(self));
        break;

    case PROP_ENABLE_ACCEL:
        g_value_set_boolean(value, virt_viewer_app_get_enable_accel(self));
        break;

    case PROP_HAS_FOCUS:
        g_value_set_boolean(value, priv->focused > 0);
        break;

    case PROP_KIOSK:
        g_value_set_boolean(value, priv->kiosk);
        break;

    case PROP_QUIT_ON_DISCONNECT:
        g_value_set_boolean(value, priv->quit_on_disconnect);
        break;

    case PROP_UUID:
        g_value_set_string(value, priv->uuid);
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
    }
}

static void
virt_viewer_app_set_property (GObject *object, guint property_id,
                              const GValue *value G_GNUC_UNUSED, GParamSpec *pspec)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(object));
    VirtViewerApp *self = VIRT_VIEWER_APP(object);
    VirtViewerAppPrivate *priv = self->priv;

    switch (property_id) {
    case PROP_VERBOSE:
        priv->verbose = g_value_get_boolean(value);
        break;

    case PROP_GUEST_NAME:
        g_free(priv->guest_name);
        priv->guest_name = g_value_dup_string(value);
        break;

    case PROP_GURI:
        g_free(priv->guri);
        priv->guri = g_value_dup_string(value);
        virt_viewer_app_update_pretty_address(self);
        break;

    case PROP_FULLSCREEN:
        virt_viewer_app_set_fullscreen(self, g_value_get_boolean(value));
        break;

    case PROP_TITLE:
        g_free(self->priv->title);
        self->priv->title = g_value_dup_string(value);
        break;

    case PROP_ENABLE_ACCEL:
        virt_viewer_app_set_enable_accel(self, g_value_get_boolean(value));
        break;

    case PROP_KIOSK:
        virt_viewer_app_set_kiosk(self, g_value_get_boolean(value));
        break;

    case PROP_QUIT_ON_DISCONNECT:
        priv->quit_on_disconnect = g_value_get_boolean(value);
        break;

    case PROP_UUID:
        virt_viewer_app_set_uuid_string(self, g_value_get_string(value));
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
    }
}

static void
virt_viewer_app_dispose (GObject *object)
{
    VirtViewerApp *self = VIRT_VIEWER_APP(object);
    VirtViewerAppPrivate *priv = self->priv;

    if (priv->preferences)
        gtk_widget_destroy(priv->preferences);
    priv->preferences = NULL;

    if (priv->windows) {
        GList *tmp = priv->windows;
        /* null-ify before unrefing, because we need
         * to prevent callbacks using priv->windows
         * while it is being disposed off. */
        priv->windows = NULL;
        priv->main_window = NULL;
        g_list_free_full(tmp, g_object_unref);
    }

    if (priv->displays) {
        GHashTable *tmp = priv->displays;
        /* null-ify before unrefing, because we need
         * to prevent callbacks using priv->displays
         * while it is being disposed of. */
        priv->displays = NULL;
        g_hash_table_unref(tmp);
    }

    priv->resource = NULL;
    g_clear_object(&priv->session);
    g_free(priv->title);
    priv->title = NULL;
    g_free(priv->guest_name);
    priv->guest_name = NULL;
    g_free(priv->pretty_address);
    priv->pretty_address = NULL;
    g_free(priv->guri);
    priv->guri = NULL;
    g_free(priv->title);
    priv->title = NULL;
    g_free(priv->uuid);
    priv->uuid = NULL;
    g_free(priv->config_file);
    priv->config_file = NULL;
    g_clear_pointer(&priv->config, g_key_file_free);
    g_clear_pointer(&priv->initial_display_map, g_hash_table_unref);

    virt_viewer_app_free_connect_info(self);

    G_OBJECT_CLASS (virt_viewer_app_parent_class)->dispose (object);
}

static gboolean
virt_viewer_app_default_start(VirtViewerApp *self, GError **error G_GNUC_UNUSED)
{
    virt_viewer_window_show(self->priv->main_window);
    return TRUE;
}

gboolean virt_viewer_app_start(VirtViewerApp *self, GError **error)
{
    VirtViewerAppClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);
    klass = VIRT_VIEWER_APP_GET_CLASS(self);

    g_return_val_if_fail(!self->priv->started, TRUE);

    self->priv->started = klass->start(self, error);
    return self->priv->started;
}

static int opt_zoom = NORMAL_ZOOM_LEVEL;
static gchar *opt_hotkeys = NULL;
static gboolean opt_version = FALSE;
static gboolean opt_verbose = FALSE;
static gboolean opt_debug = FALSE;
static gboolean opt_fullscreen = FALSE;
static gboolean opt_kiosk = FALSE;
static gboolean opt_kiosk_quit = FALSE;

static void
title_maybe_changed(VirtViewerApp *self, GParamSpec* pspec G_GNUC_UNUSED, gpointer user_data G_GNUC_UNUSED)
{
    virt_viewer_app_set_all_window_subtitles(self);
}

static void
virt_viewer_app_init(VirtViewerApp *self)
{
    GError *error = NULL;
    self->priv = GET_PRIVATE(self);

    gtk_window_set_default_icon_name("virt-viewer");

    self->priv->displays = g_hash_table_new_full(g_direct_hash, g_direct_equal, NULL, g_object_unref);
    self->priv->config = g_key_file_new();
    self->priv->config_file = g_build_filename(g_get_user_config_dir(),
                                               "virt-viewer", "settings", NULL);
    g_key_file_load_from_file(self->priv->config, self->priv->config_file,
                    G_KEY_FILE_KEEP_COMMENTS|G_KEY_FILE_KEEP_TRANSLATIONS, &error);

    if (g_error_matches(error, G_FILE_ERROR, G_FILE_ERROR_NOENT))
        g_debug("No configuration file %s", self->priv->config_file);
    else if (error)
        g_warning("Couldn't load configuration: %s", error->message);

    g_clear_error(&error);

    g_signal_connect(self, "notify::guest-name", G_CALLBACK(title_maybe_changed), NULL);
    g_signal_connect(self, "notify::title", G_CALLBACK(title_maybe_changed), NULL);
    g_signal_connect(self, "notify::guri", G_CALLBACK(title_maybe_changed), NULL);
}

static void
virt_viewer_set_insert_smartcard_accel(VirtViewerApp *self,
                                       guint accel_key,
                                       GdkModifierType accel_mods)
{
    VirtViewerAppPrivate *priv = self->priv;

    priv->insert_smartcard_accel_key = accel_key;
    priv->insert_smartcard_accel_mods = accel_mods;
}

static void
virt_viewer_set_remove_smartcard_accel(VirtViewerApp *self,
                                       guint accel_key,
                                       GdkModifierType accel_mods)
{
    VirtViewerAppPrivate *priv = self->priv;

    priv->remove_smartcard_accel_key = accel_key;
    priv->remove_smartcard_accel_mods = accel_mods;
}

static void
virt_viewer_update_smartcard_accels(VirtViewerApp *self)
{
    gboolean sw_smartcard;
    VirtViewerAppPrivate *priv = self->priv;

    if (self->priv->session != NULL) {
        g_object_get(G_OBJECT(self->priv->session),
                     "software-smartcard-reader", &sw_smartcard,
                     NULL);
    } else {
        sw_smartcard = FALSE;
    }
    if (sw_smartcard) {
        g_debug("enabling smartcard shortcuts");
        gtk_accel_map_change_entry("<virt-viewer>/file/smartcard-insert",
                                   priv->insert_smartcard_accel_key,
                                   priv->insert_smartcard_accel_mods,
                                   TRUE);
        gtk_accel_map_change_entry("<virt-viewer>/file/smartcard-remove",
                                   priv->remove_smartcard_accel_key,
                                   priv->remove_smartcard_accel_mods,
                                   TRUE);
    } else {
        g_debug("disabling smartcard shortcuts");
        gtk_accel_map_change_entry("<virt-viewer>/file/smartcard-insert", 0, 0, TRUE);
        gtk_accel_map_change_entry("<virt-viewer>/file/smartcard-remove", 0, 0, TRUE);
    }
}

static void
virt_viewer_app_on_application_startup(GApplication *app)
{
    VirtViewerApp *self = VIRT_VIEWER_APP(app);
    GError *error = NULL;

    G_APPLICATION_CLASS(virt_viewer_app_parent_class)->startup(app);

    self->priv->resource = virt_viewer_get_resource();

    virt_viewer_app_set_debug(opt_debug);
    virt_viewer_app_set_fullscreen(self, opt_fullscreen);

    self->priv->verbose = opt_verbose;
    self->priv->quit_on_disconnect = opt_kiosk ? opt_kiosk_quit : TRUE;

    self->priv->main_window = virt_viewer_app_window_new(self,
                                                         virt_viewer_app_get_first_monitor(self));
    self->priv->main_notebook = GTK_WIDGET(virt_viewer_window_get_notebook(self->priv->main_window));
    self->priv->initial_display_map = virt_viewer_app_get_monitor_mapping_for_section(self, "fallback");

    virt_viewer_app_set_kiosk(self, opt_kiosk);
    virt_viewer_app_set_hotkeys(self, opt_hotkeys);

    if (opt_zoom < MIN_ZOOM_LEVEL || opt_zoom > MAX_ZOOM_LEVEL) {
        g_printerr(_("Zoom level must be within %d-%d\n"), MIN_ZOOM_LEVEL, MAX_ZOOM_LEVEL);
        opt_zoom = NORMAL_ZOOM_LEVEL;
    }

    virt_viewer_window_set_zoom_level(self->priv->main_window, opt_zoom);

    virt_viewer_set_insert_smartcard_accel(self, GDK_KEY_F8, GDK_SHIFT_MASK);
    virt_viewer_set_remove_smartcard_accel(self, GDK_KEY_F9, GDK_SHIFT_MASK);
    gtk_accel_map_add_entry("<virt-viewer>/view/toggle-fullscreen", GDK_KEY_F11, 0);
    gtk_accel_map_add_entry("<virt-viewer>/view/release-cursor", GDK_KEY_F12, GDK_SHIFT_MASK);
    gtk_accel_map_add_entry("<virt-viewer>/view/zoom-reset", GDK_KEY_0, GDK_CONTROL_MASK);
    gtk_accel_map_add_entry("<virt-viewer>/view/zoom-out", GDK_KEY_minus, GDK_CONTROL_MASK);
    gtk_accel_map_add_entry("<virt-viewer>/view/zoom-in", GDK_KEY_plus, GDK_CONTROL_MASK);
    gtk_accel_map_add_entry("<virt-viewer>/send/secure-attention", GDK_KEY_End, GDK_CONTROL_MASK | GDK_MOD1_MASK);

    if (!virt_viewer_app_start(self, &error)) {
        if (error && !g_error_matches(error, VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_CANCELLED))
            virt_viewer_app_simple_message_dialog(self, error->message);

        g_clear_error(&error);
        g_application_quit(app);
        return;
    }
}

static gboolean
virt_viewer_app_local_command_line (GApplication   *gapp,
                                    gchar        ***args,
                                    int            *status)
{
    VirtViewerApp *self = VIRT_VIEWER_APP(gapp);
    gboolean ret = FALSE;
    gint argc = g_strv_length(*args);
    GError *error = NULL;
    GOptionContext *context = g_option_context_new(NULL);
    GOptionGroup *group = g_option_group_new("virt-viewer", NULL, NULL, gapp, NULL);

    *status = 0;
    g_option_context_set_main_group(context, group);
    VIRT_VIEWER_APP_GET_CLASS(self)->add_option_entries(self, context, group);

    g_option_context_add_group(context, gtk_get_option_group(FALSE));

#ifdef HAVE_GTK_VNC
    g_option_context_add_group(context, vnc_display_get_option_group());
#endif

#ifdef HAVE_SPICE_GTK
    g_option_context_add_group(context, spice_get_option_group());
#endif

    if (!g_option_context_parse(context, &argc, args, &error)) {
        if (error != NULL) {
            g_printerr(_("%s\n"), error->message);
            g_error_free(error);
        }

        *status = 1;
        ret = TRUE;
        goto end;
    }

    if (opt_version) {
        g_print(_("%s version %s"), g_get_prgname(), VERSION BUILDID);
#ifdef REMOTE_VIEWER_OS_ID
        g_print(" (OS ID: %s)", REMOTE_VIEWER_OS_ID);
#endif
        g_print("\n");
        ret = TRUE;
    }

end:
    g_option_context_free(context);
    return ret;
}

static void
virt_viewer_app_class_init (VirtViewerAppClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GApplicationClass *g_app_class = G_APPLICATION_CLASS(klass);

    g_type_class_add_private (klass, sizeof (VirtViewerAppPrivate));

    object_class->get_property = virt_viewer_app_get_property;
    object_class->set_property = virt_viewer_app_set_property;
    object_class->dispose = virt_viewer_app_dispose;

    g_app_class->local_command_line = virt_viewer_app_local_command_line;
    g_app_class->startup = virt_viewer_app_on_application_startup;
    g_app_class->command_line = NULL; /* inhibit GApplication default handler */

    klass->start = virt_viewer_app_default_start;
    klass->initial_connect = virt_viewer_app_default_initial_connect;
    klass->activate = virt_viewer_app_default_activate;
    klass->deactivated = virt_viewer_app_default_deactivated;
    klass->open_connection = virt_viewer_app_default_open_connection;
    klass->add_option_entries = virt_viewer_app_add_option_entries;

    g_object_class_install_property(object_class,
                                    PROP_VERBOSE,
                                    g_param_spec_boolean("verbose",
                                                         "Verbose",
                                                         "Verbose trace",
                                                         FALSE,
                                                         G_PARAM_READABLE |
                                                         G_PARAM_WRITABLE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_SESSION,
                                    g_param_spec_object("session",
                                                        "Session",
                                                        "ViewerSession",
                                                        VIRT_VIEWER_TYPE_SESSION,
                                                        G_PARAM_READABLE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_GUEST_NAME,
                                    g_param_spec_string("guest-name",
                                                        "Guest name",
                                                        "Guest name",
                                                        "",
                                                        G_PARAM_READABLE |
                                                        G_PARAM_WRITABLE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_GURI,
                                    g_param_spec_string("guri",
                                                        "guri",
                                                        "Remote graphical URI",
                                                        "",
                                                        G_PARAM_READWRITE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_FULLSCREEN,
                                    g_param_spec_boolean("fullscreen",
                                                         "Fullscreen",
                                                         "Fullscreen",
                                                         FALSE,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_TITLE,
                                    g_param_spec_string("title",
                                                        "Title",
                                                        "Title",
                                                        "",
                                                        G_PARAM_READABLE |
                                                        G_PARAM_WRITABLE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_ENABLE_ACCEL,
                                    g_param_spec_boolean("enable-accel",
                                                         "Enable Accel",
                                                         "Enable accelerators",
                                                         FALSE,
                                                         G_PARAM_CONSTRUCT |
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_HAS_FOCUS,
                                    g_param_spec_boolean("has-focus",
                                                         "Has Focus",
                                                         "Application has focus",
                                                         FALSE,
                                                         G_PARAM_READABLE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_KIOSK,
                                    g_param_spec_boolean("kiosk",
                                                         "Kiosk",
                                                         "Kiosk mode",
                                                         FALSE,
                                                         G_PARAM_CONSTRUCT |
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_QUIT_ON_DISCONNECT,
                                    g_param_spec_boolean("quit-on-disconnect",
                                                         "Quit on disconnect",
                                                         "Quit on disconnect",
                                                         TRUE,
                                                         G_PARAM_READWRITE |
                                                         G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_UUID,
                                    g_param_spec_string("uuid",
                                                        "uuid",
                                                        "uuid",
                                                        NULL,
                                                        G_PARAM_READABLE |
                                                        G_PARAM_WRITABLE |
                                                        G_PARAM_STATIC_STRINGS));
}

void
virt_viewer_app_set_direct(VirtViewerApp *self, gboolean direct)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(self));

    self->priv->direct = direct;
}

gboolean virt_viewer_app_get_direct(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    return self->priv->direct;
}

void
virt_viewer_app_clear_hotkeys(VirtViewerApp *self)
{
    /* Disable default bindings and replace them with our own */
    gtk_accel_map_change_entry("<virt-viewer>/view/toggle-fullscreen", 0, 0, TRUE);
    gtk_accel_map_change_entry("<virt-viewer>/view/release-cursor", 0, 0, TRUE);
    gtk_accel_map_change_entry("<virt-viewer>/view/zoom-reset", 0, 0, TRUE);
    gtk_accel_map_change_entry("<virt-viewer>/view/zoom-in", 0, 0, TRUE);
    gtk_accel_map_change_entry("<virt-viewer>/view/zoom-out", 0, 0, TRUE);
    gtk_accel_map_change_entry("<virt-viewer>/send/secure-attention", 0, 0, TRUE);
    virt_viewer_set_insert_smartcard_accel(self, 0, 0);
    virt_viewer_set_remove_smartcard_accel(self, 0, 0);
}

void
virt_viewer_app_set_enable_accel(VirtViewerApp *self, gboolean enable)
{
    self->priv->enable_accel = enable;
    g_object_notify(G_OBJECT(self), "enable-accel");
}

void
virt_viewer_app_set_hotkeys(VirtViewerApp *self, const gchar *hotkeys_str)
{
    gchar **hotkey, **hotkeys = NULL;

    g_return_if_fail(VIRT_VIEWER_IS_APP(self));

    if (hotkeys_str)
        hotkeys = g_strsplit(hotkeys_str, ",", -1);

    if (!hotkeys || g_strv_length(hotkeys) == 0) {
        g_strfreev(hotkeys);
        virt_viewer_app_set_enable_accel(self, FALSE);
        return;
    }

    virt_viewer_app_clear_hotkeys(self);

    for (hotkey = hotkeys; *hotkey != NULL; hotkey++) {
        gchar *key = strstr(*hotkey, "=");
        const gchar *value = (key == NULL) ? NULL : (*key = '\0', key + 1);
        if (value == NULL || *value == '\0') {
            g_warning("missing value for key '%s'", *hotkey);
            continue;
        }

        gchar *accel = spice_hotkey_to_gtk_accelerator(value);
        guint accel_key;
        GdkModifierType accel_mods;
        gtk_accelerator_parse(accel, &accel_key, &accel_mods);
        g_free(accel);

        if (accel_key == 0 && accel_mods == 0) {
            g_warning("Invalid value '%s' for key '%s'", value, *hotkey);
            continue;
        }

        if (g_str_equal(*hotkey, "toggle-fullscreen")) {
            gtk_accel_map_change_entry("<virt-viewer>/view/toggle-fullscreen", accel_key, accel_mods, TRUE);
        } else if (g_str_equal(*hotkey, "release-cursor")) {
            gtk_accel_map_change_entry("<virt-viewer>/view/release-cursor", accel_key, accel_mods, TRUE);
        } else if (g_str_equal(*hotkey, "secure-attention")) {
            gtk_accel_map_change_entry("<virt-viewer>/send/secure-attention", accel_key, accel_mods, TRUE);
        } else if (g_str_equal(*hotkey, "smartcard-insert")) {
            virt_viewer_set_insert_smartcard_accel(self, accel_key, accel_mods);
        } else if (g_str_equal(*hotkey, "smartcard-remove")) {
            virt_viewer_set_remove_smartcard_accel(self, accel_key, accel_mods);
        } else {
            g_warning("Unknown hotkey command %s", *hotkey);
        }
    }
    g_strfreev(hotkeys);

    virt_viewer_app_set_enable_accel(self, TRUE);
    virt_viewer_update_smartcard_accels(self);
}

void
virt_viewer_app_set_attach(VirtViewerApp *self, gboolean attach)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(self));

    self->priv->attach = attach;
}

gboolean
virt_viewer_app_get_attach(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    return self->priv->attach;
}

gboolean
virt_viewer_app_is_active(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    return self->priv->active;
}

gboolean
virt_viewer_app_has_session(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    return self->priv->session != NULL;
}

static void
virt_viewer_app_update_pretty_address(VirtViewerApp *self)
{
    VirtViewerAppPrivate *priv;

    priv = self->priv;
    g_free(priv->pretty_address);
    priv->pretty_address = NULL;
    if (priv->guri)
        priv->pretty_address = g_strdup(priv->guri);
    else if (priv->gport)
        priv->pretty_address = g_strdup_printf("%s:%s", priv->ghost, priv->gport);
    else if (priv->host && priv->unixsock)
        priv->pretty_address = g_strdup_printf("%s:%s", priv->host, priv->unixsock);
}

typedef struct {
    VirtViewerApp *app;
    gboolean fullscreen;
} FullscreenOptions;

static void fullscreen_cb(gpointer value,
                          gpointer user_data)
{
    FullscreenOptions *options = (FullscreenOptions *)user_data;
    gint nth = 0;
    VirtViewerWindow *vwin = VIRT_VIEWER_WINDOW(value);
    VirtViewerDisplay *display = virt_viewer_window_get_display(vwin);

    /* At startup, the main window will not yet have an associated display, so
     * assume that it's the first display */
    if (display)
        nth = virt_viewer_display_get_nth(display);
    g_debug("fullscreen display %d: %d", nth, options->fullscreen);

    if (options->fullscreen)
        app_window_try_fullscreen(options->app, vwin, nth);
    else
        virt_viewer_window_leave_fullscreen(vwin);
}

gboolean
virt_viewer_app_get_fullscreen(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    return self->priv->fullscreen;
}

static void
virt_viewer_app_set_fullscreen(VirtViewerApp *self, gboolean fullscreen)
{
    VirtViewerAppPrivate *priv = self->priv;
    FullscreenOptions options  = {
        .app = self,
        .fullscreen = fullscreen,
    };

    /* we iterate unconditionnaly, even if it was set before to update new windows */
    priv->fullscreen = fullscreen;
    g_list_foreach(priv->windows, fullscreen_cb, &options);

    g_object_notify(G_OBJECT(self), "fullscreen");
}

static void
menu_display_visible_toggled_cb(GtkCheckMenuItem *checkmenuitem,
                                VirtViewerDisplay *display)
{
    VirtViewerApp *self = virt_viewer_session_get_app(virt_viewer_display_get_session(display));
    gboolean visible = gtk_check_menu_item_get_active(checkmenuitem);
    static gboolean reentering = FALSE;
    VirtViewerWindow *vwin;

    if (reentering) /* do not reenter if I switch you back */
        return;

    reentering = TRUE;

    vwin = ensure_window_for_display(self, display);
    visible = virt_viewer_app_window_set_visible(self, vwin, visible);

    gtk_check_menu_item_set_active(checkmenuitem, /* will be toggled again */ !visible);
    reentering = FALSE;

    virt_viewer_session_update_displays_geometry(virt_viewer_display_get_session(display));
}

static gint
update_menu_displays_sort(gconstpointer a, gconstpointer b)
{
    const int ai = GPOINTER_TO_INT(a);
    const int bi = GPOINTER_TO_INT(b);

    if (ai > bi)
        return 1;
    else if (ai < bi)
        return -1;
    else
        return 0;
}

static GtkMenuShell *
window_empty_display_submenu(VirtViewerWindow *window)
{
    /* Because of what apparently is a gtk+2 bug (rhbz#922712), we
     * cannot recreate the submenu every time we need to refresh it,
     * otherwise the application may get frozen with the keyboard and
     * mouse grabbed if gtk_menu_item_set_submenu is called while
     * the menu is displayed. Reusing the same menu every time
     * works around this issue.
     */
    GtkMenuItem *menu = virt_viewer_window_get_menu_displays(window);
    GtkMenuShell *submenu;

    submenu = GTK_MENU_SHELL(gtk_menu_item_get_submenu(menu));
    if (submenu) {
        GList *subitems;
        GList *it;
        subitems = gtk_container_get_children(GTK_CONTAINER(submenu));
        for (it = subitems; it != NULL; it = it->next) {
            gtk_container_remove(GTK_CONTAINER(submenu), GTK_WIDGET(it->data));
        }
        g_list_free(subitems);
    } else {
        submenu = GTK_MENU_SHELL(gtk_menu_new());
        gtk_menu_item_set_submenu(menu, GTK_WIDGET(submenu));
    }

    return submenu;
}

static void
window_update_menu_displays_cb(gpointer value,
                               gpointer user_data)
{
    VirtViewerApp *self = VIRT_VIEWER_APP(user_data);
    GtkMenuShell *submenu;
    GList *keys = g_hash_table_get_keys(self->priv->displays);
    GList *tmp;
    gboolean sensitive;

    keys = g_list_sort(keys, update_menu_displays_sort);
    submenu = window_empty_display_submenu(VIRT_VIEWER_WINDOW(value));

    sensitive = (keys != NULL);
    virt_viewer_window_set_menu_displays_sensitive(VIRT_VIEWER_WINDOW(value), sensitive);

    tmp = keys;
    while (tmp) {
        int nth = GPOINTER_TO_INT(tmp->data);
        VirtViewerWindow *vwin = virt_viewer_app_get_nth_window(self, nth);
        VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(g_hash_table_lookup(self->priv->displays, tmp->data));
        GtkWidget *item;
        gboolean visible;
        gchar *label;

        label = g_strdup_printf(_("Display _%d"), nth + 1);
        item = gtk_check_menu_item_new_with_mnemonic(label);
        g_free(label);

        visible = vwin && gtk_widget_get_visible(GTK_WIDGET(virt_viewer_window_get_window(vwin)));
        gtk_check_menu_item_set_active(GTK_CHECK_MENU_ITEM(item), visible);

        sensitive = visible;
        if (display) {
            guint hint = virt_viewer_display_get_show_hint(display);

            if (hint & VIRT_VIEWER_DISPLAY_SHOW_HINT_READY)
                sensitive = TRUE;

            if (virt_viewer_display_get_selectable(display))
                sensitive = TRUE;
        }
        gtk_widget_set_sensitive(item, sensitive);

        virt_viewer_signal_connect_object(G_OBJECT(item), "toggled",
                                          G_CALLBACK(menu_display_visible_toggled_cb), display, 0);
        gtk_menu_shell_append(submenu, item);
        tmp = tmp->next;
    }

    gtk_widget_show_all(GTK_WIDGET(submenu));
    g_list_free(keys);
}

static void
virt_viewer_app_update_menu_displays(VirtViewerApp *self)
{
    if (!self->priv->windows)
        return;
    g_list_foreach(self->priv->windows, window_update_menu_displays_cb, self);
}

void
virt_viewer_app_set_connect_info(VirtViewerApp *self,
                                 const gchar *host,
                                 const gchar *ghost,
                                 const gchar *gport,
                                 const gchar *gtlsport,
                                 const gchar *transport,
                                 const gchar *unixsock,
                                 const gchar *user,
                                 gint port,
                                 const gchar *guri)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(self));
    VirtViewerAppPrivate *priv = self->priv;

    g_debug("Set connect info: %s,%s,%s,%s,%s,%s,%s,%d",
              host, ghost, gport ? gport : "-1", gtlsport ? gtlsport : "-1", transport, unixsock, user, port);

    g_free(priv->host);
    g_free(priv->ghost);
    g_free(priv->gport);
    g_free(priv->gtlsport);
    g_free(priv->transport);
    g_free(priv->unixsock);
    g_free(priv->user);
    g_free(priv->guri);

    priv->host = g_strdup(host);
    priv->ghost = g_strdup(ghost);
    priv->gport = g_strdup(gport);
    priv->gtlsport = g_strdup(gtlsport);
    priv->transport = g_strdup(transport);
    priv->unixsock = g_strdup(unixsock);
    priv->user = g_strdup(user);
    priv->guri = g_strdup(guri);
    priv->port = port;

    virt_viewer_app_update_pretty_address(self);
}

void
virt_viewer_app_free_connect_info(VirtViewerApp *self)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(self));

    virt_viewer_app_set_connect_info(self, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL);
}

VirtViewerWindow*
virt_viewer_app_get_main_window(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), NULL);

    return self->priv->main_window;
}

static void
show_status_cb(gpointer value,
               gpointer user_data)
{
    VirtViewerNotebook *nb = virt_viewer_window_get_notebook(VIRT_VIEWER_WINDOW(value));
    gchar *text = (gchar*)user_data;

    virt_viewer_notebook_show_status(nb, text);
}

void
virt_viewer_app_show_status(VirtViewerApp *self, const gchar *fmt, ...)
{
    va_list args;
    gchar *text;

    g_return_if_fail(VIRT_VIEWER_IS_APP(self));
    g_return_if_fail(fmt != NULL);

    va_start(args, fmt);
    text = g_strdup_vprintf(fmt, args);
    va_end(args);

    g_list_foreach(self->priv->windows, show_status_cb, text);
    g_free(text);
}

static void
show_display_cb(gpointer value,
                gpointer user_data G_GNUC_UNUSED)
{
    VirtViewerNotebook *nb = virt_viewer_window_get_notebook(VIRT_VIEWER_WINDOW(value));

    virt_viewer_notebook_show_display(nb);
}

void
virt_viewer_app_show_display(VirtViewerApp *self)
{
    g_return_if_fail(VIRT_VIEWER_IS_APP(self));
    g_list_foreach(self->priv->windows, show_display_cb, self);
}

gboolean
virt_viewer_app_get_enable_accel(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    return self->priv->enable_accel;
}

VirtViewerSession*
virt_viewer_app_get_session(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), FALSE);

    return self->priv->session;
}

GList*
virt_viewer_app_get_windows(VirtViewerApp *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_APP(self), NULL);
    return self->priv->windows;
}

static void
share_folder_changed(VirtViewerApp *self)
{
    gchar *folder;

    folder = gtk_file_chooser_get_filename(self->priv->preferences_shared_folder);

    g_object_set(virt_viewer_app_get_session(self),
                 "shared-folder", folder, NULL);

    g_free(folder);
}

static GtkWidget *
virt_viewer_app_get_preferences(VirtViewerApp *self)
{
    VirtViewerSession *session = virt_viewer_app_get_session(self);
    GtkBuilder *builder = virt_viewer_util_load_ui("virt-viewer-preferences.ui");
    gboolean can_share_folder = virt_viewer_session_can_share_folder(session);
    GtkWidget *preferences = self->priv->preferences;
    gchar *path;

    if (preferences)
        goto end;

    gtk_builder_connect_signals(builder, self);

    preferences = GTK_WIDGET(gtk_builder_get_object(builder, "preferences"));
    self->priv->preferences = preferences;

    g_object_set (gtk_builder_get_object(builder, "cbsharefolder"),
                  "sensitive", can_share_folder, NULL);
    g_object_set (gtk_builder_get_object(builder, "cbsharefolderro"),
                  "sensitive", can_share_folder, NULL);
    g_object_set (gtk_builder_get_object(builder, "fcsharefolder"),
                  "sensitive", can_share_folder, NULL);

    if (!can_share_folder)
        goto end;

    g_object_bind_property(virt_viewer_app_get_session(self),
                           "share-folder",
                           gtk_builder_get_object(builder, "cbsharefolder"),
                           "active",
                           G_BINDING_BIDIRECTIONAL|G_BINDING_SYNC_CREATE);

    g_object_bind_property(virt_viewer_app_get_session(self),
                           "share-folder-ro",
                           gtk_builder_get_object(builder, "cbsharefolderro"),
                           "active",
                           G_BINDING_BIDIRECTIONAL|G_BINDING_SYNC_CREATE);

    self->priv->preferences_shared_folder =
        GTK_FILE_CHOOSER(gtk_builder_get_object(builder, "fcsharefolder"));

    g_object_get(virt_viewer_app_get_session(self),
                 "shared-folder", &path, NULL);

    gtk_file_chooser_set_filename(self->priv->preferences_shared_folder, path);
    g_free(path);

    virt_viewer_signal_connect_object(self->priv->preferences_shared_folder,
                                      "file-set",
                                      G_CALLBACK(share_folder_changed), self,
                                      G_CONNECT_SWAPPED);

end:
    g_object_unref(builder);

    return preferences;
}

void
virt_viewer_app_show_preferences(VirtViewerApp *self, GtkWidget *parent)
{
    GtkWidget *preferences = virt_viewer_app_get_preferences(self);

    gtk_window_set_transient_for(GTK_WINDOW(preferences),
                                 GTK_WINDOW(parent));

    gtk_window_present(GTK_WINDOW(preferences));
}

static gboolean
option_kiosk_quit(G_GNUC_UNUSED const gchar *option_name,
                  const gchar *value,
                  G_GNUC_UNUSED gpointer data, GError **error)
{
    if (g_str_equal(value, "never")) {
        opt_kiosk_quit = FALSE;
        return TRUE;
    }
    if (g_str_equal(value, "on-disconnect")) {
        opt_kiosk_quit = TRUE;
        return TRUE;
    }

    g_set_error(error, G_OPTION_ERROR, G_OPTION_ERROR_FAILED, _("Invalid kiosk-quit argument: %s"), value);
    return FALSE;
}

static void
virt_viewer_app_add_option_entries(G_GNUC_UNUSED VirtViewerApp *self,
                                   G_GNUC_UNUSED GOptionContext *context,
                                   GOptionGroup *group)
{
    static const GOptionEntry options [] = {
        { "version", 'V', 0, G_OPTION_ARG_NONE, &opt_version,
          N_("Display version information"), NULL },
        { "zoom", 'z', 0, G_OPTION_ARG_INT, &opt_zoom,
          N_("Zoom level of window, in percentage"), "ZOOM" },
        { "full-screen", 'f', 0, G_OPTION_ARG_NONE, &opt_fullscreen,
          N_("Open in full screen mode (adjusts guest resolution to fit the client)"), NULL },
        { "hotkeys", 'H', 0, G_OPTION_ARG_STRING, &opt_hotkeys,
          N_("Customise hotkeys"), NULL },
        { "kiosk", 'k', 0, G_OPTION_ARG_NONE, &opt_kiosk,
          N_("Enable kiosk mode"), NULL },
        { "kiosk-quit", '\0', 0, G_OPTION_ARG_CALLBACK, option_kiosk_quit,
          N_("Quit on given condition in kiosk mode"), N_("<never|on-disconnect>") },
        { "verbose", 'v', 0, G_OPTION_ARG_NONE, &opt_verbose,
          N_("Display verbose information"), NULL },
        { "debug", '\0', 0, G_OPTION_ARG_NONE, &opt_debug,
          N_("Display debugging information"), NULL },
        { NULL, 0, 0, G_OPTION_ARG_NONE, NULL, NULL, NULL }
    };

    g_option_group_add_entries(group, options);
}

gboolean virt_viewer_app_get_session_cancelled(VirtViewerApp *self)
{
    return self->priv->cancelled;
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
