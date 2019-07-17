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
#include <glib/gprintf.h>
#include <glib/gi18n.h>
#include <math.h>

#include "virt-viewer-window.h"
#include "virt-viewer-display.h"
#include "virt-viewer-session.h"
#include "virt-viewer-app.h"
#include "virt-viewer-util.h"
#include "virt-viewer-timed-revealer.h"
#include "remote-viewer.h"

#include "vdi_api_session.h"

//#include "remote-viewer-iso-list-dialog.h"

#define ZOOM_STEP 10

// externs
extern gboolean opt_manual_mode;
extern gboolean take_extern_credentials;

/* Signal handlers for main window (move in a VirtViewerMainWindow?) */
void virt_viewer_window_menu_view_zoom_out(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_view_zoom_in(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_view_zoom_reset(GtkWidget *menu, VirtViewerWindow *self);
gboolean virt_viewer_window_delete(GtkWidget *src, void *dummy, VirtViewerWindow *self);
void virt_viewer_window_menu_file_quit(GtkWidget *src, VirtViewerWindow *self);
void virt_viewer_window_guest_details_response(GtkDialog *dialog, gint response_id, gpointer user_data);
void virt_viewer_window_menu_help_about(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_help_guest_details(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_view_fullscreen(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_send(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_file_screenshot(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_file_usb_device_selection(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_file_smartcard_insert(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_file_smartcard_remove(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_view_release_cursor(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_preferences_cb(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_change_cd_activate(GtkWidget *menu, VirtViewerWindow *self);
// vm control
void virt_viewer_window_menu_switch_off(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_start_vm(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_suspend_vm(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_shutdown_vm(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_shutdown_vm_force(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_reboot_vm(GtkWidget *menu, VirtViewerWindow *self);
void virt_viewer_window_menu_reboot_vm_force(GtkWidget *menu, VirtViewerWindow *self);

/* Internal methods */
static void virt_viewer_window_enable_modifiers(VirtViewerWindow *self);
static void virt_viewer_window_disable_modifiers(VirtViewerWindow *self);
static void virt_viewer_window_queue_resize(VirtViewerWindow *self);
static void virt_viewer_window_toolbar_setup(VirtViewerWindow *self);
static GtkMenu* virt_viewer_window_get_keycombo_menu(VirtViewerWindow *self);
static void virt_viewer_window_get_minimal_dimensions(VirtViewerWindow *self, guint *width, guint *height);
static gint virt_viewer_window_get_minimal_zoom_level(VirtViewerWindow *self);

G_DEFINE_TYPE (VirtViewerWindow, virt_viewer_window, G_TYPE_OBJECT)

#define GET_PRIVATE(o)                                                  \
    (G_TYPE_INSTANCE_GET_PRIVATE ((o), VIRT_VIEWER_TYPE_WINDOW, VirtViewerWindowPrivate))

enum {
    PROP_0,
    PROP_WINDOW,
    PROP_DISPLAY,
    PROP_SUBTITLE,
    PROP_APP,
};

struct _VirtViewerWindowPrivate {
    VirtViewerApp *app;

    GtkBuilder *builder;
    GtkWidget *window;
    GtkWidget *toolbar;
    GtkWidget *toolbar_usb_device_selection;
    GtkWidget *toolbar_send_key;
    GtkAccelGroup *accel_group;
    VirtViewerNotebook *notebook;
    VirtViewerDisplay *display;
    VirtViewerTimedRevealer *revealer;

    gboolean accel_enabled;
    GValue accel_setting;
    GSList *accel_list;
    gboolean enable_mnemonics_save;
    gboolean grabbed;
    gint fullscreen_monitor;
    gboolean desktop_resize_pending;
    gboolean kiosk;

    gint zoomlevel;
    gboolean fullscreen;
    gchar *subtitle;
    gboolean initial_zoom_set;
};

static void
virt_viewer_window_get_property (GObject *object, guint property_id,
                                 GValue *value, GParamSpec *pspec)
{
    VirtViewerWindow *self = VIRT_VIEWER_WINDOW(object);
    VirtViewerWindowPrivate *priv = self->priv;

    switch (property_id) {
    case PROP_SUBTITLE:
        g_value_set_string(value, priv->subtitle);
        break;

    case PROP_WINDOW:
        g_value_set_object(value, priv->window);
        break;

    case PROP_DISPLAY:
        g_value_set_object(value, virt_viewer_window_get_display(self));
        break;

    case PROP_APP:
        g_value_set_object(value, priv->app);
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
    }
}

static void
virt_viewer_window_set_property (GObject *object, guint property_id,
                                 const GValue *value, GParamSpec *pspec)
{
    VirtViewerWindowPrivate *priv = VIRT_VIEWER_WINDOW(object)->priv;

    switch (property_id) {
    case PROP_SUBTITLE:
        g_free(priv->subtitle);
        priv->subtitle = g_value_dup_string(value);
        virt_viewer_window_update_title(VIRT_VIEWER_WINDOW(object));
        break;

    case PROP_APP:
        g_return_if_fail(priv->app == NULL);
        priv->app = g_value_get_object(value);
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
    }
}

static void
virt_viewer_window_dispose (GObject *object)
{
    VirtViewerWindowPrivate *priv = VIRT_VIEWER_WINDOW(object)->priv;
    GSList *it;

    if (priv->display) {
        g_object_unref(priv->display);
        priv->display = NULL;
    }

    g_debug("Disposing window %p\n", object);

    if (priv->window) {
        gtk_widget_destroy(priv->window);
        priv->window = NULL;
    }
    if (priv->builder) {
        g_object_unref(priv->builder);
        priv->builder = NULL;
    }

    priv->revealer = NULL;

    for (it = priv->accel_list ; it != NULL ; it = it->next) {
        g_object_unref(G_OBJECT(it->data));
    }
    g_slist_free(priv->accel_list);
    priv->accel_list = NULL;

    g_free(priv->subtitle);
    priv->subtitle = NULL;

    g_value_unset(&priv->accel_setting);
    priv->toolbar = NULL;

    G_OBJECT_CLASS (virt_viewer_window_parent_class)->dispose (object);
}

static void
rebuild_combo_menu(GObject    *gobject G_GNUC_UNUSED,
                   GParamSpec *pspec G_GNUC_UNUSED,
                   gpointer    user_data)
{
    VirtViewerWindow *self = user_data;
    GtkWidget *menu;

    menu = GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-send"));
    gtk_menu_item_set_submenu(GTK_MENU_ITEM(menu),
                              GTK_WIDGET(virt_viewer_window_get_keycombo_menu(self)));
    gtk_widget_set_sensitive(menu, (self->priv->display != NULL));
}

static void
virt_viewer_window_constructed(GObject *object)
{
    VirtViewerWindowPrivate *priv = VIRT_VIEWER_WINDOW(object)->priv;

    if (G_OBJECT_CLASS(virt_viewer_window_parent_class)->constructed)
        G_OBJECT_CLASS(virt_viewer_window_parent_class)->constructed(object);

    g_signal_connect(priv->app, "notify::enable-accel",
                     G_CALLBACK(rebuild_combo_menu), object);
    rebuild_combo_menu(NULL, NULL, object);
}

static void
virt_viewer_window_class_init (VirtViewerWindowClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);

    g_type_class_add_private (klass, sizeof (VirtViewerWindowPrivate));

    object_class->get_property = virt_viewer_window_get_property;
    object_class->set_property = virt_viewer_window_set_property;
    object_class->dispose = virt_viewer_window_dispose;
    object_class->constructed = virt_viewer_window_constructed;

    g_object_class_install_property(object_class,
                                    PROP_SUBTITLE,
                                    g_param_spec_string("subtitle",
                                                        "Subtitle",
                                                        "Window subtitle",
                                                        "",
                                                        G_PARAM_READABLE |
                                                        G_PARAM_WRITABLE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_WINDOW,
                                    g_param_spec_object("window",
                                                        "Window",
                                                        "GtkWindow",
                                                        GTK_TYPE_WIDGET,
                                                        G_PARAM_READABLE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_DISPLAY,
                                    g_param_spec_object("display",
                                                        "Display",
                                                        "VirtDisplay",
                                                        VIRT_VIEWER_TYPE_DISPLAY,
                                                        G_PARAM_READABLE |
                                                        G_PARAM_STATIC_STRINGS));

    g_object_class_install_property(object_class,
                                    PROP_APP,
                                    g_param_spec_object("app",
                                                        "App",
                                                        "VirtViewerApp",
                                                        VIRT_VIEWER_TYPE_APP,
                                                        G_PARAM_READABLE |
                                                        G_PARAM_WRITABLE |
                                                        G_PARAM_CONSTRUCT_ONLY |
                                                        G_PARAM_STATIC_STRINGS));
}

static gboolean
can_activate_cb (GtkWidget *widget G_GNUC_UNUSED,
                 guint signal_id G_GNUC_UNUSED,
                 VirtViewerWindow *self G_GNUC_UNUSED)
{
    return TRUE;
}

static void
virt_viewer_window_init (VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv;
    GtkWidget *vbox;
    GSList *accels;

    self->priv = GET_PRIVATE(self);
    priv = self->priv;

    priv->fullscreen_monitor = -1;
    g_value_init(&priv->accel_setting, G_TYPE_STRING);

    priv->notebook = virt_viewer_notebook_new();
    gtk_widget_show(GTK_WIDGET(priv->notebook));

    priv->builder = virt_viewer_util_load_ui("virt-viewer_veil.ui");

    gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-send")), FALSE);
    gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-view-zoom")), FALSE);
    gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-file-screenshot")), FALSE);
    gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-preferences")), FALSE);

    gtk_builder_connect_signals(priv->builder, self);

    priv->accel_group = GTK_ACCEL_GROUP(gtk_builder_get_object(priv->builder, "accelgroup"));

    /* make sure they can be activated even if the menu item is not visible */
    g_signal_connect(gtk_builder_get_object(priv->builder, "menu-view-fullscreen"),
                     "can-activate-accel", G_CALLBACK(can_activate_cb), self);
    g_signal_connect(gtk_builder_get_object(priv->builder, "menu-file-smartcard-insert"),
                     "can-activate-accel", G_CALLBACK(can_activate_cb), self);
    g_signal_connect(gtk_builder_get_object(priv->builder, "menu-file-smartcard-remove"),
                     "can-activate-accel", G_CALLBACK(can_activate_cb), self);
    g_signal_connect(gtk_builder_get_object(priv->builder, "menu-view-release-cursor"),
                     "can-activate-accel", G_CALLBACK(can_activate_cb), self);
    g_signal_connect(gtk_builder_get_object(priv->builder, "menu-view-zoom-reset"),
                     "can-activate-accel", G_CALLBACK(can_activate_cb), self);
    g_signal_connect(gtk_builder_get_object(priv->builder, "menu-view-zoom-in"),
                     "can-activate-accel", G_CALLBACK(can_activate_cb), self);
    g_signal_connect(gtk_builder_get_object(priv->builder, "menu-view-zoom-out"),
                     "can-activate-accel", G_CALLBACK(can_activate_cb), self);

    vbox = GTK_WIDGET(gtk_builder_get_object(priv->builder, "viewer-box"));
    virt_viewer_window_toolbar_setup(self);

    gtk_box_pack_end(GTK_BOX(vbox), GTK_WIDGET(priv->notebook), TRUE, TRUE, 0);

    priv->window = GTK_WIDGET(gtk_builder_get_object(priv->builder, "viewer"));
    gtk_window_add_accel_group(GTK_WINDOW(priv->window), priv->accel_group);

    virt_viewer_window_update_title(self);
    gtk_window_set_resizable(GTK_WINDOW(priv->window), TRUE);
    gtk_window_set_has_resize_grip(GTK_WINDOW(priv->window), FALSE);
    priv->accel_enabled = TRUE;

    accels = gtk_accel_groups_from_object(G_OBJECT(priv->window));
    for ( ; accels ; accels = accels->next) {
        priv->accel_list = g_slist_append(priv->accel_list, accels->data);
        g_object_ref(G_OBJECT(accels->data));
    }

    priv->zoomlevel = NORMAL_ZOOM_LEVEL;
}

static void
virt_viewer_window_desktop_resize(VirtViewerDisplay *display G_GNUC_UNUSED,
                                  VirtViewerWindow *self)
{
    if (!gtk_widget_get_visible(self->priv->window)) {
        self->priv->desktop_resize_pending = TRUE;
        return;
    }
    virt_viewer_window_queue_resize(self);
}

static gint
virt_viewer_window_get_real_zoom_level(VirtViewerWindow *self)
{
    GtkAllocation allocation;
    guint width, height;

    g_return_val_if_fail(self->priv->display != NULL, NORMAL_ZOOM_LEVEL);

    gtk_widget_get_allocation(GTK_WIDGET(self->priv->display), &allocation);
    virt_viewer_display_get_desktop_size(self->priv->display, &width, &height);

    return round((double) NORMAL_ZOOM_LEVEL * allocation.width / width);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_view_zoom_out(GtkWidget *menu G_GNUC_UNUSED,
                                      VirtViewerWindow *self)
{
    virt_viewer_window_set_zoom_level(self,
                                      virt_viewer_window_get_real_zoom_level(self) - ZOOM_STEP);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_view_zoom_in(GtkWidget *menu G_GNUC_UNUSED,
                                     VirtViewerWindow *self)
{
    virt_viewer_window_set_zoom_level(self,
                                      virt_viewer_window_get_real_zoom_level(self) + ZOOM_STEP);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_view_zoom_reset(GtkWidget *menu G_GNUC_UNUSED,
                                        VirtViewerWindow *self)
{
    virt_viewer_window_set_zoom_level(self, NORMAL_ZOOM_LEVEL);
}

/* Kick GtkWindow to tell it to adjust to our new widget sizes */
static void
virt_viewer_window_queue_resize(VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv = self->priv;
    GtkRequisition nat;
    GtkWidget *child;
    guint border;

    border = gtk_container_get_border_width(GTK_CONTAINER(priv->window));
    child = gtk_bin_get_child(GTK_BIN(priv->window));
    gtk_window_set_default_size(GTK_WINDOW(priv->window), -1, -1);
    gtk_widget_get_preferred_size(child, NULL, &nat);
    gtk_window_resize(GTK_WINDOW(priv->window), nat.width + border, nat.height + border);
}

static void
virt_viewer_window_move_to_monitor(VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv = self->priv;
    GdkRectangle mon;
    gint n = priv->fullscreen_monitor;

    if (n == -1)
        return;

    gdk_screen_get_monitor_geometry(gdk_screen_get_default(), n, &mon);
    gtk_window_move(GTK_WINDOW(priv->window), mon.x, mon.y);

    gtk_widget_set_size_request(priv->window,
                                mon.width,
                                mon.height);
}

static gboolean
mapped(GtkWidget *widget, GdkEvent *event G_GNUC_UNUSED,
       VirtViewerWindow *self)
{
    g_signal_handlers_disconnect_by_func(widget, mapped, self);
    self->priv->fullscreen = FALSE;
    virt_viewer_window_enter_fullscreen(self, self->priv->fullscreen_monitor);
    return FALSE;
}

static void
virt_viewer_window_menu_fullscreen_set_active(VirtViewerWindow *self, gboolean active)
{
    GtkCheckMenuItem *check = GTK_CHECK_MENU_ITEM(gtk_builder_get_object(self->priv->builder, "menu-view-fullscreen"));

    g_signal_handlers_block_by_func(check, virt_viewer_window_menu_view_fullscreen, self);
    gtk_check_menu_item_set_active(check, active);
    g_signal_handlers_unblock_by_func(check, virt_viewer_window_menu_view_fullscreen, self);
}

void
virt_viewer_window_leave_fullscreen(VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv = self->priv;
    GtkWidget *menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "top-menu"));

    /* if we enter and leave fullscreen mode before being shown, make sure to
     * disconnect the mapped signal handler */
    g_signal_handlers_disconnect_by_func(priv->window, mapped, self);

    if (!priv->fullscreen)
        return;

    virt_viewer_window_menu_fullscreen_set_active(self, FALSE);
    priv->fullscreen = FALSE;
    priv->fullscreen_monitor = -1;
    if (priv->display) {
        virt_viewer_display_set_monitor(priv->display, -1);
        virt_viewer_display_set_fullscreen(priv->display, FALSE);
    }
    virt_viewer_timed_revealer_force_reveal(priv->revealer, FALSE);
    gtk_widget_show(menu);
    gtk_widget_hide(priv->toolbar);
    gtk_widget_set_size_request(priv->window, -1, -1);
    gtk_window_unfullscreen(GTK_WINDOW(priv->window));

}

void
virt_viewer_window_enter_fullscreen(VirtViewerWindow *self, gint monitor)
{
    VirtViewerWindowPrivate *priv = self->priv;
    GtkWidget *menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "top-menu"));

    if (priv->fullscreen && priv->fullscreen_monitor != monitor)
        virt_viewer_window_leave_fullscreen(self);

    if (priv->fullscreen)
        return;

    priv->fullscreen_monitor = monitor;
    priv->fullscreen = TRUE;

    if (!gtk_widget_get_mapped(priv->window)) {
        /*
         * To avoid some races with metacity, the window should be placed
         * as early as possible, before it is (re)allocated & mapped
         * Position & size should not be queried yet. (rhbz#809546).
         */
        virt_viewer_window_move_to_monitor(self);
        g_signal_connect(priv->window, "map-event", G_CALLBACK(mapped), self);
        return;
    }

    virt_viewer_window_menu_fullscreen_set_active(self, TRUE);
    gtk_widget_hide(menu);

    if (!priv->kiosk) {
        gtk_widget_show(priv->toolbar);
        virt_viewer_timed_revealer_force_reveal(priv->revealer, TRUE);
    }

    if (priv->display) {
        virt_viewer_display_set_monitor(priv->display, monitor);
        virt_viewer_display_set_fullscreen(priv->display, TRUE);
    }
    virt_viewer_window_move_to_monitor(self);

    gtk_window_fullscreen(GTK_WINDOW(priv->window));
}

#define MAX_KEY_COMBO 4
struct keyComboDef {
    guint keys[MAX_KEY_COMBO];
    const char *label;
    const gchar* accel_path;
};

static const struct keyComboDef keyCombos[] = {
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_Delete, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+_Del"), "<virt-viewer>/send/secure-attention"},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_BackSpace, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+_Backspace"), NULL},
    { { GDK_KEY_VoidSymbol }, "" , NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F1, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_1"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F2, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_2"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F3, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_3"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F4, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_4"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F5, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_5"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F6, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_6"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F7, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_7"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F8, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_8"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F9, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F_9"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F10, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F1_0"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F11, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F11"), NULL},
    { { GDK_KEY_Control_L, GDK_KEY_Alt_L, GDK_KEY_F12, GDK_KEY_VoidSymbol }, N_("Ctrl+Alt+F12"), NULL},
    { { GDK_KEY_VoidSymbol }, "" , NULL},
    { { GDK_KEY_Print, GDK_KEY_VoidSymbol }, "_PrintScreen", NULL},
};

static guint
get_nkeys(const guint *keys)
{
    guint i;

    for (i = 0; keys[i] != GDK_KEY_VoidSymbol; )
        i++;

    return i;
}

G_MODULE_EXPORT void
virt_viewer_window_menu_send(GtkWidget *menu,
                             VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv = self->priv;

    g_return_if_fail(priv->display != NULL);
    guint *keys = g_object_get_data(G_OBJECT(menu), "vv-keys");
    g_return_if_fail(keys != NULL);

    virt_viewer_display_send_keys(VIRT_VIEWER_DISPLAY(priv->display),
                                  keys, get_nkeys(keys));
}

static void
virt_viewer_menu_add_combo(VirtViewerWindow *self, GtkMenu *menu,
                           const guint *keys, const gchar *label, const gchar* accel_path)
{
    GtkWidget *item;

    if (keys == NULL || keys[0] == GDK_KEY_VoidSymbol) {
        item = gtk_separator_menu_item_new();
    } else {
        item = gtk_menu_item_new_with_mnemonic(label);
        if (accel_path) {
            gtk_menu_item_set_accel_path(GTK_MENU_ITEM(item), accel_path);
            /* make accel work in fullscreen */
            g_signal_connect(item, "can-activate-accel", G_CALLBACK(can_activate_cb), self);
        }
        guint *ckeys = g_memdup(keys, (get_nkeys(keys) + 1) * sizeof(guint));
        g_object_set_data_full(G_OBJECT(item), "vv-keys", ckeys, g_free);
        g_signal_connect(item, "activate", G_CALLBACK(virt_viewer_window_menu_send), self);
    }

    gtk_container_add(GTK_CONTAINER(menu), item);
}

static guint*
accel_key_to_keys(const GtkAccelKey *key)
{
    guint i;
    guint *val, *keys;
    const struct {
        const guint mask;
        const guint key;
    } modifiers[] = {
        {GDK_SHIFT_MASK, GDK_KEY_Shift_L},
        {GDK_CONTROL_MASK, GDK_KEY_Control_L},
        {GDK_MOD1_MASK, GDK_KEY_Alt_L},
    };

    g_warn_if_fail((key->accel_mods &
                    ~(GDK_SHIFT_MASK | GDK_CONTROL_MASK | GDK_MOD1_MASK)) == 0);

    keys = val = g_new(guint, 5); /* up to 3 modifiers, key and the stop symbol */
    /* first, send the modifiers */
    for (i = 0; i < G_N_ELEMENTS(modifiers); i++) {
        if (key->accel_mods & modifiers[i].mask)
            *val++ = modifiers[i].key;
    }

    /* only after, the non-modifier key (ctrl-t, not t-ctrl) */
    *val++ = key->accel_key;
    /* stop symbol */
    *val = GDK_KEY_VoidSymbol;

    return keys;
}

struct accelCbData
{
    VirtViewerWindow *self;
    GtkMenu *menu;
};

static void
accel_map_item_cb(gpointer data,
                  const gchar *accel_path,
                  guint accel_key,
                  GdkModifierType accel_mods,
                  gboolean changed G_GNUC_UNUSED)
{
    struct accelCbData *d = data;
    GtkAccelKey key = {
        .accel_key = accel_key,
        .accel_mods = accel_mods
    };

    if (!g_str_has_prefix(accel_path, "<virt-viewer>"))
        return;
    if (accel_key == GDK_KEY_VoidSymbol || accel_key == 0)
        return;

    guint *keys = accel_key_to_keys(&key);
    gchar *label = gtk_accelerator_get_label(accel_key, accel_mods);
    virt_viewer_menu_add_combo(d->self, d->menu, keys, label, NULL);
    g_free(label);
    g_free(keys);
}

static GtkMenu*
virt_viewer_window_get_keycombo_menu(VirtViewerWindow *self)
{
    gint i;
    VirtViewerWindowPrivate *priv = self->priv;
    GtkMenu *menu = GTK_MENU(gtk_menu_new());
    gtk_menu_set_accel_group(menu, priv->accel_group);

    for (i = 0 ; i < G_N_ELEMENTS(keyCombos); i++) {
        virt_viewer_menu_add_combo(self, menu, keyCombos[i].keys, keyCombos[i].label, keyCombos[i].accel_path);
    }

    if (virt_viewer_app_get_enable_accel(priv->app)) {
        struct accelCbData d = {
            .self = self,
            .menu = menu
        };

        gtk_accel_map_foreach(&d, accel_map_item_cb);
    }

    gtk_widget_show_all(GTK_WIDGET(menu));
    return menu;
}

static void
action_zoom_in(G_GNUC_UNUSED GSimpleAction *action,
               G_GNUC_UNUSED GVariant *state,
               gpointer user_data)
{
    virt_viewer_window_menu_view_zoom_in(NULL, VIRT_VIEWER_WINDOW(user_data));
}

static void
action_zoom_out(G_GNUC_UNUSED GSimpleAction *action,
                G_GNUC_UNUSED GVariant *state,
                gpointer user_data)
{
    virt_viewer_window_menu_view_zoom_out(NULL, VIRT_VIEWER_WINDOW(user_data));
}

static void
action_zoom_reset(G_GNUC_UNUSED GSimpleAction *action,
                  G_GNUC_UNUSED GVariant *state,
                  gpointer user_data)
{
    virt_viewer_window_menu_view_zoom_reset(NULL, VIRT_VIEWER_WINDOW(user_data));
}

/* Keep keypad_action_entries and keypad_action_accels in sync */
static const GActionEntry keypad_action_entries[] = {
    { .name = "zoom-in", .activate = action_zoom_in },
    { .name = "zoom-out", .activate = action_zoom_out },
    { .name = "zoom-reset", .activate = action_zoom_reset },
};

static const gchar *const keypad_action_accels[][2] = {
    /* numpad keys are not handled automatically by gtk, see bgo#699823 */
    {"<control>KP_Add", NULL},
    {"<control>KP_Subtract", NULL},
    {"<control>KP_0", NULL},
};
G_STATIC_ASSERT(G_N_ELEMENTS(keypad_action_entries) == G_N_ELEMENTS(keypad_action_accels));

void
virt_viewer_window_disable_modifiers(VirtViewerWindow *self)
{
    GtkSettings *settings = gtk_settings_get_default();
    VirtViewerWindowPrivate *priv = self->priv;
    GValue empty;
    GSList *accels;
    guint i;

    if (!priv->accel_enabled)
        return;

    /* This stops F10 activating menu bar */
    memset(&empty, 0, sizeof empty);
    g_value_init(&empty, G_TYPE_STRING);
    g_object_get_property(G_OBJECT(settings), "gtk-menu-bar-accel", &priv->accel_setting);
    g_object_set_property(G_OBJECT(settings), "gtk-menu-bar-accel", &empty);

    /* This stops global accelerators like Ctrl+Q == Quit */
    for (accels = priv->accel_list ; accels ; accels = accels->next) {
        if (virt_viewer_app_get_enable_accel(priv->app) &&
            priv->accel_group == accels->data)
            continue;
        gtk_window_remove_accel_group(GTK_WINDOW(priv->window), accels->data);
    }

    /* This stops menu bar shortcuts like Alt+F == File */
    g_object_get(settings,
                 "gtk-enable-mnemonics", &priv->enable_mnemonics_save,
                 NULL);
    g_object_set(settings,
                 "gtk-enable-mnemonics", FALSE,
                 NULL);

    for (i = 0; i < G_N_ELEMENTS(keypad_action_entries); i++) {
        g_action_map_remove_action(G_ACTION_MAP(priv->window), keypad_action_entries[i].name);
    }

    priv->accel_enabled = FALSE;
}

void
virt_viewer_window_enable_modifiers(VirtViewerWindow *self)
{
    GtkSettings *settings = gtk_settings_get_default();
    VirtViewerWindowPrivate *priv = self->priv;
    GSList *accels;
    guint i;

    if (priv->accel_enabled)
        return;

    /* This allows F10 activating menu bar */
    g_object_set_property(G_OBJECT(settings), "gtk-menu-bar-accel", &priv->accel_setting);

    /* This allows global accelerators like Ctrl+Q == Quit */
    for (accels = priv->accel_list ; accels ; accels = accels->next) {
        if (virt_viewer_app_get_enable_accel(priv->app) &&
            priv->accel_group == accels->data)
            continue;
        gtk_window_add_accel_group(GTK_WINDOW(priv->window), accels->data);
    }

    /* This allows menu bar shortcuts like Alt+F == File */
    g_object_set(settings,
                 "gtk-enable-mnemonics", priv->enable_mnemonics_save,
                 NULL);

    g_action_map_add_action_entries(G_ACTION_MAP(priv->window),
                                    keypad_action_entries, G_N_ELEMENTS(keypad_action_entries),
                                    self);
    for (i = 0; i < G_N_ELEMENTS(keypad_action_entries); i++) {
        gchar *detailed_name = g_strdup_printf("win.%s", keypad_action_entries[i].name);
        gtk_application_set_accels_for_action(GTK_APPLICATION(priv->app),
                                              detailed_name,
                                              keypad_action_accels[i]);
        g_free(detailed_name);
    }

    priv->accel_enabled = TRUE;
}


G_MODULE_EXPORT gboolean
virt_viewer_window_delete(GtkWidget *src G_GNUC_UNUSED,
                          void *dummy G_GNUC_UNUSED,
                          VirtViewerWindow *self)
{
    g_debug("Window closed");
    virt_viewer_app_maybe_quit(self->priv->app, self);
    return TRUE;
}


G_MODULE_EXPORT void
virt_viewer_window_menu_file_quit(GtkWidget *src G_GNUC_UNUSED,
                                  VirtViewerWindow *self)
{
    virt_viewer_app_maybe_quit(self->priv->app, self);
}


static void
virt_viewer_window_set_fullscreen(VirtViewerWindow *self,
                                  gboolean fullscreen)
{
    if (fullscreen) {
        virt_viewer_window_enter_fullscreen(self, -1);
    } else {
        /* leave all windows fullscreen state */
        if (virt_viewer_app_get_fullscreen(self->priv->app))
            g_object_set(self->priv->app, "fullscreen", FALSE, NULL);
        /* or just this window */
        else
            virt_viewer_window_leave_fullscreen(self);
    }
}

static void
virt_viewer_window_toolbar_leave_fullscreen(GtkWidget *button G_GNUC_UNUSED,
                                            VirtViewerWindow *self)
{
    virt_viewer_window_set_fullscreen(self, FALSE);
}

static void keycombo_menu_location(GtkMenu *menu G_GNUC_UNUSED, gint *x, gint *y,
                                   gboolean *push_in, gpointer user_data)
{
    VirtViewerWindow *self = user_data;
    GtkAllocation allocation;
    GtkWidget *toplevel = gtk_widget_get_toplevel(self->priv->toolbar_send_key);

    *push_in = TRUE;
    gdk_window_get_origin(gtk_widget_get_window(toplevel), x, y);
    gtk_widget_translate_coordinates(self->priv->toolbar_send_key, toplevel,
                                     *x, *y, x, y);
    gtk_widget_get_allocation(self->priv->toolbar_send_key, &allocation);
    *y += allocation.height;
}

static void
virt_viewer_window_toolbar_send_key(GtkWidget *button G_GNUC_UNUSED,
                                    VirtViewerWindow *self)
{
    GtkMenu *menu = virt_viewer_window_get_keycombo_menu(self);
    gtk_menu_attach_to_widget(menu, self->priv->window, NULL);
    g_object_ref_sink(menu);
    gtk_menu_popup(menu, NULL, NULL, keycombo_menu_location, self,
                   0, gtk_get_current_event_time());
    g_object_unref(menu);
}


G_MODULE_EXPORT void
virt_viewer_window_menu_view_fullscreen(GtkWidget *menu,
                                        VirtViewerWindow *self)
{
    gboolean fullscreen = gtk_check_menu_item_get_active(GTK_CHECK_MENU_ITEM(menu));

    virt_viewer_window_set_fullscreen(self, fullscreen);
}

static void add_if_writable (GdkPixbufFormat *data, GHashTable *formats)
{
    if (gdk_pixbuf_format_is_writable(data)) {
        gchar **extensions;
        gchar **it;
        extensions = gdk_pixbuf_format_get_extensions(data);
        for (it = extensions; *it != NULL; it++) {
            g_hash_table_insert(formats, g_strdup(*it), data);
        }
        g_strfreev(extensions);
    }
}

static GHashTable *init_image_formats(void)
{
    GHashTable *format_map;
    GSList *formats = gdk_pixbuf_get_formats();

    format_map = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, NULL);
    g_slist_foreach(formats, (GFunc)add_if_writable, format_map);
    g_slist_free (formats);

    return format_map;
}

static GdkPixbufFormat *get_image_format(const char *filename)
{
    static GOnce image_formats_once = G_ONCE_INIT;
    const char *ext;

    g_once(&image_formats_once, (GThreadFunc)init_image_formats, NULL);

    ext = strrchr(filename, '.');
    if (ext == NULL)
        return NULL;

    ext++; /* skip '.' */

    return g_hash_table_lookup(image_formats_once.retval, ext);
}

static gboolean
virt_viewer_window_save_screenshot(VirtViewerWindow *self,
                                   const char *file,
                                   GError **error)
{
    VirtViewerWindowPrivate *priv = self->priv;
    GdkPixbuf *pix = virt_viewer_display_get_pixbuf(VIRT_VIEWER_DISPLAY(priv->display));
    GdkPixbufFormat *format = get_image_format(file);
    gboolean result;

    if (format == NULL) {
        g_set_error(error, G_FILE_ERROR, G_FILE_ERROR_FAILED,
                    _("Unable to determine image format for file '%s'"), file);
        result = FALSE;
    } else {
        char *type = gdk_pixbuf_format_get_name(format);
        g_debug("saving to %s", type);
        result = gdk_pixbuf_save(pix, file, type, error, NULL);
        g_free(type);
    }

    g_object_unref(pix);
    return result;
}

G_MODULE_EXPORT void
virt_viewer_window_menu_file_screenshot(GtkWidget *menu G_GNUC_UNUSED,
                                        VirtViewerWindow *self)
{
    GtkWidget *dialog;
    VirtViewerWindowPrivate *priv = self->priv;
    const char *image_dir;

    g_return_if_fail(priv->display != NULL);

    dialog = gtk_file_chooser_dialog_new("Save screenshot",
                                         NULL,
                                         GTK_FILE_CHOOSER_ACTION_SAVE,
                                         _("_Cancel"), GTK_RESPONSE_CANCEL,
                                         _("_Save"), GTK_RESPONSE_ACCEPT,
                                         NULL);
    gtk_file_chooser_set_do_overwrite_confirmation(GTK_FILE_CHOOSER (dialog), TRUE);
    gtk_window_set_transient_for(GTK_WINDOW(dialog),
                                 GTK_WINDOW(self->priv->window));
    image_dir = g_get_user_special_dir(G_USER_DIRECTORY_PICTURES);
    if (image_dir != NULL)
        gtk_file_chooser_set_current_folder(GTK_FILE_CHOOSER (dialog), image_dir);
    gtk_file_chooser_set_current_name(GTK_FILE_CHOOSER (dialog), _("Screenshot.png"));

    if (gtk_dialog_run(GTK_DIALOG (dialog)) == GTK_RESPONSE_ACCEPT) {
        char *filename;
        GError *error = NULL;

        filename = gtk_file_chooser_get_filename(GTK_FILE_CHOOSER (dialog));
        if (!virt_viewer_window_save_screenshot(self, filename, &error)) {
            virt_viewer_app_simple_message_dialog(self->priv->app,
                                                  error->message);
            g_error_free(error);
        }
        g_free(filename);
    }

    gtk_widget_destroy(dialog);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_file_usb_device_selection(GtkWidget *menu G_GNUC_UNUSED,
                                                  VirtViewerWindow *self)
{
    virt_viewer_session_usb_device_selection(virt_viewer_app_get_session(self->priv->app),
                                             GTK_WINDOW(self->priv->window));
}

G_MODULE_EXPORT void
virt_viewer_window_menu_file_smartcard_insert(GtkWidget *menu G_GNUC_UNUSED,
                                              VirtViewerWindow *self)
{
    virt_viewer_session_smartcard_insert(virt_viewer_app_get_session(self->priv->app));
}

G_MODULE_EXPORT void
virt_viewer_window_menu_file_smartcard_remove(GtkWidget *menu G_GNUC_UNUSED,
                                              VirtViewerWindow *self)
{
    virt_viewer_session_smartcard_remove(virt_viewer_app_get_session(self->priv->app));
}

G_MODULE_EXPORT void
virt_viewer_window_menu_preferences_cb(GtkWidget *menu G_GNUC_UNUSED,
                                       VirtViewerWindow *self)
{
    virt_viewer_app_show_preferences(self->priv->app, self->priv->window);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_view_release_cursor(GtkWidget *menu G_GNUC_UNUSED,
                                            VirtViewerWindow *self)
{
    g_return_if_fail(self->priv->display != NULL);
    virt_viewer_display_release_cursor(VIRT_VIEWER_DISPLAY(self->priv->display));
}

G_MODULE_EXPORT void
virt_viewer_window_menu_help_guest_details(GtkWidget *menu G_GNUC_UNUSED,
                                           VirtViewerWindow *self)
{
    GError *error = NULL;
    GdkScreen *default_screen = gdk_screen_get_default ();
    gtk_show_uri (default_screen, "http://mashtab.org/files/veil/index.html", GDK_CURRENT_TIME, &error);
}

G_MODULE_EXPORT void
virt_viewer_window_guest_details_response(GtkDialog *dialog,
                                          gint response_id,
                                          gpointer user_data G_GNUC_UNUSED)
{
    if (response_id == GTK_RESPONSE_CLOSE)
        gtk_widget_hide(GTK_WIDGET(dialog));
}

G_MODULE_EXPORT void
virt_viewer_window_menu_help_about(GtkWidget *menu G_GNUC_UNUSED,
                                   VirtViewerWindow *self)
{
    GtkBuilder *about;
    GtkWidget *dialog;
    GdkPixbuf *icon;

    about = virt_viewer_util_load_ui("virt-viewer-about.ui");

    dialog = GTK_WIDGET(gtk_builder_get_object(about, "about"));
    gtk_about_dialog_set_version ((GtkAboutDialog *)dialog, VERSION);
    gtk_about_dialog_set_license ((GtkAboutDialog *)dialog, "");

    //gtk_about_dialog_set_version(GTK_ABOUT_DIALOG(dialog), VERSION BUILDID);

    icon = gdk_pixbuf_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png", NULL);
    if (icon != NULL) {
        gtk_about_dialog_set_logo(GTK_ABOUT_DIALOG(dialog), icon);
        g_object_unref(icon);
    } else {
        gtk_about_dialog_set_logo_icon_name(GTK_ABOUT_DIALOG(dialog), "virt-viewer_veil");
    }

    gtk_window_set_transient_for(GTK_WINDOW(dialog),
                                 GTK_WINDOW(self->priv->window));

    gtk_builder_connect_signals(about, self);

    gtk_widget_show_all(dialog);

    g_object_unref(G_OBJECT(about));
}

#if HAVE_OVIRT
static void
iso_dialog_response(GtkDialog *dialog,
                    gint response_id,
                    gpointer user_data G_GNUC_UNUSED)
{
    if (response_id == GTK_RESPONSE_NONE)
        return;

    gtk_widget_destroy(GTK_WIDGET(dialog));
}
#endif

G_MODULE_EXPORT void
virt_viewer_window_menu_change_cd_activate(GtkWidget *menu G_GNUC_UNUSED,
                                           VirtViewerWindow *self G_GNUC_UNUSED)
{
#if HAVE_OVIRT
    VirtViewerWindowPrivate *priv = self->priv;
    GtkWidget *dialog;
    GObject *foreign_menu;

    g_object_get(G_OBJECT(priv->app), "ovirt-foreign-menu", &foreign_menu, NULL);
    dialog = remote_viewer_iso_list_dialog_new(GTK_WINDOW(priv->window), foreign_menu);
    g_object_unref(foreign_menu);

    if (!dialog)
        dialog = gtk_message_dialog_new(GTK_WINDOW(priv->window),
                                        GTK_DIALOG_MODAL | GTK_DIALOG_DESTROY_WITH_PARENT,
                                        GTK_MESSAGE_ERROR,
                                        GTK_BUTTONS_CLOSE,
                                        _("Unable to connnect to oVirt"));

    g_signal_connect(dialog, "response", G_CALLBACK(iso_dialog_response), NULL);
    gtk_widget_show_all(dialog);
    gtk_dialog_run(GTK_DIALOG(dialog));
#endif
}

G_MODULE_EXPORT void
virt_viewer_window_menu_switch_off(GtkWidget *menu, VirtViewerWindow *self)
{
    printf("%s\n", (char *)__func__);

    virt_viewer_window_hide(self);
    virt_viewer_app_deactivate(self->priv->app, TRUE);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_start_vm(GtkWidget *menu G_GNUC_UNUSED, VirtViewerWindow *self)
{
    printf("%s\n", (char *)__func__);
    do_action_on_vm_async("start", FALSE);
    // start connect atempts
    RemoteViewer *remote_viewer = REMOTE_VIEWER(self->priv->app);
    virt_viewer_start_reconnect_poll(remote_viewer);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_suspend_vm(GtkWidget *menu G_GNUC_UNUSED, VirtViewerWindow *self G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);
    do_action_on_vm_async("suspend", FALSE);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_shutdown_vm(GtkWidget *menu G_GNUC_UNUSED, VirtViewerWindow *self G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);
    do_action_on_vm_async("shutdown", FALSE);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_shutdown_vm_force(GtkWidget *menu G_GNUC_UNUSED, VirtViewerWindow *self G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);
    do_action_on_vm_async("shutdown", TRUE);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_reboot_vm(GtkWidget *menu G_GNUC_UNUSED, VirtViewerWindow *self G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);
    do_action_on_vm_async("reboot", FALSE);
}

G_MODULE_EXPORT void
virt_viewer_window_menu_reboot_vm_force(GtkWidget *menu G_GNUC_UNUSED, VirtViewerWindow *self G_GNUC_UNUSED)
{
    printf("%s\n", (char *)__func__);
    do_action_on_vm_async("reboot", TRUE);
}

static void
virt_viewer_window_toolbar_setup(VirtViewerWindow *self)
{
    GtkWidget *button;
    GtkWidget *overlay;
    VirtViewerWindowPrivate *priv = self->priv;

    priv->toolbar = gtk_toolbar_new();
    gtk_toolbar_set_show_arrow(GTK_TOOLBAR(priv->toolbar), FALSE);
    gtk_widget_set_no_show_all(priv->toolbar, TRUE);
    gtk_toolbar_set_style(GTK_TOOLBAR(priv->toolbar), GTK_TOOLBAR_BOTH_HORIZ);

    /* Close connection */
    button = GTK_WIDGET(gtk_tool_button_new(NULL, NULL));
    gtk_tool_button_set_icon_name(GTK_TOOL_BUTTON(button), "window-close");
    gtk_tool_item_set_tooltip_text(GTK_TOOL_ITEM(button), _("Disconnect"));
    gtk_widget_show(button);
    gtk_toolbar_insert(GTK_TOOLBAR(priv->toolbar), GTK_TOOL_ITEM (button), 0);
    g_signal_connect(button, "clicked", G_CALLBACK(virt_viewer_window_menu_file_quit), self);

    /* USB Device selection */
    //button = gtk_image_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/24x24/virt-viewer-usb.png");
    button = GTK_WIDGET(gtk_tool_button_new(NULL, NULL));

    gtk_tool_button_set_label(GTK_TOOL_BUTTON(button), _("USB device selection"));
    gtk_tool_item_set_tooltip_text(GTK_TOOL_ITEM(button), _("USB device selection"));
    gtk_toolbar_insert(GTK_TOOLBAR(priv->toolbar), GTK_TOOL_ITEM(button), 0);
    g_signal_connect(button, "clicked", G_CALLBACK(virt_viewer_window_menu_file_usb_device_selection), self);
    priv->toolbar_usb_device_selection = button;

    /* Send key */
    button = GTK_WIDGET(gtk_tool_button_new(NULL, NULL));
    gtk_tool_button_set_icon_name(GTK_TOOL_BUTTON(button), "preferences-desktop-keyboard-shortcuts");
    gtk_tool_item_set_tooltip_text(GTK_TOOL_ITEM(button), _("Send key combination"));
    gtk_widget_show(button);
    gtk_toolbar_insert(GTK_TOOLBAR(priv->toolbar), GTK_TOOL_ITEM(button), 0);
    g_signal_connect(button, "clicked", G_CALLBACK(virt_viewer_window_toolbar_send_key), self);
    gtk_widget_set_sensitive(button, FALSE);
    priv->toolbar_send_key = button;

    /* Leave fullscreen */
    button = GTK_WIDGET(gtk_tool_button_new(NULL, NULL));
    gtk_tool_button_set_icon_name(GTK_TOOL_BUTTON(button), "view-restore");
    gtk_tool_button_set_label(GTK_TOOL_BUTTON(button), _("Leave fullscreen"));
    gtk_tool_item_set_tooltip_text(GTK_TOOL_ITEM(button), _("Leave fullscreen"));
    gtk_tool_item_set_is_important(GTK_TOOL_ITEM(button), TRUE);
    gtk_widget_show(button);
    gtk_toolbar_insert(GTK_TOOLBAR(priv->toolbar), GTK_TOOL_ITEM(button), 0);
    g_signal_connect(button, "clicked", G_CALLBACK(virt_viewer_window_toolbar_leave_fullscreen), self);

    priv->revealer = virt_viewer_timed_revealer_new(priv->toolbar);
    overlay = GTK_WIDGET(gtk_builder_get_object(priv->builder, "viewer-overlay"));
    gtk_overlay_add_overlay(GTK_OVERLAY(overlay), GTK_WIDGET(priv->revealer));
}

VirtViewerNotebook*
virt_viewer_window_get_notebook (VirtViewerWindow *self)
{
    return VIRT_VIEWER_NOTEBOOK(self->priv->notebook);
}

GtkWindow*
virt_viewer_window_get_window (VirtViewerWindow *self)
{
    return GTK_WINDOW(self->priv->window);
}

static void
virt_viewer_window_pointer_grab(VirtViewerDisplay *display G_GNUC_UNUSED,
                                VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv = self->priv;

    priv->grabbed = TRUE;
    virt_viewer_window_update_title(self);
}

static void
virt_viewer_window_pointer_ungrab(VirtViewerDisplay *display G_GNUC_UNUSED,
                                  VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv = self->priv;

    priv->grabbed = FALSE;
    virt_viewer_window_update_title(self);
}

static void
virt_viewer_window_keyboard_grab(VirtViewerDisplay *display G_GNUC_UNUSED,
                                 VirtViewerWindow *self)
{
    virt_viewer_window_disable_modifiers(self);
}

static void
virt_viewer_window_keyboard_ungrab(VirtViewerDisplay *display G_GNUC_UNUSED,
                                   VirtViewerWindow *self)
{
    virt_viewer_window_enable_modifiers(self);
}

void
virt_viewer_window_update_title(VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv = self->priv;
    char *title;
    gchar *ungrab = NULL;

    if (priv->grabbed) {
        gchar *label;
        GtkAccelKey key = {0, 0, 0};

        if (virt_viewer_app_get_enable_accel(priv->app))
            gtk_accel_map_lookup_entry("<virt-viewer>/view/release-cursor", &key);

        if (key.accel_key || key.accel_mods) {
            g_debug("release-cursor accel key: key=%u, mods=%x, flags=%u", key.accel_key, key.accel_mods, key.accel_flags);
            label = gtk_accelerator_get_label(key.accel_key, key.accel_mods);
        } else {
            label = g_strdup(_("Ctrl+Alt"));
        }

        ungrab = g_strdup_printf(_("(Press %s to release pointer)"), label);
        g_free(label);
    }

    if (!ungrab && !priv->subtitle)
        title = g_strdup(g_get_application_name());
    else
        /* translators:
         * This is "<ungrab (or empty)><space (or empty)><subtitle (or empty)> - <appname>"
         * Such as: "(Press Ctrl+Alt to release pointer) BigCorpTycoon MOTD - Virt Viewer"
         */
        title = g_strdup_printf(_("%s%s%s - %s"),
                                /* translators: <ungrab empty> */
                                ungrab ? ungrab : "",
                                /* translators: <space> */
                                ungrab && priv->subtitle ? _(" ") : "",
                                priv->subtitle,
                                g_get_application_name());

    gtk_window_set_title(GTK_WINDOW(priv->window), title);

    g_free(title);
    g_free(ungrab);
}

void
virt_viewer_window_set_menu_displays_sensitive(VirtViewerWindow *self, gboolean sensitive)
{
    VirtViewerWindowPrivate *priv;
    GtkWidget *menu;

    g_return_if_fail(VIRT_VIEWER_IS_WINDOW(self));

    priv = self->priv;
    menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "menu-displays"));
    gtk_widget_set_sensitive(menu, FALSE); // sensitive  // temp
}

void
virt_viewer_window_set_usb_options_sensitive(VirtViewerWindow *self, gboolean sensitive)
{
    VirtViewerWindowPrivate *priv;
    //GtkWidget *main_menu;
    GtkWidget *menu;

    g_return_if_fail(VIRT_VIEWER_IS_WINDOW(self));

    priv = self->priv;
    menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "menu-file-usb-device-selection"));
    gtk_widget_set_sensitive(menu, TRUE);
    gtk_widget_set_visible(priv->toolbar_usb_device_selection, sensitive);

    // set icon for main usb menu
    //main_menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "menu-file-usb"));

    //GError *error2  = NULL;
    //GdkPixbuf *gdkPixbuf =
    //        gdk_pixbuf_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png", &error2);
    //GtkWidget *image =
    //        gtk_image_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png");
    //gtk_tool_button_set_icon_widget(main_menu, image);
}

void
virt_viewer_window_set_menus_sensitive(VirtViewerWindow *self, gboolean sensitive)
{
    VirtViewerWindowPrivate *priv;
    GtkWidget *menu;

    g_return_if_fail(VIRT_VIEWER_IS_WINDOW(self));

    priv = self->priv;

    menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "menu-preferences"));
    gtk_widget_set_sensitive(menu, sensitive);

    menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "menu-file-screenshot"));
    gtk_widget_set_sensitive(menu, sensitive);

    menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "menu-view-zoom"));
    gtk_widget_set_sensitive(menu, sensitive);

    menu = GTK_WIDGET(gtk_builder_get_object(priv->builder, "menu-send"));
    gtk_widget_set_sensitive(menu, sensitive);
}

static void
display_show_hint(VirtViewerDisplay *display,
                  GParamSpec *pspec G_GNUC_UNUSED,
                  VirtViewerWindow *self)
{
    guint hint;

    g_object_get(display, "show-hint", &hint, NULL);

    hint = (hint & VIRT_VIEWER_DISPLAY_SHOW_HINT_READY);

    if (!self->priv->initial_zoom_set && hint && virt_viewer_display_get_enabled(display)) {
        self->priv->initial_zoom_set = TRUE;
        virt_viewer_window_set_zoom_level(self, self->priv->zoomlevel);
    }

    gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-file-screenshot")), hint);
}
static gboolean
window_key_pressed (GtkWidget *widget G_GNUC_UNUSED,
                    GdkEvent  *event,
                    GtkWidget *display)
{
    gtk_widget_grab_focus(display);
    return gtk_widget_event(display, event);
}

void
virt_viewer_window_set_display(VirtViewerWindow *self, VirtViewerDisplay *display)
{
    VirtViewerWindowPrivate *priv;

    g_return_if_fail(VIRT_VIEWER_IS_WINDOW(self));
    g_return_if_fail(display == NULL || VIRT_VIEWER_IS_DISPLAY(display));

    priv = self->priv;
    if (priv->display) {
        gtk_notebook_remove_page(GTK_NOTEBOOK(priv->notebook), 1);
        g_object_unref(priv->display);
        priv->display = NULL;
    }

    if (display != NULL) {
        priv->display = g_object_ref(display);

        virt_viewer_display_set_monitor(VIRT_VIEWER_DISPLAY(priv->display), priv->fullscreen_monitor);
        virt_viewer_display_set_fullscreen(VIRT_VIEWER_DISPLAY(priv->display), priv->fullscreen);

        gtk_widget_show_all(GTK_WIDGET(display));
        gtk_notebook_append_page(GTK_NOTEBOOK(priv->notebook), GTK_WIDGET(display), NULL);
        gtk_widget_realize(GTK_WIDGET(display));

        virt_viewer_signal_connect_object(priv->window, "key-press-event",
                                          G_CALLBACK(window_key_pressed), display, 0);

        /* switch back to non-display if not ready */
        if (!(virt_viewer_display_get_show_hint(display) &
              VIRT_VIEWER_DISPLAY_SHOW_HINT_READY))
            gtk_notebook_set_current_page(GTK_NOTEBOOK(priv->notebook), 0);

        virt_viewer_signal_connect_object(display, "display-pointer-grab",
                                          G_CALLBACK(virt_viewer_window_pointer_grab), self, 0);
        virt_viewer_signal_connect_object(display, "display-pointer-ungrab",
                                          G_CALLBACK(virt_viewer_window_pointer_ungrab), self, 0);
        virt_viewer_signal_connect_object(display, "display-keyboard-grab",
                                          G_CALLBACK(virt_viewer_window_keyboard_grab), self, 0);
        virt_viewer_signal_connect_object(display, "display-keyboard-ungrab",
                                          G_CALLBACK(virt_viewer_window_keyboard_ungrab), self, 0);
        virt_viewer_signal_connect_object(display, "display-desktop-resize",
                                          G_CALLBACK(virt_viewer_window_desktop_resize), self, 0);
        virt_viewer_signal_connect_object(display, "notify::show-hint",
                                          G_CALLBACK(display_show_hint), self, 0);

        display_show_hint(display, NULL, self);

        if (virt_viewer_display_get_enabled(display))
            virt_viewer_window_desktop_resize(display, self);

        gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-preferences")), TRUE);
        gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-view-zoom")), TRUE);
        gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(self->priv->builder, "menu-send")), TRUE);
        gtk_widget_set_sensitive(self->priv->toolbar_send_key, TRUE);
    }
}

static void
virt_viewer_window_enable_kiosk(VirtViewerWindow *self)
{
    VirtViewerWindowPrivate *priv;

    g_return_if_fail(VIRT_VIEWER_IS_WINDOW(self));
    priv = self->priv;

    virt_viewer_timed_revealer_force_reveal(priv->revealer, FALSE);

    /* You probably also want X11 Option "DontVTSwitch" "true" */
    /* and perhaps more distro/desktop-specific options */
    virt_viewer_window_disable_modifiers(self);
}

void
virt_viewer_window_show(VirtViewerWindow *self)
{
    if (self->priv->display && !virt_viewer_display_get_enabled(self->priv->display))
        virt_viewer_display_enable(self->priv->display);

    if (self->priv->desktop_resize_pending) {
        virt_viewer_window_queue_resize(self);
        self->priv->desktop_resize_pending = FALSE;
    }

    gtk_window_set_position (GTK_WINDOW(self->priv->window), GTK_WIN_POS_CENTER);
    gtk_widget_show(self->priv->window);

    if (self->priv->kiosk)
        virt_viewer_window_enable_kiosk(self);

    if (self->priv->fullscreen)
        virt_viewer_window_move_to_monitor(self);
}

void
virt_viewer_window_hide(VirtViewerWindow *self)
{
    if (self->priv->kiosk) {
        g_warning("Can't hide windows in kiosk mode");
        return;
    }

    gtk_widget_hide(self->priv->window);

    if (self->priv->display) {
        VirtViewerDisplay *display = self->priv->display;
        virt_viewer_display_disable(display);
    }
}

void
virt_viewer_window_set_zoom_level(VirtViewerWindow *self, gint zoom_level)
{
    VirtViewerWindowPrivate *priv;
    gint min_zoom;

    g_return_if_fail(VIRT_VIEWER_IS_WINDOW(self));
    priv = self->priv;

    if (zoom_level < MIN_ZOOM_LEVEL)
        zoom_level = MIN_ZOOM_LEVEL;
    if (zoom_level > MAX_ZOOM_LEVEL)
        zoom_level = MAX_ZOOM_LEVEL;
    priv->zoomlevel = zoom_level;

    if (!priv->display)
        return;

    min_zoom = virt_viewer_window_get_minimal_zoom_level(self);
    if (min_zoom > priv->zoomlevel) {
        g_debug("Cannot set zoom level %d, using %d", priv->zoomlevel, min_zoom);
        priv->zoomlevel = min_zoom;
    }

    if (priv->zoomlevel == virt_viewer_display_get_zoom_level(priv->display) &&
        priv->zoomlevel == virt_viewer_window_get_real_zoom_level(self)) {
        g_debug("Zoom level not changed, using: %d", priv->zoomlevel);
        return;
    }

    virt_viewer_display_set_zoom_level(VIRT_VIEWER_DISPLAY(priv->display), priv->zoomlevel);

    virt_viewer_window_queue_resize(self);
}

gint virt_viewer_window_get_zoom_level(VirtViewerWindow *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_WINDOW(self), NORMAL_ZOOM_LEVEL);
    return self->priv->zoomlevel;
}

GtkMenuItem*
virt_viewer_window_get_menu_displays(VirtViewerWindow *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_WINDOW(self), NULL);

    return GTK_MENU_ITEM(gtk_builder_get_object(self->priv->builder, "menu-displays"));
}

GtkBuilder*
virt_viewer_window_get_builder(VirtViewerWindow *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_WINDOW(self), NULL);

    return self->priv->builder;
}

VirtViewerDisplay*
virt_viewer_window_get_display(VirtViewerWindow *self)
{
    g_return_val_if_fail(VIRT_VIEWER_WINDOW(self), NULL);

    return self->priv->display;
}

void
virt_viewer_window_set_kiosk(VirtViewerWindow *self, gboolean enabled)
{
    g_return_if_fail(VIRT_VIEWER_IS_WINDOW(self));
    g_return_if_fail(enabled == !!enabled);

    if (self->priv->kiosk == enabled)
        return;

    self->priv->kiosk = enabled;

    if (enabled)
        virt_viewer_window_enable_kiosk(self);
    else
        g_debug("disabling kiosk not implemented yet");
}

static void
virt_viewer_window_get_minimal_dimensions(VirtViewerWindow *self,
                                          guint *width,
                                          guint *height)
{
    GtkRequisition req;
    GtkWidget *top_menu;

    top_menu = GTK_WIDGET(gtk_builder_get_object(virt_viewer_window_get_builder(self), "top-menu"));
    gtk_widget_get_preferred_size(top_menu, &req, NULL);
    /* minimal dimensions of the window are the maximum of dimensions of the top-menu
     * and minimal dimension of the display
     */
    *height = MIN_DISPLAY_HEIGHT;
    *width = MAX(MIN_DISPLAY_WIDTH, req.width);
}

/**
 * virt_viewer_window_get_minimal_zoom_level:
 * @self: a #VirtViewerWindow
 *
 * Calculates the zoom level with respect to the desktop dimensions
 *
 * Returns: minimal possible zoom level (multiple of ZOOM_STEP)
 */
static gint
virt_viewer_window_get_minimal_zoom_level(VirtViewerWindow *self)
{
    guint min_width, min_height;
    guint width, height; /* desktop dimensions */
    gint zoom;
    double width_ratio, height_ratio;

    g_return_val_if_fail(VIRT_VIEWER_IS_WINDOW(self) &&
                         self->priv->display != NULL, MIN_ZOOM_LEVEL);

    virt_viewer_window_get_minimal_dimensions(self, &min_width, &min_height);
    virt_viewer_display_get_desktop_size(virt_viewer_window_get_display(self), &width, &height);

    /* e.g. minimal width = 200, desktop width = 550 => width ratio = 0.36
     * which means that the minimal zoom level is 40 (4 * ZOOM_STEP)
     */
    width_ratio = (double) min_width / width;
    height_ratio = (double) min_height / height;
    zoom = ceil(10 * MAX(width_ratio, height_ratio));

    /* make sure that the returned zoom level is in the range from MIN_ZOOM_LEVEL to NORMAL_ZOOM_LEVEL */
    return CLAMP(zoom * ZOOM_STEP, MIN_ZOOM_LEVEL, NORMAL_ZOOM_LEVEL);
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
