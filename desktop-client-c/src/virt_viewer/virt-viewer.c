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

#include <libvirt/libvirt.h>
#include <libvirt/virterror.h>
#include <libvirt-glib/libvirt-glib.h>
#include <libxml/xpath.h>
#include <libxml/uri.h>

#if defined(HAVE_SOCKETPAIR)
#include <sys/socket.h>
#endif

#include "virt-viewer.h"
#include "virt-viewer-app.h"
#include "virt-viewer-vm-connection.h"
#include "virt-viewer-auth.h"
#include "virt-viewer-util.h"

#ifdef HAVE_SPICE_GTK
#include "virt-viewer-session-spice.h"
#endif

struct _VirtViewerPrivate {
    char *uri;
    virConnectPtr conn;
    virDomainPtr dom;
    char *domkey;
    gboolean waitvm;
    gboolean reconnect;
    gboolean auth_cancelled;
    gint domain_event;
    guint reconnect_poll; /* source id */
};

G_DEFINE_TYPE (VirtViewer, virt_viewer, VIRT_VIEWER_TYPE_APP)
#define GET_PRIVATE(o)                                                        \
    (G_TYPE_INSTANCE_GET_PRIVATE ((o), VIRT_VIEWER_TYPE, VirtViewerPrivate))

static gboolean virt_viewer_initial_connect(VirtViewerApp *self, GError **error);
static gboolean virt_viewer_open_connection(VirtViewerApp *self, int *fd);
static void virt_viewer_deactivated(VirtViewerApp *self, gboolean connect_error);
static gboolean virt_viewer_start(VirtViewerApp *self, GError **error);
static void virt_viewer_dispose (GObject *object);
static int virt_viewer_connect(VirtViewerApp *app, GError **error);

static gchar **opt_args = NULL;
static gchar *opt_uri = NULL;
static gboolean opt_direct = FALSE;
static gboolean opt_attach = FALSE;
static gboolean opt_waitvm = FALSE;
static gboolean opt_reconnect = FALSE;

typedef enum {
    DOMAIN_SELECTION_ID = (1 << 0),
    DOMAIN_SELECTION_UUID = (1 << 1),
    DOMAIN_SELECTION_NAME = (1 << 2),
    DOMAIN_SELECTION_DEFAULT = DOMAIN_SELECTION_ID | DOMAIN_SELECTION_UUID | DOMAIN_SELECTION_NAME,
} DomainSelection;

static const gchar* domain_selection_to_opt[] = {
    [DOMAIN_SELECTION_ID] = "--id",
    [DOMAIN_SELECTION_UUID] = "--uuid",
    [DOMAIN_SELECTION_NAME] = "--domain-name",
};

static DomainSelection domain_selection_type = DOMAIN_SELECTION_DEFAULT;

static gboolean
opt_domain_selection_cb(const gchar *option_name,
                        const gchar *value G_GNUC_UNUSED,
                        gpointer data G_GNUC_UNUSED,
                        GError **error)
{
    guint i;
    if (domain_selection_type != DOMAIN_SELECTION_DEFAULT) {
        g_set_error(error, G_OPTION_ERROR, G_OPTION_ERROR_FAILED,
                    "selection type has been already set");
        return FALSE;
    }

    for (i = DOMAIN_SELECTION_ID; i < G_N_ELEMENTS(domain_selection_to_opt); i++) {
        if (g_strcmp0(option_name, domain_selection_to_opt[i]) == 0) {
            domain_selection_type = i;
            return TRUE;
        }
    }

    g_assert_not_reached();
    return FALSE;
}

static void
virt_viewer_add_option_entries(VirtViewerApp *self, GOptionContext *context, GOptionGroup *group)
{
    static const GOptionEntry options[] = {
        { "direct", 'd', 0, G_OPTION_ARG_NONE, &opt_direct,
          N_("Direct connection with no automatic tunnels"), NULL },
        { "attach", 'a', 0, G_OPTION_ARG_NONE, &opt_attach,
          N_("Attach to the local display using libvirt"), NULL },
        { "connect", 'c', 0, G_OPTION_ARG_STRING, &opt_uri,
          N_("Connect to hypervisor"), "URI"},
        { "wait", 'w', 0, G_OPTION_ARG_NONE, &opt_waitvm,
          N_("Wait for domain to start"), NULL },
        { "reconnect", 'r', 0, G_OPTION_ARG_NONE, &opt_reconnect,
          N_("Reconnect to domain upon restart"), NULL },
        { "domain-name", '\0', G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK, opt_domain_selection_cb,
          N_("Select the virtual machine only by its name"), NULL },
        { "id", '\0', G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK, opt_domain_selection_cb,
          N_("Select the virtual machine only by its id"), NULL },
        { "uuid", '\0', G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK, opt_domain_selection_cb,
          N_("Select the virtual machine only by its uuid"), NULL },
        { G_OPTION_REMAINING, '\0', 0, G_OPTION_ARG_STRING_ARRAY, &opt_args,
          NULL, "-- ID|UUID|DOMAIN-NAME" },
        { NULL, 0, 0, G_OPTION_ARG_NONE, NULL, NULL, NULL }
    };

    VIRT_VIEWER_APP_CLASS(virt_viewer_parent_class)->add_option_entries(self, context, group);
    g_option_context_set_summary(context, _("Virtual machine graphical console"));
    g_option_group_add_entries(group, options);
}

static gboolean
virt_viewer_local_command_line (GApplication   *gapp,
                                gchar        ***args,
                                int            *status)
{
    gboolean ret = FALSE;
    VirtViewer *self = VIRT_VIEWER(gapp);
    VirtViewerApp *app = VIRT_VIEWER_APP(gapp);

    ret = G_APPLICATION_CLASS(virt_viewer_parent_class)->local_command_line(gapp, args, status);
    if (ret)
        goto end;

    if (opt_args) {
        if (g_strv_length(opt_args) != 1) {
            g_printerr(_("\nUsage: %s [OPTIONS] [ID|UUID|DOMAIN-NAME]\n\n"), PACKAGE);
            ret = TRUE;
            *status = 1;
            goto end;
        }

        self->priv->domkey = g_strdup(opt_args[0]);
    }


    if (opt_waitvm || domain_selection_type != DOMAIN_SELECTION_DEFAULT) {
        if (!self->priv->domkey) {
            g_printerr(_("\nNo ID|UUID|DOMAIN-NAME was specified for '%s'\n\n"),
                       opt_waitvm ? "--wait" : domain_selection_to_opt[domain_selection_type]);
            ret = TRUE;
            *status = 1;
            goto end;
        }

        self->priv->waitvm = opt_waitvm;
    }

    virt_viewer_app_set_direct(app, opt_direct);
    virt_viewer_app_set_attach(app, opt_attach);
    self->priv->reconnect = opt_reconnect;
    self->priv->uri = g_strdup(opt_uri);

end:
    if (ret && *status)
        g_printerr(_("Run '%s --help' to see a full list of available command line options\n"), g_get_prgname());

    g_strfreev(opt_args);
    g_free(opt_uri);
    return ret;
}

static void
virt_viewer_class_init (VirtViewerClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    VirtViewerAppClass *app_class = VIRT_VIEWER_APP_CLASS (klass);
    GApplicationClass *g_app_class = G_APPLICATION_CLASS(klass);

    g_type_class_add_private (klass, sizeof (VirtViewerPrivate));

    object_class->dispose = virt_viewer_dispose;

    app_class->initial_connect = virt_viewer_initial_connect;
    app_class->deactivated = virt_viewer_deactivated;
    app_class->open_connection = virt_viewer_open_connection;
    app_class->start = virt_viewer_start;
    app_class->add_option_entries = virt_viewer_add_option_entries;

    g_app_class->local_command_line = virt_viewer_local_command_line;
}

static void
virt_viewer_init(VirtViewer *self)
{
    self->priv = GET_PRIVATE(self);
    self->priv->domain_event = -1;
}

static gboolean
virt_viewer_connect_timer(void *opaque)
{
    VirtViewer *self = VIRT_VIEWER(opaque);
    VirtViewerApp *app = VIRT_VIEWER_APP(self);

    g_debug("Connect timer fired");

    if (!virt_viewer_app_is_active(app) &&
        !virt_viewer_app_initial_connect(app, NULL))
        g_application_quit(G_APPLICATION(app));

    if (virt_viewer_app_is_active(app)) {
        self->priv->reconnect_poll = 0;
        return FALSE;
    }

    return TRUE;
}

static void
virt_viewer_start_reconnect_poll(VirtViewer *self)
{
    VirtViewerPrivate *priv = self->priv;

    g_debug("reconnect_poll: %d", priv->reconnect_poll);

    if (priv->reconnect_poll != 0)
        return;

    priv->reconnect_poll = g_timeout_add(500, virt_viewer_connect_timer, self);
}

static void
virt_viewer_stop_reconnect_poll(VirtViewer *self)
{
    VirtViewerPrivate *priv = self->priv;

    g_debug("reconnect_poll: %d", priv->reconnect_poll);

    if (priv->reconnect_poll == 0)
        return;

    g_source_remove(priv->reconnect_poll);
    priv->reconnect_poll = 0;
}

static void
virt_viewer_deactivated(VirtViewerApp *app, gboolean connect_error)
{
    VirtViewer *self = VIRT_VIEWER(app);
    VirtViewerPrivate *priv = self->priv;

    if (priv->dom) {
        virDomainFree(priv->dom);
        priv->dom = NULL;
    }

    if (priv->reconnect && !virt_viewer_app_get_session_cancelled(app)) {
        if (priv->domain_event < 0) {
            g_debug("No domain events, falling back to polling");
            virt_viewer_start_reconnect_poll(self);
        }

        virt_viewer_app_show_status(app, _("Waiting for guest domain to re-start"));
        virt_viewer_app_trace(app, "Guest %s display has disconnected, waiting to reconnect", priv->domkey);
        virt_viewer_app_set_menus_sensitive(app, FALSE);
    } else {
        VIRT_VIEWER_APP_CLASS(virt_viewer_parent_class)->deactivated(app, connect_error);
    }
}

static int
virt_viewer_parse_uuid(const char *name,
                       unsigned char *uuid)
{
    int i;

    const char *cur = name;
    for (i = 0;i < 16;) {
        uuid[i] = 0;
        if (*cur == 0)
            return -1;
        if ((*cur == '-') || (*cur == ' ')) {
            cur++;
            continue;
        }
        if ((*cur >= '0') && (*cur <= '9'))
            uuid[i] = *cur - '0';
        else if ((*cur >= 'a') && (*cur <= 'f'))
            uuid[i] = *cur - 'a' + 10;
        else if ((*cur >= 'A') && (*cur <= 'F'))
            uuid[i] = *cur - 'A' + 10;
        else
            return -1;
        uuid[i] *= 16;
        cur++;
        if (*cur == 0)
            return -1;
        if ((*cur >= '0') && (*cur <= '9'))
            uuid[i] += *cur - '0';
        else if ((*cur >= 'a') && (*cur <= 'f'))
            uuid[i] += *cur - 'a' + 10;
        else if ((*cur >= 'A') && (*cur <= 'F'))
            uuid[i] += *cur - 'A' + 10;
        else
            return -1;
        i++;
        cur++;
    }

    return 0;
}


static virDomainPtr
virt_viewer_lookup_domain(VirtViewer *self)
{
    char *end;
    VirtViewerPrivate *priv = self->priv;
    virDomainPtr dom = NULL;

    if (priv->domkey == NULL) {
        return NULL;
    }

    if (domain_selection_type & DOMAIN_SELECTION_ID) {
        long int id = strtol(priv->domkey, &end, 10);
        if (id >= 0 && end && !*end) {
            dom = virDomainLookupByID(priv->conn, id);
        }
    }

    if (domain_selection_type & DOMAIN_SELECTION_UUID) {
        unsigned char uuid[16];
        if (dom == NULL && virt_viewer_parse_uuid(priv->domkey, uuid) == 0) {
            dom = virDomainLookupByUUID(priv->conn, uuid);
        }
    }

    if (domain_selection_type & DOMAIN_SELECTION_NAME) {
        if (dom == NULL) {
            dom = virDomainLookupByName(priv->conn, priv->domkey);
        }
    }

    return dom;
}

static int
virt_viewer_matches_domain(VirtViewer *self,
                           virDomainPtr dom)
{
    char *end;
    const char *name;
    VirtViewerPrivate *priv = self->priv;
    int id = strtol(priv->domkey, &end, 10);
    unsigned char wantuuid[16];
    unsigned char domuuid[16];

    if (id >= 0 && end && !*end) {
        if (virDomainGetID(dom) == id)
            return 1;
    }
    if (virt_viewer_parse_uuid(priv->domkey, wantuuid) == 0) {
        virDomainGetUUID(dom, domuuid);
        if (memcmp(wantuuid, domuuid, VIR_UUID_BUFLEN) == 0)
            return 1;
    }

    name = virDomainGetName(dom);
    if (strcmp(name, priv->domkey) == 0)
        return 1;

    return 0;
}

static char *
virt_viewer_extract_xpath_string(const gchar *xmldesc,
                                 const gchar *xpath)
{
    xmlDocPtr xml = NULL;
    xmlParserCtxtPtr pctxt = NULL;
    xmlXPathContextPtr ctxt = NULL;
    xmlXPathObjectPtr obj = NULL;
    char *port = NULL;

    pctxt = xmlNewParserCtxt();
    if (!pctxt || !pctxt->sax)
        goto error;

    xml = xmlCtxtReadDoc(pctxt, (const xmlChar *)xmldesc, "domain.xml", NULL,
                         XML_PARSE_NOENT | XML_PARSE_NONET |
                         XML_PARSE_NOWARNING);
    if (!xml)
        goto error;

    ctxt = xmlXPathNewContext(xml);
    if (!ctxt)
        goto error;

    obj = xmlXPathEval((const xmlChar *)xpath, ctxt);
    if (!obj || obj->type != XPATH_STRING || !obj->stringval || !obj->stringval[0])
        goto error;
    if (!strcmp((const char*)obj->stringval, "-1"))
        goto error;

    port = g_strdup((const char*)obj->stringval);
    xmlXPathFreeObject(obj);
    obj = NULL;

 error:
    xmlXPathFreeObject(obj);
    xmlXPathFreeContext(ctxt);
    xmlFreeDoc(xml);
    xmlFreeParserCtxt(pctxt);
    return port;
}


static gboolean
virt_viewer_replace_host(const gchar *host)
{
    GInetAddress *addr;
    gboolean ret;

    if (!host)
        return TRUE;

    addr = g_inet_address_new_from_string(host);

    if (!addr) /* Parsing error means it was probably a hostname */
        return FALSE;

    ret = g_inet_address_get_is_any(addr);
    g_object_unref(addr);

    return ret;
}


static gboolean
virt_viewer_is_loopback(const char *host)
{
    GInetAddress *addr = NULL;
    gboolean is_loopback = FALSE;

    g_return_val_if_fail(host != NULL, FALSE);

    addr = g_inet_address_new_from_string(host);
    if (!addr) /* Parsing error means it was probably a hostname */
        return (strcmp(host, "localhost") == 0);

    is_loopback = g_inet_address_get_is_loopback(addr);
    g_object_unref(addr);

    return is_loopback;
}


static gboolean
virt_viewer_is_reachable(const gchar *host,
                         const char *transport,
                         const char *transport_host,
                         gboolean direct)
{
    gboolean host_is_loopback;
    gboolean transport_is_loopback;

    if (!host)
        return FALSE;

    if (!transport)
        return TRUE;

    if (strcmp(transport, "ssh") == 0 && !direct)
        return TRUE;

    if (strcmp(transport, "unix") == 0)
        return TRUE;

    host_is_loopback = virt_viewer_is_loopback(host);
    transport_is_loopback = virt_viewer_is_loopback(transport_host);

    if (transport_is_loopback && host_is_loopback)
        return TRUE;
    else
        return !host_is_loopback;
}


static gboolean
virt_viewer_extract_connect_info(VirtViewer *self,
                                 virDomainPtr dom,
                                 GError **error)
{
    char *type = NULL;
    char *xpath = NULL;
    gboolean retval = FALSE;
    char *xmldesc = virDomainGetXMLDesc(dom, 0);
    VirtViewerPrivate *priv = self->priv;
    VirtViewerApp *app = VIRT_VIEWER_APP(self);
    gchar *gport = NULL;
    gchar *gtlsport = NULL;
    gchar *ghost = NULL;
    gchar *unixsock = NULL;
    gchar *host = NULL;
    gchar *transport = NULL;
    gchar *user = NULL;
    gint port = 0;
    gchar *uri = NULL;
    gboolean direct = virt_viewer_app_get_direct(app);

    virt_viewer_app_free_connect_info(app);

    if ((type = virt_viewer_extract_xpath_string(xmldesc, "string(/domain/devices/graphics/@type)")) == NULL) {
        g_set_error(error,
                    VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Cannot determine the graphic type for the guest %s"), priv->domkey);

        goto cleanup;
    }

    if (!virt_viewer_app_create_session(app, type, error))
        goto cleanup;

    xpath = g_strdup_printf("string(/domain/devices/graphics[@type='%s']/@port)", type);
    gport = virt_viewer_extract_xpath_string(xmldesc, xpath);
    g_free(xpath);
    if (g_str_equal(type, "spice")) {
        xpath = g_strdup_printf("string(/domain/devices/graphics[@type='%s']/@tlsPort)", type);
        gtlsport = virt_viewer_extract_xpath_string(xmldesc, xpath);
        g_free(xpath);
    }

    if (gport || gtlsport) {
        xpath = g_strdup_printf("string(/domain/devices/graphics[@type='%s']/listen/@address)", type);
        ghost = virt_viewer_extract_xpath_string(xmldesc, xpath);
        if (ghost == NULL) { /* try old xml format - listen attribute in the graphics node */
            g_free(xpath);
            xpath = g_strdup_printf("string(/domain/devices/graphics[@type='%s']/@listen)", type);
            ghost = virt_viewer_extract_xpath_string(xmldesc, xpath);
        }
    } else {
        xpath = g_strdup_printf("string(/domain/devices/graphics[@type='%s']/listen/@socket)", type);
        unixsock = virt_viewer_extract_xpath_string(xmldesc, xpath);
        if (unixsock == NULL) { /* try old xml format - socket attribute in the graphics node */
            g_free(xpath);
            xpath = g_strdup_printf("string(/domain/devices/graphics[@type='%s']/@socket)", type);
            unixsock = virt_viewer_extract_xpath_string(xmldesc, xpath);
        }
    }

    if (ghost && gport) {
        g_debug("Guest graphics address is %s:%s", ghost, gport);
    } else if (unixsock) {
        g_debug("Guest graphics address is %s", unixsock);
    } else {
        g_debug("Using direct libvirt connection");
        retval = TRUE;
        goto cleanup;
    }

    uri = virConnectGetURI(priv->conn);
    if (virt_viewer_util_extract_host(uri, NULL, &host, &transport, &user, &port) < 0) {
        g_set_error(error,
                    VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Cannot determine the host for the guest %s"), priv->domkey);

        goto cleanup;
    }

    /* If the XML listen attribute shows a wildcard address, we need to
     * throw that away since you obviously can't 'connect(2)' to that
     * from a remote host. Instead we fallback to the hostname used in
     * the libvirt URI. This isn't perfect but it is better than nothing.
     * If the transport is SSH, fallback to localhost as the connection
     * will be made from the remote end of the ssh connection.
     */
    if (virt_viewer_replace_host(ghost)) {
        gchar *replacement_host = NULL;
        if ((g_strcmp0(transport, "ssh") == 0) && !direct) {
            replacement_host = g_strdup("localhost");
        } else {
            replacement_host = g_strdup(host);
        }
        g_debug("Guest graphics listen '%s' is NULL or a wildcard, replacing with '%s'",
                  ghost ? ghost : "", replacement_host);
        g_free(ghost);
        ghost = replacement_host;
    }

    if (!virt_viewer_is_reachable(ghost, transport, host, direct)) {
        g_set_error(error,
                    VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Guest '%s' is not reachable"), priv->domkey);

        g_debug("graphics listen '%s' is not reachable from this machine",
                ghost ? ghost : "");

        goto cleanup;
    }

    virt_viewer_app_set_connect_info(app, host, ghost, gport, gtlsport,transport, unixsock, user, port, NULL);

    retval = TRUE;

 cleanup:
    g_free(gport);
    g_free(gtlsport);
    g_free(ghost);
    g_free(unixsock);
    g_free(host);
    g_free(transport);
    g_free(user);
    g_free(type);
    g_free(xpath);
    g_free(xmldesc);
    g_free(uri);
    return retval;
}

static gboolean
virt_viewer_update_display(VirtViewer *self, virDomainPtr dom, GError **error)
{
    VirtViewerPrivate *priv = self->priv;
    VirtViewerApp *app = VIRT_VIEWER_APP(self);

    if (priv->dom)
        virDomainFree(priv->dom);
    priv->dom = dom;
    virDomainRef(priv->dom);

    virt_viewer_app_trace(app, "Guest %s is running, determining display",
                          priv->domkey);

    if (virt_viewer_app_has_session(app))
        return TRUE;

    return virt_viewer_extract_connect_info(self, dom, error);
}

static gboolean
virt_viewer_open_connection(VirtViewerApp *self G_GNUC_UNUSED, int *fd)
{
    VirtViewer *viewer = VIRT_VIEWER(self);
    VirtViewerPrivate *priv = viewer->priv;
#if defined(HAVE_SOCKETPAIR) || defined(HAVE_VIR_DOMAIN_OPEN_GRAPHICS_FD)
    virErrorPtr err;
#endif
#if defined(HAVE_SOCKETPAIR)
    int pair[2];
#endif
    *fd = -1;

    if (!priv->dom)
        return TRUE;

#ifdef HAVE_VIR_DOMAIN_OPEN_GRAPHICS_FD
    if ((*fd = virDomainOpenGraphicsFD(priv->dom, 0,
                                       VIR_DOMAIN_OPEN_GRAPHICS_SKIPAUTH)) >= 0)
        return TRUE;

    err = virGetLastError();
    if (err && err->code != VIR_ERR_NO_SUPPORT) {
        g_debug("Error %s", err->message ? err->message : "Unknown");
        return TRUE;
    }
#endif

#if defined(HAVE_SOCKETPAIR)
    if (socketpair(PF_UNIX, SOCK_STREAM, 0, pair) < 0)
        return FALSE;

    if (virDomainOpenGraphics(priv->dom, 0, pair[0],
                              VIR_DOMAIN_OPEN_GRAPHICS_SKIPAUTH) < 0) {
        err = virGetLastError();
        g_debug("Error %s", err && err->message ? err->message : "Unknown");
        close(pair[0]);
        close(pair[1]);
        return TRUE;
    }
    close(pair[0]);
    *fd = pair[1];
#endif
    return TRUE;
}

static int
virt_viewer_domain_event(virConnectPtr conn G_GNUC_UNUSED,
                         virDomainPtr dom,
                         int event,
                         int detail G_GNUC_UNUSED,
                         void *opaque)
{
    VirtViewer *self = opaque;
    VirtViewerApp *app = VIRT_VIEWER_APP(self);
    VirtViewerSession *session;
    GError *error = NULL;

    g_debug("Got domain event %d %d", event, detail);

    if (!virt_viewer_matches_domain(self, dom))
        return 0;

    switch (event) {
    case VIR_DOMAIN_EVENT_STOPPED:
        session = virt_viewer_app_get_session(app);
#ifdef HAVE_SPICE_GTK
        /* do not disconnect due to migration */
        if (detail == VIR_DOMAIN_EVENT_STOPPED_MIGRATED &&
            VIRT_VIEWER_IS_SESSION_SPICE(session)) {
            break;
        }
#endif
        if (session != NULL)
            virt_viewer_session_close(session);
        break;

    case VIR_DOMAIN_EVENT_STARTED:
        virt_viewer_update_display(self, dom, &error);
        if (error) {
            virt_viewer_app_simple_message_dialog(app, error->message);
            g_clear_error(&error);
        }

        virt_viewer_app_activate(app, &error);
        if (error) {
            /* we may want to consolidate error reporting in
               app_activate() instead */
            g_warning("%s", error->message);
            g_clear_error(&error);
        }
        break;
    }

    return 0;
}

static void
virt_viewer_conn_event(virConnectPtr conn G_GNUC_UNUSED,
                       int reason,
                       void *opaque)
{
    VirtViewer *self = opaque;
    VirtViewerPrivate *priv = self->priv;

    g_debug("Got connection event %d", reason);

    virConnectClose(priv->conn);
    priv->conn = NULL;

    virt_viewer_start_reconnect_poll(self);
}

static void
virt_viewer_dispose (GObject *object)
{
    VirtViewer *self = VIRT_VIEWER(object);
    VirtViewerPrivate *priv = self->priv;

    if (priv->conn) {
        if (priv->domain_event >= 0) {
            virConnectDomainEventDeregisterAny(priv->conn,
                                               priv->domain_event);
            priv->domain_event = -1;
        }
        virConnectUnregisterCloseCallback(priv->conn,
                                          virt_viewer_conn_event);
        virConnectClose(priv->conn);
        priv->conn = NULL;
    }
    if (priv->dom) {
        virDomainFree(priv->dom);
        priv->dom = NULL;
    }
    g_free(priv->uri);
    priv->uri = NULL;
    g_free(priv->domkey);
    priv->domkey = NULL;
    G_OBJECT_CLASS(virt_viewer_parent_class)->dispose (object);
}

static virDomainPtr
choose_vm(GtkWindow *main_window,
          char **vm_name,
          virConnectPtr conn,
          GError **error)
{
    GtkListStore *model;
    GtkTreeIter iter;
    virDomainPtr *domains, dom = NULL;
    int i, vms_running;
    unsigned int flags = VIR_CONNECT_LIST_DOMAINS_RUNNING;

    g_return_val_if_fail(vm_name != NULL, NULL);
    free(*vm_name);

    model = gtk_list_store_new(1, G_TYPE_STRING);

    vms_running = virConnectListAllDomains(conn, &domains, flags);
    for (i = 0; i < vms_running; i++) {
        gtk_list_store_append(model, &iter);
        gtk_list_store_set(model, &iter, 0, virDomainGetName(domains[i]), -1);
        virDomainFree(domains[i]);
    }
    free(domains);

    *vm_name = virt_viewer_vm_connection_choose_name_dialog(main_window,
                                                            GTK_TREE_MODEL(model),
                                                            error);
    g_object_unref(G_OBJECT(model));
    if (*vm_name == NULL)
        return NULL;

    dom = virDomainLookupByName(conn, *vm_name);
    if (dom == NULL) {
        virErrorPtr err = virGetLastError();
        g_set_error_literal(error,
                            VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                            err && err->message ? err->message : "unknown libvirt error");
    } else if (virDomainGetState(dom, &i, NULL, 0) < 0 || i != VIR_DOMAIN_RUNNING) {
        g_set_error(error,
                    VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                    _("Virtual machine %s is not running"), *vm_name);
        virDomainFree(dom);
        dom = NULL;
    }

    return dom;
}

static gboolean
virt_viewer_initial_connect(VirtViewerApp *app, GError **error)
{
    virDomainPtr dom = NULL;
    virDomainInfo info;
    gboolean ret = FALSE;
    VirtViewer *self = VIRT_VIEWER(app);
    VirtViewerPrivate *priv = self->priv;
    char uuid_string[VIR_UUID_STRING_BUFLEN];
    const char *guest_name;
    GError *err = NULL;

    g_debug("initial connect");

    if (!priv->conn &&
        virt_viewer_connect(app, &err) < 0) {
        virt_viewer_app_show_status(app, _("Waiting for libvirt to start"));
        goto wait;
    }

    virt_viewer_app_show_status(app, _("Finding guest domain"));
    dom = virt_viewer_lookup_domain(self);
    if (!dom) {
        if (priv->waitvm) {
            virt_viewer_app_show_status(app, _("Waiting for guest domain to be created"));
            goto wait;
        } else {
            VirtViewerWindow *main_window = virt_viewer_app_get_main_window(app);
            if (priv->domkey != NULL)
                g_debug("Cannot find guest %s", priv->domkey);
            dom = choose_vm(virt_viewer_window_get_window(main_window),
                            &priv->domkey,
                            priv->conn,
                            &err);
            if (dom == NULL) {
                goto cleanup;
            }
        }
    }

    if (virDomainGetUUIDString(dom, uuid_string) < 0) {
        g_debug("Couldn't get uuid from libvirt");
    } else {
        g_object_set(app, "uuid", uuid_string, NULL);
    }
    guest_name = virDomainGetName(dom);
    if (guest_name != NULL) {
        g_object_set(app, "guest-name", guest_name, NULL);
    }

    virt_viewer_app_show_status(app, _("Checking guest domain status"));
    if (virDomainGetInfo(dom, &info) < 0) {
        g_set_error_literal(&err, VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                            _("Cannot get guest state"));
        g_debug("%s", err->message);
        goto cleanup;
    }

    if (info.state == VIR_DOMAIN_SHUTOFF) {
        virt_viewer_app_show_status(app, _("Waiting for guest domain to start"));
        goto wait;
    }

    if (!virt_viewer_update_display(self, dom, &err))
        goto cleanup;

    ret = VIRT_VIEWER_APP_CLASS(virt_viewer_parent_class)->initial_connect(app, &err);
    if (ret || err)
        goto cleanup;

wait:
    virt_viewer_app_trace(app, "Guest %s has not activated its display yet, waiting "
                          "for it to start", priv->domkey);
    ret = TRUE;

cleanup:
    if (err != NULL)
        g_propagate_error(error, err);
    if (dom)
        virDomainFree(dom);
    return ret;
}

static void
virt_viewer_error_func (void *data G_GNUC_UNUSED,
                        virErrorPtr error G_GNUC_UNUSED)
{
    /* nothing */
}



static int
virt_viewer_auth_libvirt_credentials(virConnectCredentialPtr cred,
                                     unsigned int ncred,
                                     void *cbdata)
{
    char **username = NULL, **password = NULL;
    VirtViewer *app = cbdata;
    VirtViewerPrivate *priv = app->priv;
    int i;
    int ret = 0;

    g_debug("Got libvirt credential request for %d credential(s)", ncred);

    for (i = 0 ; i < ncred ; i++) {
        switch (cred[i].type) {
        case VIR_CRED_USERNAME:
        case VIR_CRED_AUTHNAME:
            username = &cred[i].result;
            break;
        case VIR_CRED_PASSPHRASE:
            password = &cred[i].result;
            break;
        default:
            g_debug("Unsupported libvirt credential %d", cred[i].type);
            return -1;
        }
    }

    if (username || password) {
        VirtViewerWindow *vwin = virt_viewer_app_get_main_window(VIRT_VIEWER_APP(app));
        GtkWindow *win = virt_viewer_window_get_window(vwin);

        if (username && (*username == NULL || **username == '\0'))
            *username = g_strdup(g_get_user_name());

        priv->auth_cancelled = !virt_viewer_auth_collect_credentials(win,
                                                                     "libvirt",
                                                                     app->priv->uri,
                                                                     username, password);
        if (priv->auth_cancelled) {
            ret = -1;
            goto cleanup;
        }
    }

    for (i = 0 ; i < ncred ; i++) {
        const char *cred_type_to_str[] = {
            [VIR_CRED_USERNAME] = "Identity to act as",
            [VIR_CRED_AUTHNAME] = "Identify to authorize as",
            [VIR_CRED_PASSPHRASE] = "Passphrase secret",
        };
        switch (cred[i].type) {
        case VIR_CRED_AUTHNAME:
        case VIR_CRED_USERNAME:
        case VIR_CRED_PASSPHRASE:
            if (cred[i].result)
                cred[i].resultlen = strlen(cred[i].result);
            else
                cred[i].resultlen = 0;
            g_debug("Got %s '%s' %d",
                    cred_type_to_str[cred[i].type],
                    /* hide password */
                    (cred[i].type == VIR_CRED_PASSPHRASE) ? "*****" : cred[i].result,
                    cred[i].type);
            break;
        }
    }

 cleanup:
    g_debug("Return %d", ret);
    return ret;
}

static gchar *
virt_viewer_get_error_message_from_vir_error(VirtViewer *self,
                                             virErrorPtr error)
{
    VirtViewerPrivate *priv = self->priv;
    const gchar *error_details = NULL;
    gchar *detailed_error_message = NULL;
    gchar *error_message = g_strdup_printf(_("Unable to connect to libvirt with URI: %s."),
                                           priv->uri ? priv->uri : _("[none]"));

    g_debug("Error: %s", error->message);

    /* For now we are only treating authentication errors. */
    switch (error->code) {
        case VIR_ERR_AUTH_FAILED:
            error_details = _("Authentication failed.");
            break;
        default:
            break;
    }

    if (error_details != NULL) {
        detailed_error_message = g_strdup_printf("%s\n%s", error_message, error_details);
        g_free(error_message);
        return detailed_error_message;
    }

    return error_message;
}

static int
virt_viewer_connect(VirtViewerApp *app, GError **err)
{
    VirtViewer *self = VIRT_VIEWER(app);
    VirtViewerPrivate *priv = self->priv;
    int cred_types[] =
        { VIR_CRED_AUTHNAME, VIR_CRED_PASSPHRASE };
    virConnectAuth auth_libvirt = {
        .credtype = cred_types,
        .ncredtype = G_N_ELEMENTS(cred_types),
        .cb = virt_viewer_auth_libvirt_credentials,
        .cbdata = app,
    };
    int oflags = 0;
    GError *error = NULL;

    if (!virt_viewer_app_get_attach(app))
        oflags |= VIR_CONNECT_RO;

    g_debug("connecting ...");

    virt_viewer_app_trace(app, "Opening connection to libvirt with URI %s",
                          priv->uri ? priv->uri : "<null>");
    priv->conn = virConnectOpenAuth(priv->uri,
                                    //virConnectAuthPtrDefault,
                                    &auth_libvirt,
                                    oflags);
    if (!priv->conn) {
        if (!priv->auth_cancelled) {
            gchar *error_message = virt_viewer_get_error_message_from_vir_error(self, virGetLastError());
            g_set_error_literal(&error,
                                VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_FAILED,
                                error_message);

            g_free(error_message);
        } else {
            g_set_error_literal(&error,
                                VIRT_VIEWER_ERROR, VIRT_VIEWER_ERROR_CANCELLED,
                                _("Authentication was cancelled"));
        }
        g_propagate_error(err, error);
        return -1;
    }

    if (!virt_viewer_app_initial_connect(app, &error)) {
        g_propagate_prefixed_error(err, error, _("Failed to connect: "));
        return -1;
    }

    priv->domain_event = virConnectDomainEventRegisterAny(priv->conn,
                                                          priv->dom,
                                                          VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                                                          VIR_DOMAIN_EVENT_CALLBACK(virt_viewer_domain_event),
                                                          self,
                                                          NULL);
    if (priv->domain_event < 0 &&
        !virt_viewer_app_is_active(app)) {
        g_debug("No domain events, falling back to polling");
        virt_viewer_start_reconnect_poll(self);
    } else {
        /* we may be polling if we lost the libvirt connection and are trying
         * to reconnect */
        virt_viewer_stop_reconnect_poll(self);
    }

    if (virConnectRegisterCloseCallback(priv->conn,
                                        virt_viewer_conn_event,
                                        self,
                                        NULL) < 0) {
        g_debug("Unable to register close callback on libvirt connection");
    }

    if (virConnectSetKeepAlive(priv->conn, 5, 3) < 0) {
        g_debug("Unable to set keep alive");
    }

    return 0;
}

static gboolean
virt_viewer_start(VirtViewerApp *app, GError **error)
{
    gvir_event_register();

    virSetErrorFunc(NULL, virt_viewer_error_func);

    if (virt_viewer_connect(app, error) < 0)
        return FALSE;

    return VIRT_VIEWER_APP_CLASS(virt_viewer_parent_class)->start(app, error, AUTH_DIALOG);
}

VirtViewer *
virt_viewer_new(void)
{
    return g_object_new(VIRT_VIEWER_TYPE,
                        "application-id", "org.virt-manager.virt-viewer",
                        "flags", G_APPLICATION_NON_UNIQUE,
                        NULL);
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
