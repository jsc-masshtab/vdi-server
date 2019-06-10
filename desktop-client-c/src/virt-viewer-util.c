/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2007-2015 Red Hat, Inc.
 * Copyright (C) 2009-2012 Daniel P. Berrange
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

#include <glib.h>
#include <glib/gi18n.h>
#include <locale.h>

#ifdef G_OS_WIN32
#include <windows.h>
#include <io.h>
#endif

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>
#include <libxml/xpath.h>
#include <libxml/uri.h>

#include "virt-viewer-util.h"

GQuark
virt_viewer_error_quark(void)
{
  return g_quark_from_static_string ("virt-viewer-error-quark");
}

GtkBuilder *virt_viewer_util_load_ui(const char *name)
{
    GtkBuilder *builder;
    gchar *resource = g_strdup_printf("%s/ui/%s",
                                      VIRT_VIEWER_RESOURCE_PREFIX,
                                      name);

    builder = gtk_builder_new_from_resource(resource);

    g_free(resource);
    return builder;
}
//  spice://192.168.11.110:5908
int
virt_viewer_util_extract_host(const char *uristr,
                              char **scheme,
                              char **host,
                              char **transport,
                              char **user,
                              int *port)
{
    xmlURIPtr uri;
    char *offset = NULL;

    if (uristr == NULL ||
        !g_ascii_strcasecmp(uristr, "xen"))
        uristr = "xen:///";

    uri = xmlParseURI(uristr);
    g_return_val_if_fail(uri != NULL, 1);

    if (host) {
        if (!uri->server) {
            *host = g_strdup("localhost");
        } else {
            if (uri->server[0] == '[') {
                gchar *tmp;
                *host = g_strdup(uri->server + 1);
                if ((tmp = strchr(*host, ']')))
                    *tmp = '\0';
            } else {
                *host = g_strdup(uri->server);
            }
        }
    }

    if (user) {
        if (uri->user)
            *user = g_strdup(uri->user);
        else
            *user = NULL;
    }

    if (port)
        *port = uri->port;

    if (uri->scheme)
        offset = strchr(uri->scheme, '+');

    if (transport) {
        if (offset)
            *transport = g_strdup(offset + 1);
        else
            *transport = NULL;
    }

    if (scheme && uri->scheme) {
        if (offset)
            *scheme = g_strndup(uri->scheme, offset - uri->scheme);
        else
            *scheme = g_strdup(uri->scheme);
    }

    xmlFreeURI(uri);
    return 0;
}

typedef struct {
    GObject *instance;
    GObject *observer;
    GClosure *closure;
    gulong handler_id;
} WeakHandlerCtx;

static WeakHandlerCtx *
whc_new(GObject *instance,
        GObject *observer)
{
    WeakHandlerCtx *ctx = g_new0(WeakHandlerCtx, 1);

    ctx->instance = instance;
    ctx->observer = observer;

    return ctx;
}

static void
whc_free(WeakHandlerCtx *ctx)
{
    g_free(ctx);
}

static void observer_destroyed_cb(gpointer, GObject *);
static void closure_invalidated_cb(gpointer, GClosure *);

/*
 * If signal handlers are removed before the object is destroyed, this
 * callback will never get triggered.
 */
static void
instance_destroyed_cb(gpointer ctx_,
                      GObject *where_the_instance_was G_GNUC_UNUSED)
{
    WeakHandlerCtx *ctx = ctx_;

    /* No need to disconnect the signal here, the instance has gone away. */
    g_object_weak_unref(ctx->observer, observer_destroyed_cb, ctx);
    g_closure_remove_invalidate_notifier(ctx->closure, ctx,
                                         closure_invalidated_cb);
    whc_free(ctx);
}

/* Triggered when the observer is destroyed. */
static void
observer_destroyed_cb(gpointer ctx_,
                      GObject *where_the_observer_was G_GNUC_UNUSED)
{
    WeakHandlerCtx *ctx = ctx_;

    g_closure_remove_invalidate_notifier(ctx->closure, ctx,
                                         closure_invalidated_cb);
    g_signal_handler_disconnect(ctx->instance, ctx->handler_id);
    g_object_weak_unref(ctx->instance, instance_destroyed_cb, ctx);
    whc_free(ctx);
}

/* Triggered when either object is destroyed or the handler is disconnected. */
static void
closure_invalidated_cb(gpointer ctx_,
                       GClosure *where_the_closure_was G_GNUC_UNUSED)
{
    WeakHandlerCtx *ctx = ctx_;

    g_object_weak_unref(ctx->instance, instance_destroyed_cb, ctx);
    g_object_weak_unref(ctx->observer, observer_destroyed_cb, ctx);
    whc_free(ctx);
}

/* Copied from tp_g_signal_connect_object. */
/**
  * virt_viewer_signal_connect_object: (skip)
  * @instance: the instance to connect to.
  * @detailed_signal: a string of the form "signal-name::detail".
  * @c_handler: the #GCallback to connect.
  * @gobject: the object to pass as data to @c_handler.
  * @connect_flags: a combination of #GConnectFlags.
  *
  * Similar to g_signal_connect_object() but will delete connection
  * when any of the objects is destroyed.
  *
  * Returns: the handler id.
  */
gulong virt_viewer_signal_connect_object(gpointer instance,
                                         const gchar *detailed_signal,
                                         GCallback c_handler,
                                         gpointer gobject,
                                         GConnectFlags connect_flags)
{
    GObject *instance_obj = G_OBJECT(instance);
    WeakHandlerCtx *ctx = whc_new(instance_obj, gobject);

    g_return_val_if_fail(G_TYPE_CHECK_INSTANCE (instance), 0);
    g_return_val_if_fail(detailed_signal != NULL, 0);
    g_return_val_if_fail(c_handler != NULL, 0);
    g_return_val_if_fail(G_IS_OBJECT (gobject), 0);
    g_return_val_if_fail((connect_flags & ~(G_CONNECT_AFTER|G_CONNECT_SWAPPED)) == 0, 0);

    if (connect_flags & G_CONNECT_SWAPPED)
        ctx->closure = g_cclosure_new_object_swap(c_handler, gobject);
    else
        ctx->closure = g_cclosure_new_object(c_handler, gobject);

    ctx->handler_id = g_signal_connect_closure(instance, detailed_signal,
                                               ctx->closure, (connect_flags & G_CONNECT_AFTER) ? TRUE : FALSE);

    g_object_weak_ref(instance_obj, instance_destroyed_cb, ctx);
    g_object_weak_ref(gobject, observer_destroyed_cb, ctx);
    g_closure_add_invalidate_notifier(ctx->closure, ctx,
                                      closure_invalidated_cb);

    return ctx->handler_id;
}

static void log_handler(const gchar *log_domain,
                        GLogLevelFlags log_level,
                        const gchar *message,
                        gpointer unused_data)
{
    if (glib_check_version(2, 32, 0) != NULL)
        if (log_level >= G_LOG_LEVEL_DEBUG && !doDebug)
            return;

    g_log_default_handler(log_domain, log_level, message, unused_data);
}

#ifdef G_OS_WIN32
static BOOL is_handle_valid(HANDLE h)
{
    if (h == INVALID_HANDLE_VALUE || h == NULL)
        return FALSE;

    DWORD flags;
    return GetHandleInformation(h, &flags);
}
#endif

void virt_viewer_util_init(const char *appname)
{
#ifdef G_OS_WIN32
    /*
     * This named mutex will be kept around by Windows until the
     * process terminates. This allows other instances to check if it
     * already exists, indicating already running instances. It is
     * used to warn the user that installer can't proceed in this
     * case.
     */
    CreateMutexA(0, 0, "VirtViewerMutex");

    /* Get redirection from parent */
    BOOL out_valid = is_handle_valid(GetStdHandle(STD_OUTPUT_HANDLE));
    BOOL err_valid = is_handle_valid(GetStdHandle(STD_ERROR_HANDLE));

    /*
     * If not all output are redirected try to redirect to parent console.
     * If parent has no console (for instance as launched from GUI) just
     * rely on default (no output).
     */
    if ((!out_valid || !err_valid) && AttachConsole(ATTACH_PARENT_PROCESS)) {
        if (!out_valid) {
            freopen("CONOUT$", "w", stdout);
            dup2(fileno(stdout), STDOUT_FILENO);
        }
        if (!err_valid) {
            freopen("CONOUT$", "w", stderr);
            dup2(fileno(stderr), STDERR_FILENO);
        }
    }
#endif

    setlocale(LC_ALL, "");
    //bindtextdomain(GETTEXT_PACKAGE, LOCALE_DIR); solo fix
    bind_textdomain_codeset(GETTEXT_PACKAGE, "UTF-8");
    textdomain(GETTEXT_PACKAGE);

    g_set_application_name(appname);

    g_log_set_handler(G_LOG_DOMAIN, G_LOG_LEVEL_MASK, log_handler, NULL);
}

static gchar *
ctrl_key_to_gtk_key(const gchar *key)
{
    guint i;

    static const struct {
        const char *ctrl;
        const char *gtk;
    } keys[] = {
        /* FIXME: right alt, right ctrl, right shift, cmds */
        { "alt", "<Alt>" },
        { "ralt", "<Alt>" },
        { "rightalt", "<Alt>" },
        { "right-alt", "<Alt>" },
        { "lalt", "<Alt>" },
        { "leftalt", "<Alt>" },
        { "left-alt", "<Alt>" },

        { "ctrl", "<Ctrl>" },
        { "rctrl", "<Ctrl>" },
        { "rightctrl", "<Ctrl>" },
        { "right-ctrl", "<Ctrl>" },
        { "lctrl", "<Ctrl>" },
        { "leftctrl", "<Ctrl>" },
        { "left-ctrl", "<Ctrl>" },

        { "shift", "<Shift>" },
        { "rshift", "<Shift>" },
        { "rightshift", "<Shift>" },
        { "right-shift", "<Shift>" },
        { "lshift", "<Shift>" },
        { "leftshift", "<Shift>" },
        { "left-shift", "<Shift>" },

        { "cmd", "<Ctrl>" },
        { "rcmd", "<Ctrl>" },
        { "rightcmd", "<Ctrl>" },
        { "right-cmd", "<Ctrl>" },
        { "lcmd", "<Ctrl>" },
        { "leftcmd", "<Ctrl>" },
        { "left-cmd", "<Ctrl>" },

        { "win", "<Super>" },
        { "rwin", "<Super>" },
        { "rightwin", "<Super>" },
        { "right-win", "<Super>" },
        { "lwin", "<Super>" },
        { "leftwin", "<Super>" },
        { "left-win", "<Super>" },

        { "esc", "Escape" },
        /* { "escape", "Escape" }, */

        { "ins", "Insert" },
        /* { "insert", "Insert" }, */

        { "del", "Delete" },
        /* { "delete", "Delete" }, */

        { "pgup", "Page_Up" },
        { "pageup", "Page_Up" },
        { "pgdn", "Page_Down" },
        { "pagedown", "Page_Down" },

        /* { "home", "home" }, */
        { "end", "End" },
        /* { "space", "space" }, */

        { "enter", "Return" },

        /* { "tab", "tab" }, */
        /* { "f1", "F1" }, */
        /* { "f2", "F2" }, */
        /* { "f3", "F3" }, */
        /* { "f4", "F4" }, */
        /* { "f5", "F5" }, */
        /* { "f6", "F6" }, */
        /* { "f7", "F7" }, */
        /* { "f8", "F8" }, */
        /* { "f9", "F9" }, */
        /* { "f10", "F10" }, */
        /* { "f11", "F11" }, */
        /* { "f12", "F12" } */
    };

    for (i = 0; i < G_N_ELEMENTS(keys); ++i) {
        if (g_ascii_strcasecmp(keys[i].ctrl, key) == 0)
            return g_strdup(keys[i].gtk);
    }

    return g_ascii_strup(key, -1);
}

gchar*
spice_hotkey_to_gtk_accelerator(const gchar *key)
{
    gchar *accel, **k, **keyv;

    keyv = g_strsplit(key, "+", -1);
    g_return_val_if_fail(keyv != NULL, NULL);

    for (k = keyv; *k != NULL; k++) {
        gchar *tmp = *k;
        *k = ctrl_key_to_gtk_key(tmp);
        g_free(tmp);
    }

    accel = g_strjoinv(NULL, keyv);
    g_strfreev(keyv);

    return accel;
}

static gboolean str_is_empty(const gchar *str)
{
  return ((str == NULL) || (str[0] == '\0'));
}

static gint
virt_viewer_compare_version(const gchar *s1, const gchar *s2)
{
    gint i, retval = 0;
    gchar **v1, **v2;

    if (str_is_empty(s1) && str_is_empty(s2)) {
      return 0;
    } else if (str_is_empty(s1)) {
      return -1;
    } else if (str_is_empty(s2)) {
      return 1;
    }

    v1 = g_strsplit(s1, ".", -1);
    v2 = g_strsplit(s2, ".", -1);

    for (i = 0; v1[i] && v2[i]; ++i) {
        gchar *e1 = NULL, *e2 = NULL;
        guint64 m1 = g_ascii_strtoull(v1[i], &e1, 10);
        guint64 m2 = g_ascii_strtoull(v2[i], &e2, 10);

        retval = m1 - m2;
        if (retval != 0)
            goto end;

        g_return_val_if_fail(e1 && e2, 0);
        if (*e1 || *e2) {
            g_warning("the version string contains a suffix");
            goto end;
        }
    }

    if (v1[i])
        retval = 1;
    else if (v2[i])
        retval = -1;

end:
    g_strfreev(v1);
    g_strfreev(v2);
    return retval;
}

/**
 * virt_viewer_compare_buildid:
 * @s1: a version-like string
 * @s2: a version-like string
 *
 * Compare two buildid strings: 1.1-1 > 1.0-1, 1.0-2 > 1.0-1, 1.10 > 1.7...
 *
 * String suffix (1.0rc1 etc) are not accepted, and will return 0.
 *
 * Returns: negative value if s1 < s2; zero if s1 = s2; positive value if s1 > s2.
 **/
gint
virt_viewer_compare_buildid(const gchar *s1, const gchar *s2)
{
    int ret = 0;
    GStrv split1 = NULL;
    GStrv split2 = NULL;

    split1 = g_strsplit(s1, "-", 2);
    split2 = g_strsplit(s2, "-", 2);
    if ((split1 == NULL) || (split2 == NULL)) {
      goto end;
    }
    /* Compare versions */
    ret = virt_viewer_compare_version(split1[0], split2[0]);
    if (ret != 0) {
        goto end;
    }
    if ((split1[0] == NULL) || (split2[0] == NULL)) {
      goto end;
    }

    /* Compare -release */
    ret = virt_viewer_compare_version(split1[1], split2[1]);

end:
    g_strfreev(split1);
    g_strfreev(split2);

    return ret;
}

/* simple sorting of monitors. Primary sort left-to-right, secondary sort from
 * top-to-bottom, finally by monitor id */
static int
displays_cmp(const void *p1, const void *p2, gpointer user_data)
{
    guint diff;
    GHashTable *displays = user_data;
    guint i = *(guint*)p1;
    guint j = *(guint*)p2;
    GdkRectangle *m1 = g_hash_table_lookup(displays, GINT_TO_POINTER(i));
    GdkRectangle *m2 = g_hash_table_lookup(displays, GINT_TO_POINTER(j));
    g_return_val_if_fail(m1 != NULL && m2 != NULL, 0);
    diff = m1->x - m2->x;
    if (diff == 0)
        diff = m1->y - m2->y;
    if (diff == 0)
        diff = i - j;

    return diff;
}

static void find_max_id(gpointer key,
                        gpointer value G_GNUC_UNUSED,
                        gpointer user_data)
{
    guint *max_id = user_data;
    guint id = GPOINTER_TO_INT(key);
    *max_id = MAX(*max_id, id);
}

void
virt_viewer_align_monitors_linear(GHashTable *displays)
{
    guint i;
    gint x = 0;
    guint *sorted_displays;
    guint max_id = 0;
    guint ndisplays = 0;
    GHashTableIter iter;
    gpointer key;

    g_return_if_fail(displays != NULL);

    if (g_hash_table_size(displays) == 0)
        return;

    g_hash_table_foreach(displays, find_max_id, &max_id);
    ndisplays = max_id + 1;

    sorted_displays = g_new0(guint, ndisplays);

    g_hash_table_iter_init(&iter, displays);
    while (g_hash_table_iter_next(&iter, &key, NULL))
        sorted_displays[GPOINTER_TO_INT(key)] = GPOINTER_TO_INT(key);

    g_qsort_with_data(sorted_displays, ndisplays, sizeof(guint), displays_cmp, displays);

    /* adjust monitor positions so that there's no gaps or overlap between
     * monitors */
    for (i = 0; i < ndisplays; i++) {
        guint nth = sorted_displays[i];
        g_assert(nth < ndisplays);
        GdkRectangle *rect = g_hash_table_lookup(displays, GINT_TO_POINTER(nth));
        g_return_if_fail(rect != NULL);
        rect->x = x;
        rect->y = 0;
        x += rect->width;
    }
    g_free(sorted_displays);
}

/* Shift all displays so that the monitor origin is at (0,0). This reduces the
 * size of the screen that will be required on the guest when all client
 * monitors are fullscreen but do not begin at the origin. For example, instead
 * of sending down the following configuration:
 *   1280x1024+4240+0
 * (which implies that the guest screen must be at least 5520x1024), we'd send
 *   1280x1024+0+0
 * (which implies the guest screen only needs to be 1280x1024). The first
 * version might fail if the guest video memory is not large enough to handle a
 * screen of that size.
 */
void
virt_viewer_shift_monitors_to_origin(GHashTable *displays)
{
    gint xmin = G_MAXINT;
    gint ymin = G_MAXINT;
    GHashTableIter iter;
    gpointer value;

    if (g_hash_table_size(displays) == 0)
        return;

    g_hash_table_iter_init(&iter, displays);
    while (g_hash_table_iter_next(&iter, NULL, &value)) {
        GdkRectangle *display = value;
        g_return_if_fail(display != NULL);
        if (display->width > 0 && display->height > 0) {
            xmin = MIN(xmin, display->x);
            ymin = MIN(ymin, display->y);
        }
    }
    g_return_if_fail(xmin < G_MAXINT && ymin < G_MAXINT);

    if (xmin > 0 || ymin > 0) {
        g_debug("%s: Shifting all monitors by (%i, %i)", G_STRFUNC, xmin, ymin);
        g_hash_table_iter_init(&iter, displays);
        while (g_hash_table_iter_next(&iter, NULL, &value)) {
            GdkRectangle *display = value;
            if (display->width > 0 && display->height > 0) {
                display->x -= xmin;
                display->y -= ymin;
            }
        }
    }
}

/**
 * virt_viewer_parse_monitor_mappings:
 * @mappings: (array zero-terminated=1) values for the "monitor-mapping" key
 * @nmappings: the size of @mappings
 * @nmonitors: the count of client's monitors
 *
 * Parses and validates monitor mappings values to return a hash table
 * containing the mapping from guest display ids to client monitors ids.
 *
 * Returns: (transfer full) a #GHashTable containing mapping from guest display
 *  ids to client monitor ids or %NULL if the mapping is invalid.
 */
GHashTable*
virt_viewer_parse_monitor_mappings(gchar **mappings, const gsize nmappings, const gint nmonitors)
{
    GHashTable *displaymap;
    GHashTable *monitormap;
    guint i, max_display_id = 0;
    gchar **tokens = NULL;

    g_return_val_if_fail(nmonitors != 0, NULL);
    displaymap = g_hash_table_new(g_direct_hash, g_direct_equal);
    monitormap = g_hash_table_new(g_direct_hash, g_direct_equal);
    if (nmappings == 0) {
        g_warning("Empty monitor-mapping configuration");
        goto configerror;
    }

    for (i = 0; i < nmappings; i++) {
        gchar *endptr = NULL;
        gint display = 0, monitor = 0;

        tokens = g_strsplit(mappings[i], ":", 2);
        if (g_strv_length(tokens) != 2) {
            g_warning("Invalid monitor-mapping configuration: '%s'. "
                      "Expected format is '<DISPLAY-ID>:<MONITOR-ID>'",
                      mappings[i]);
            g_strfreev(tokens);
            goto configerror;
        }

        display = strtol(tokens[0], &endptr, 10);
        if ((endptr && *endptr != '\0') || display < 1) {
            g_warning("Invalid monitor-mapping configuration: display id is invalid: %s %p='%s'", tokens[0], endptr, endptr);
            g_strfreev(tokens);
            goto configerror;
        }
        monitor = strtol(tokens[1], &endptr, 10);
        if ((endptr && *endptr != '\0') || monitor < 1) {
            g_warning("Invalid monitor-mapping configuration: monitor id '%s' is invalid", tokens[1]);
            g_strfreev(tokens);
            goto configerror;
        }
        g_strfreev(tokens);

        if (monitor > nmonitors) {
            g_warning("Invalid monitor-mapping configuration: monitor #%i for display #%i does not exist", monitor, display);
            goto configerror;
        }

        /* config file format is 1-based, not 0-based */
        display--;
        monitor--;

        if (g_hash_table_lookup_extended(displaymap, GINT_TO_POINTER(display), NULL, NULL) ||
            g_hash_table_lookup_extended(monitormap, GINT_TO_POINTER(monitor), NULL, NULL)) {
            g_warning("Invalid monitor-mapping configuration: a display or monitor id was specified twice");
            goto configerror;
        }
        g_debug("Fullscreen config: mapping guest display %i to monitor %i", display, monitor);
        g_hash_table_insert(displaymap, GINT_TO_POINTER(display), GINT_TO_POINTER(monitor));
        g_hash_table_insert(monitormap, GINT_TO_POINTER(monitor), GINT_TO_POINTER(display));
        max_display_id = MAX((guint) display, max_display_id);
    }

    for (i = 0; i < max_display_id; i++) {
        if (!g_hash_table_lookup_extended(displaymap, GINT_TO_POINTER(i), NULL, NULL)) {
            g_warning("Invalid monitor-mapping configuration: display #%d was not specified", i+1);
            goto configerror;
        }
    }

    g_hash_table_unref(monitormap);
    return displaymap;

configerror:
    g_hash_table_unref(monitormap);
    g_hash_table_unref(displaymap);
    return NULL;
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
