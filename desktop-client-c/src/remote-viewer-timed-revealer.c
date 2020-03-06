/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (c) 2016 Red Hat, Inc.
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
 * Author: Cole Robinson <crobinso@redhat.com>
 * Author: Fabiano Fidêncio <fidencio@redhat.com>
 */

#include <config.h>

#include "remote-viewer-timed-revealer.h"

G_DEFINE_TYPE (VirtViewerTimedRevealer, virt_viewer_timed_revealer, GTK_TYPE_EVENT_BOX)

#define VIRT_VIEWER_TIMED_REVEALER_GET_PRIVATE(obj) \
    (G_TYPE_INSTANCE_GET_PRIVATE ((obj), VIRT_VIEWER_TYPE_TIMED_REVEALER, VirtViewerTimedRevealerPrivate))

struct _VirtViewerTimedRevealerPrivate
{
    gboolean fullscreen;
    guint timeout_id;

    GtkWidget *revealer;
};

static void
virt_viewer_timed_revealer_unregister_timeout(VirtViewerTimedRevealer *self)
{
    VirtViewerTimedRevealerPrivate *priv = self->priv;

    if (priv->timeout_id) {
        g_source_remove(priv->timeout_id);
        priv->timeout_id = 0;
    }
}

static gboolean
schedule_unreveal_timeout_cb(VirtViewerTimedRevealer *self)
{
    VirtViewerTimedRevealerPrivate *priv = self->priv;

    gtk_revealer_set_reveal_child(GTK_REVEALER(priv->revealer), FALSE);
    priv->timeout_id = 0;

    return FALSE;
}

static void
virt_viewer_timed_revealer_schedule_unreveal_timeout(VirtViewerTimedRevealer *self,
                                                     guint timeout)
{
    VirtViewerTimedRevealerPrivate *priv = self->priv;

    if (priv->timeout_id != 0)
        return;

    priv->timeout_id = g_timeout_add(timeout,
                                     (GSourceFunc)schedule_unreveal_timeout_cb,
                                     self);
}

static void
virt_viewer_timed_revealer_grab_notify(VirtViewerTimedRevealer *self,
                                       gboolean was_grabbed,
                                       gpointer user_data G_GNUC_UNUSED)
{
    if (was_grabbed)
        virt_viewer_timed_revealer_schedule_unreveal_timeout(self, 1000);
}

static gboolean
virt_viewer_timed_revealer_enter_leave_notify(VirtViewerTimedRevealer *self,
                                              GdkEventCrossing *event,
                                              gpointer user_data G_GNUC_UNUSED)
{
    VirtViewerTimedRevealerPrivate *priv = self->priv;
    GdkDevice *device;
    GtkAllocation allocation;
    gint x, y;
    gboolean entered;

    if (!priv->fullscreen)
        return FALSE;

    device = gdk_event_get_device((GdkEvent *)event);

    gdk_window_get_device_position(event->window, device, &x, &y, 0);
    gtk_widget_get_allocation(GTK_WIDGET(self), &allocation);

    entered = !!(x >= 0 && y >= 0 && x < allocation.width && y < allocation.height);

    /*
     * Pointer exited the toolbar, and toolbar is revealed. Schedule
     * a timeout to close it, if one isn't already scheduled.
     */
    if (!entered && gtk_revealer_get_reveal_child(GTK_REVEALER(priv->revealer))) {
        virt_viewer_timed_revealer_schedule_unreveal_timeout(self, 1000);
        return FALSE;
    }

    virt_viewer_timed_revealer_unregister_timeout(self);
    if (entered && !gtk_revealer_get_reveal_child(GTK_REVEALER(priv->revealer))) {
        gtk_revealer_set_reveal_child(GTK_REVEALER(priv->revealer), TRUE);
    }

    return FALSE;
}

static void
virt_viewer_timed_revealer_init(VirtViewerTimedRevealer *self)
{
    self->priv = VIRT_VIEWER_TIMED_REVEALER_GET_PRIVATE(self);
}

static void
virt_viewer_timed_revealer_dispose(GObject *object)
{
    VirtViewerTimedRevealer *self = VIRT_VIEWER_TIMED_REVEALER(object);
    VirtViewerTimedRevealerPrivate *priv = self->priv;

    priv->revealer = NULL;

    if (priv->timeout_id) {
        g_source_remove(priv->timeout_id);
        priv->timeout_id = 0;
    }

    G_OBJECT_CLASS(virt_viewer_timed_revealer_parent_class)->dispose(object);
}


static void
virt_viewer_timed_revealer_class_init(VirtViewerTimedRevealerClass *klass)
{
   GObjectClass *object_class = G_OBJECT_CLASS(klass);

   g_type_class_add_private (klass, sizeof (VirtViewerTimedRevealerPrivate));

   object_class->dispose = virt_viewer_timed_revealer_dispose;
}

VirtViewerTimedRevealer *
virt_viewer_timed_revealer_new(GtkWidget *toolbar)
{
    VirtViewerTimedRevealer *self;
    VirtViewerTimedRevealerPrivate *priv;

    self = g_object_new(VIRT_VIEWER_TYPE_TIMED_REVEALER, NULL);

    priv = self->priv;

    priv->fullscreen = FALSE;
    priv->timeout_id = 0;

    priv->revealer = gtk_revealer_new();
    gtk_container_add(GTK_CONTAINER(priv->revealer), toolbar);

    /*
     * Adding the revealer to the eventbox seems to ensure the
     * GtkEventBox always has 1 invisible pixel showing at the top of the
     * screen, which we can use to grab the pointer event to show
     * the hidden toolbar.
     */

    gtk_container_add(GTK_CONTAINER(self), priv->revealer);
    gtk_widget_set_halign(GTK_WIDGET(self), GTK_ALIGN_CENTER);
    gtk_widget_set_valign(GTK_WIDGET(self), GTK_ALIGN_START);
    gtk_widget_show_all(GTK_WIDGET(self));

    g_signal_connect(self,
                     "grab-notify",
                     G_CALLBACK(virt_viewer_timed_revealer_grab_notify),
                     NULL);
    g_signal_connect(self,
                     "enter-notify-event",
                     G_CALLBACK(virt_viewer_timed_revealer_enter_leave_notify),
                     NULL);
    g_signal_connect(self,
                     "leave-notify-event",
                     G_CALLBACK(virt_viewer_timed_revealer_enter_leave_notify),
                     NULL);

    return self;
}

void
virt_viewer_timed_revealer_force_reveal(VirtViewerTimedRevealer *self,
                                        gboolean fullscreen)
{
    VirtViewerTimedRevealerPrivate *priv;

    g_return_if_fail(VIRT_VIEWER_IS_TIMED_REVEALER(self));

    priv = self->priv;

    virt_viewer_timed_revealer_unregister_timeout(self);
    priv->fullscreen = fullscreen;
    gtk_revealer_set_reveal_child(GTK_REVEALER(priv->revealer), fullscreen);
    virt_viewer_timed_revealer_schedule_unreveal_timeout(self, 2000);
}
