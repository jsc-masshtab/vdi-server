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
#include "virt-viewer-display.h"
#include "virt-viewer-util.h"

#define VIRT_VIEWER_DISPLAY_GET_PRIVATE(o) (G_TYPE_INSTANCE_GET_PRIVATE((o), VIRT_VIEWER_TYPE_DISPLAY, VirtViewerDisplayPrivate))

struct _VirtViewerDisplayPrivate
{
    guint desktopWidth;
    guint desktopHeight;
    guint zoom_level;
    gint nth_display; /* Monitor number inside the guest */
    gint monitor;     /* Monitor number on the client */
    guint show_hint;
    VirtViewerSession *session;
    gboolean fullscreen;
};

static void virt_viewer_display_get_preferred_width(GtkWidget *widget,
                                                    int *minwidth,
                                                    int *defwidth);
static void virt_viewer_display_get_preferred_height(GtkWidget *widget,
                                                     int *minheight,
                                                     int *defheight);
static void virt_viewer_display_size_allocate(GtkWidget *widget,
                                              GtkAllocation *allocation);
static void virt_viewer_display_set_property(GObject *object,
                                             guint prop_id,
                                             const GValue *value,
                                             GParamSpec *pspec);
static void virt_viewer_display_get_property(GObject *object,
                                             guint prop_id,
                                             GValue *value,
                                             GParamSpec *pspec);
static void virt_viewer_display_grab_focus(GtkWidget *widget);

G_DEFINE_ABSTRACT_TYPE(VirtViewerDisplay, virt_viewer_display, GTK_TYPE_BIN)

enum {
    PROP_0,

    PROP_DESKTOP_WIDTH,
    PROP_DESKTOP_HEIGHT,
    PROP_FULLSCREEN,
    PROP_NTH_DISPLAY,
    PROP_ZOOM,
    PROP_ZOOM_LEVEL,
    PROP_SHOW_HINT,
    PROP_SESSION,
    PROP_SELECTABLE,
    PROP_MONITOR,
};

static void
virt_viewer_display_class_init(VirtViewerDisplayClass *class)
{
    GObjectClass *object_class = G_OBJECT_CLASS(class);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS(class);

    object_class->set_property = virt_viewer_display_set_property;
    object_class->get_property = virt_viewer_display_get_property;

    widget_class->get_preferred_width = virt_viewer_display_get_preferred_width;
    widget_class->get_preferred_height = virt_viewer_display_get_preferred_height;
    widget_class->size_allocate = virt_viewer_display_size_allocate;
    widget_class->grab_focus = virt_viewer_display_grab_focus;

    g_object_class_install_property(object_class,
                                    PROP_DESKTOP_WIDTH,
                                    g_param_spec_int("desktop-width",
                                                     "Width",
                                                     "Desktop width",
                                                     MIN_DISPLAY_WIDTH,
                                                     G_MAXINT32,
                                                     MIN_DISPLAY_WIDTH,
                                                     G_PARAM_READWRITE));

    g_object_class_install_property(object_class,
                                    PROP_DESKTOP_HEIGHT,
                                    g_param_spec_int("desktop-height",
                                                     "Height",
                                                     "Desktop height",
                                                     MIN_DISPLAY_HEIGHT,
                                                     G_MAXINT32,
                                                     MIN_DISPLAY_HEIGHT,
                                                     G_PARAM_READWRITE));

    g_object_class_install_property(object_class,
                                    PROP_ZOOM_LEVEL,
                                    g_param_spec_int("zoom-level",
                                                     "Zoom",
                                                     "Zoom level",
                                                     MIN_ZOOM_LEVEL,
                                                     MAX_ZOOM_LEVEL,
                                                     NORMAL_ZOOM_LEVEL,
                                                     G_PARAM_READWRITE));

    g_object_class_install_property(object_class,
                                    PROP_NTH_DISPLAY,
                                    g_param_spec_int("nth-display",
                                                     "Nth display",
                                                     "Nth display",
                                                     0,
                                                     G_MAXINT32,
                                                     0,
                                                     G_PARAM_READWRITE |
                                                     G_PARAM_CONSTRUCT_ONLY));

    g_object_class_install_property(object_class,
                                    PROP_SHOW_HINT,
                                    g_param_spec_flags("show-hint",
                                                       "Show hint",
                                                       "Show state hint",
                                                       VIRT_VIEWER_TYPE_DISPLAY_SHOW_HINT_FLAGS,
                                                       0,
                                                       G_PARAM_READABLE));

    g_object_class_install_property(object_class,
                                    PROP_SESSION,
                                    g_param_spec_object("session",
                                                        "Session",
                                                        "VirtSession",
                                                        VIRT_VIEWER_TYPE_SESSION,
                                                        G_PARAM_READWRITE |
                                                        G_PARAM_CONSTRUCT_ONLY));

    g_object_class_install_property(object_class,
                                    PROP_SELECTABLE,
                                    g_param_spec_boolean("selectable",
                                                         "Selectable",
                                                         "Selectable",
                                                         FALSE,
                                                         G_PARAM_READABLE));

    g_object_class_install_property(object_class,
                                    PROP_MONITOR,
                                    g_param_spec_int("monitor",
                                                     "Monitor",
                                                     "Display Monitor",
                                                     -1,
                                                     G_MAXINT32,
                                                     -1,
                                                     G_PARAM_READWRITE |
                                                     G_PARAM_CONSTRUCT));

    g_object_class_install_property(object_class,
                                    PROP_FULLSCREEN,
                                    g_param_spec_boolean("fullscreen",
                                                         "Fullscreen",
                                                         "Fullscreen",
                                                         FALSE,
                                                         G_PARAM_READABLE));

    g_signal_new("display-pointer-grab",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerDisplayClass, display_pointer_grab),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("display-pointer-ungrab",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerDisplayClass, display_pointer_ungrab),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("display-keyboard-grab",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerDisplayClass, display_keyboard_grab),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("display-keyboard-ungrab",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerDisplayClass, display_keyboard_ungrab),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("display-desktop-resize",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 G_STRUCT_OFFSET(VirtViewerDisplayClass, display_desktop_resize),
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_signal_new("monitor-geometry-changed",
                 G_OBJECT_CLASS_TYPE(object_class),
                 G_SIGNAL_RUN_LAST | G_SIGNAL_NO_HOOKS,
                 0,
                 NULL,
                 NULL,
                 g_cclosure_marshal_VOID__VOID,
                 G_TYPE_NONE,
                 0);

    g_type_class_add_private(class, sizeof(VirtViewerDisplayPrivate));
}

static void
virt_viewer_display_init(VirtViewerDisplay *display)
{
    gtk_widget_set_has_window(GTK_WIDGET(display), FALSE);
    gtk_widget_set_redraw_on_allocate(GTK_WIDGET(display), FALSE);

    display->priv = VIRT_VIEWER_DISPLAY_GET_PRIVATE(display);

    display->priv->desktopWidth = MIN_DISPLAY_WIDTH;
    display->priv->desktopHeight = MIN_DISPLAY_HEIGHT;
    display->priv->zoom_level = NORMAL_ZOOM_LEVEL;
}

GtkWidget*
virt_viewer_display_new(void)
{
    return g_object_new(VIRT_VIEWER_TYPE_DISPLAY, NULL);
}

static void
virt_viewer_display_set_property(GObject *object,
                                 guint prop_id,
                                 const GValue *value,
                                 GParamSpec *pspec)
{
    VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(object);
    VirtViewerDisplayPrivate *priv = display->priv;

    switch (prop_id) {
    case PROP_DESKTOP_WIDTH:
        priv->desktopWidth = g_value_get_int(value);
        break;
    case PROP_DESKTOP_HEIGHT:
        priv->desktopHeight = g_value_get_int(value);
        break;
    case PROP_NTH_DISPLAY:
        priv->nth_display = g_value_get_int(value);
        break;
    case PROP_SESSION:
        g_warn_if_fail(priv->session == NULL);
        priv->session = g_value_get_object(value);
        break;
    case PROP_MONITOR:
        priv->monitor = g_value_get_int(value);
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
        break;
    }
}

static void
virt_viewer_display_get_property(GObject *object,
                                 guint prop_id,
                                 GValue *value,
                                 GParamSpec *pspec)
{
    VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(object);
    VirtViewerDisplayPrivate *priv = display->priv;

    switch (prop_id) {
    case PROP_DESKTOP_WIDTH:
        g_value_set_int(value, priv->desktopWidth);
        break;
    case PROP_DESKTOP_HEIGHT:
        g_value_set_int(value, priv->desktopHeight);
        break;
    case PROP_NTH_DISPLAY:
        g_value_set_int(value, priv->nth_display);
        break;
    case PROP_SHOW_HINT:
        g_value_set_flags(value, priv->show_hint);
        break;
    case PROP_SESSION:
        g_value_set_object(value, virt_viewer_display_get_session(display));
        break;
    case PROP_SELECTABLE:
        g_value_set_boolean(value, virt_viewer_display_get_selectable(display));
        break;
    case PROP_MONITOR:
        g_value_set_int(value, priv->monitor);
        break;
    case PROP_FULLSCREEN:
        g_value_set_boolean(value, virt_viewer_display_get_fullscreen(display));
        break;

    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
        break;
    }
}


static void
virt_viewer_display_grab_focus(GtkWidget *widget)
{
    GtkBin *bin = GTK_BIN(widget);

    gtk_widget_grab_focus(gtk_bin_get_child(bin));
}

static void virt_viewer_display_get_preferred_dimension_from_desktop(VirtViewerDisplay *display,
                                                                     const int minimal_size,
                                                                     const int desktop_dim,
                                                                     int *minimal_dim,
                                                                     int *preferred_dim)
{
    int border_width = gtk_container_get_border_width(GTK_CONTAINER(display));

    if (virt_viewer_display_get_zoom(display)) {
        guint zoom_level = virt_viewer_display_get_zoom_level(display);
        *preferred_dim = round(desktop_dim * zoom_level / (double) NORMAL_ZOOM_LEVEL);
        *minimal_dim = round(minimal_size * zoom_level / (double) NORMAL_ZOOM_LEVEL);
    } else {
        *preferred_dim = desktop_dim;
        *minimal_dim = minimal_size;
    }
    *preferred_dim += 2 * border_width;
    *minimal_dim += 2 * border_width;
}


static void virt_viewer_display_get_preferred_width(GtkWidget *widget,
                                                    int *minwidth,
                                                    int *defwidth)
{
    VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(widget);
    VirtViewerDisplayPrivate *priv = display->priv;

    virt_viewer_display_get_preferred_dimension_from_desktop(display,
                                                             MIN_DISPLAY_WIDTH,
                                                             priv->desktopWidth,
                                                             minwidth,
                                                             defwidth);
}


static void virt_viewer_display_get_preferred_height(GtkWidget *widget,
                                                     int *minheight,
                                                     int *defheight)
{
    VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(widget);
    VirtViewerDisplayPrivate *priv = display->priv;

    virt_viewer_display_get_preferred_dimension_from_desktop(display,
                                                             MIN_DISPLAY_HEIGHT,
                                                             priv->desktopHeight,
                                                             minheight,
                                                             defheight);
}


static void
virt_viewer_display_size_allocate(GtkWidget *widget,
                                  GtkAllocation *allocation)
{
    GtkBin *bin = GTK_BIN(widget);
    VirtViewerDisplay *display = VIRT_VIEWER_DISPLAY(widget);
    VirtViewerDisplayPrivate *priv = display->priv;
    GtkAllocation child_allocation;
    gint width, height;
    gint border_width;
    double desktopAspect;
    double actualAspect;
    GtkWidget *child = gtk_bin_get_child(bin);

    g_debug("Allocated %dx%d", allocation->width, allocation->height);
    gtk_widget_set_allocation(widget, allocation);

    if (priv->desktopWidth == 0 || priv->desktopHeight == 0 ||
        child == NULL || !gtk_widget_get_visible(child))
        return;

    border_width = gtk_container_get_border_width(GTK_CONTAINER(display));

    width  = MAX(MIN_DISPLAY_WIDTH, allocation->width - 2 * border_width);
    height = MAX(MIN_DISPLAY_HEIGHT, allocation->height - 2 * border_width);

    desktopAspect = (double) priv->desktopWidth / (double) priv->desktopHeight;
    actualAspect = (double) width / (double) height;

    if (actualAspect > desktopAspect) {
        child_allocation.width = round(height * desktopAspect);
        child_allocation.height = height;
    } else {
        child_allocation.width = width;
        child_allocation.height = round(width / desktopAspect);
    }

    child_allocation.x = 0.5 * (width - child_allocation.width) + allocation->x + border_width;
    child_allocation.y = 0.5 * (height - child_allocation.height) + allocation->y + border_width;

    g_debug("Child allocate %dx%d", child_allocation.width, child_allocation.height);
    gtk_widget_size_allocate(child, &child_allocation);
}


void virt_viewer_display_set_desktop_size(VirtViewerDisplay *display,
                                          guint width,
                                          guint height)
{
    VirtViewerDisplayPrivate *priv = display->priv;

    if (width == priv->desktopWidth && height == priv->desktopHeight)
        return;

    priv->desktopWidth = width;
    priv->desktopHeight = height;

    virt_viewer_display_queue_resize(display);

    g_signal_emit_by_name(display, "display-desktop-resize");
}


void virt_viewer_display_get_desktop_size(VirtViewerDisplay *display,
                                          guint *width,
                                          guint *height)
{
    VirtViewerDisplayPrivate *priv = display->priv;

    *width = priv->desktopWidth;
    *height = priv->desktopHeight;
}


void virt_viewer_display_queue_resize(VirtViewerDisplay *display)
{
    GtkWidget *child = gtk_bin_get_child(GTK_BIN(display));

    if (child && gtk_widget_get_visible(child)) {
        gtk_widget_queue_resize(GTK_WIDGET(display));
    }
}

void virt_viewer_display_set_zoom_level(VirtViewerDisplay *display,
                                        guint zoom)
{
    VirtViewerDisplayPrivate *priv = display->priv;

    if (zoom < MIN_ZOOM_LEVEL)
        zoom = MIN_ZOOM_LEVEL;
    if (zoom > MAX_ZOOM_LEVEL)
        zoom = MAX_ZOOM_LEVEL;

    if (priv->zoom_level == zoom)
        return;

    priv->zoom_level = zoom;

    virt_viewer_display_queue_resize(display);
    g_object_notify(G_OBJECT(display), "zoom-level");
}


guint virt_viewer_display_get_zoom_level(VirtViewerDisplay *display)
{
    VirtViewerDisplayPrivate *priv = display->priv;
    return priv->zoom_level;
}

gboolean virt_viewer_display_get_zoom(VirtViewerDisplay *display)
{
    return virt_viewer_display_get_zoom_level(display) != NORMAL_ZOOM_LEVEL;
}


void virt_viewer_display_send_keys(VirtViewerDisplay *display,
                                   const guint *keyvals, int nkeyvals)
{
    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(display));

    VIRT_VIEWER_DISPLAY_GET_CLASS(display)->send_keys(display, keyvals, nkeyvals);
}

GdkPixbuf* virt_viewer_display_get_pixbuf(VirtViewerDisplay *display)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_DISPLAY(display), NULL);

    return VIRT_VIEWER_DISPLAY_GET_CLASS(display)->get_pixbuf(display);
}

guint virt_viewer_display_get_show_hint(VirtViewerDisplay *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_DISPLAY(self), 0);

    return self->priv->show_hint;
}

void virt_viewer_display_set_show_hint(VirtViewerDisplay *self, guint mask, gboolean enable)
{
    VirtViewerDisplayPrivate *priv;
    guint hint;
    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    priv = self->priv;
    hint = priv->show_hint;

    if (enable)
        hint |= mask;
    else
        hint &= ~mask;

    if (priv->show_hint == hint)
        return;

    priv->show_hint = hint;
    g_object_notify(G_OBJECT(self), "show-hint");
}

/* This function attempts to enable the display if supported by the backend */
void virt_viewer_display_enable(VirtViewerDisplay *self)
{
    VirtViewerDisplayClass *klass;

    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    klass = VIRT_VIEWER_DISPLAY_GET_CLASS(self);
    if (!klass->enable)
        return;

    klass->enable(self);
}

/* This function attempts to disable the display if supported by the backend */
void virt_viewer_display_disable(VirtViewerDisplay *self)
{
    VirtViewerDisplayClass *klass;

    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    klass = VIRT_VIEWER_DISPLAY_GET_CLASS(self);
    if (!klass->disable)
        return;

    klass->disable(self);
}

/* this function simply informs the display that it is enabled. see
 * virt_viewer_display_enable()/disable() if you want to attempt to change the
 * state of the display */
void virt_viewer_display_set_enabled(VirtViewerDisplay *self, gboolean enabled)
{
    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    g_object_freeze_notify(G_OBJECT(self));

    virt_viewer_display_set_show_hint(self, VIRT_VIEWER_DISPLAY_SHOW_HINT_SET, TRUE);
    virt_viewer_display_set_show_hint(self, VIRT_VIEWER_DISPLAY_SHOW_HINT_DISABLED, !enabled);

    g_object_thaw_notify(G_OBJECT(self));
}

gboolean virt_viewer_display_get_enabled(VirtViewerDisplay *self)
{
    return ((self->priv->show_hint & VIRT_VIEWER_DISPLAY_SHOW_HINT_SET) &&
        !(self->priv->show_hint & VIRT_VIEWER_DISPLAY_SHOW_HINT_DISABLED));
}

VirtViewerSession* virt_viewer_display_get_session(VirtViewerDisplay *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_DISPLAY(self), NULL);

    return self->priv->session;
}

void virt_viewer_display_set_monitor(VirtViewerDisplay *self, gint monitor)
{
    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    self->priv->monitor = monitor;
    g_object_notify(G_OBJECT(self), "monitor");
}

gint virt_viewer_display_get_monitor(VirtViewerDisplay *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_DISPLAY(self), -1);

    return self->priv->monitor;
}

void virt_viewer_display_release_cursor(VirtViewerDisplay *self)
{
    VirtViewerDisplayClass *klass;

    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    klass = VIRT_VIEWER_DISPLAY_GET_CLASS(self);
    g_return_if_fail(klass->release_cursor != NULL);

    klass->release_cursor(self);
}

gboolean virt_viewer_display_get_selectable(VirtViewerDisplay *self)
{
    VirtViewerDisplayClass *klass;

    g_return_val_if_fail(VIRT_VIEWER_IS_DISPLAY(self), FALSE);

    klass = VIRT_VIEWER_DISPLAY_GET_CLASS(self);
    if (klass->selectable)
        return klass->selectable(self);

    return TRUE;
}

void virt_viewer_display_close(VirtViewerDisplay *self)
{
    VirtViewerDisplayClass *klass;

    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    klass = VIRT_VIEWER_DISPLAY_GET_CLASS(self);
    g_return_if_fail(klass->close != NULL);

    klass->close(self);
}

void virt_viewer_display_set_fullscreen(VirtViewerDisplay *self, gboolean fullscreen)
{
    g_return_if_fail(VIRT_VIEWER_IS_DISPLAY(self));

    if (self->priv->fullscreen == fullscreen)
        return;

    self->priv->fullscreen = fullscreen;
    g_object_notify(G_OBJECT(self), "fullscreen");
}

gboolean virt_viewer_display_get_fullscreen(VirtViewerDisplay *self)
{
    g_return_val_if_fail(VIRT_VIEWER_IS_DISPLAY(self), FALSE);

    return self->priv->fullscreen;
}

void virt_viewer_display_get_preferred_monitor_geometry(VirtViewerDisplay* self,
                                                        GdkRectangle* preferred)
{
    GtkWidget *top = NULL;
    gint topx = 0, topy = 0;

    g_return_if_fail(preferred != NULL);

    if (!virt_viewer_display_get_enabled(self)) {
        preferred->width = 0;
        preferred->height = 0;
        preferred->x = 0;
        preferred->y = 0;
        return;
    }

    top = gtk_widget_get_toplevel(GTK_WIDGET(self));
    gtk_window_get_position(GTK_WINDOW(top), &topx, &topy);
    topx = MAX(topx, 0);
    topy = MAX(topy, 0);

    if (virt_viewer_display_get_fullscreen(self)) {
        GdkRectangle physical_monitor;
        GdkScreen *screen = gtk_widget_get_screen(GTK_WIDGET(self));
        int n = virt_viewer_display_get_monitor(self);
        if (n == -1)
            n = gdk_screen_get_monitor_at_window(screen,
                                                 gtk_widget_get_window(GTK_WIDGET(self)));
        gdk_screen_get_monitor_geometry(screen, n, &physical_monitor);
        preferred->x = physical_monitor.x;
        preferred->y = physical_monitor.y;
        preferred->width = physical_monitor.width;
        preferred->height = physical_monitor.height;
    } else {
        gtk_widget_get_allocation(GTK_WIDGET(self), preferred);
        preferred->x = topx;
        preferred->y = topy;
    }

    if (virt_viewer_display_get_zoom(self)) {
        guint zoom = virt_viewer_display_get_zoom_level(self);

        preferred->width = round(preferred->width * NORMAL_ZOOM_LEVEL / (double) zoom);
        preferred->height = round(preferred->height * NORMAL_ZOOM_LEVEL / (double) zoom);
    }
}

gint
virt_viewer_display_get_nth(VirtViewerDisplay *self)
{
    return self->priv->nth_display;
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
