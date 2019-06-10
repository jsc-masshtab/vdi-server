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
#ifndef _VIRT_VIEWER_DISPLAY_H
#define _VIRT_VIEWER_DISPLAY_H

#include <gtk/gtk.h>
#include "virt-viewer-enums.h"

G_BEGIN_DECLS

#define MIN_DISPLAY_WIDTH 320
#define MIN_DISPLAY_HEIGHT 200

#define VIRT_VIEWER_TYPE_DISPLAY virt_viewer_display_get_type()

#define VIRT_VIEWER_DISPLAY(obj)                                        \
    (G_TYPE_CHECK_INSTANCE_CAST ((obj), VIRT_VIEWER_TYPE_DISPLAY, VirtViewerDisplay))

#define VIRT_VIEWER_DISPLAY_CLASS(klass)                                \
    (G_TYPE_CHECK_CLASS_CAST ((klass), VIRT_VIEWER_TYPE_DISPLAY, VirtViewerDisplayClass))

#define VIRT_VIEWER_IS_DISPLAY(obj)                                     \
    (G_TYPE_CHECK_INSTANCE_TYPE ((obj), VIRT_VIEWER_TYPE_DISPLAY))

#define VIRT_VIEWER_IS_DISPLAY_CLASS(klass)                             \
    (G_TYPE_CHECK_CLASS_TYPE ((klass), VIRT_VIEWER_TYPE_DISPLAY))

#define VIRT_VIEWER_DISPLAY_GET_CLASS(obj)                                \
    (G_TYPE_INSTANCE_GET_CLASS ((obj), VIRT_VIEWER_TYPE_DISPLAY, VirtViewerDisplayClass))

typedef struct _VirtViewerSession       VirtViewerSession;
typedef struct _VirtViewerSessionClass  VirtViewerSessionClass;

typedef struct _VirtViewerDisplay       VirtViewerDisplay;
typedef struct _VirtViewerDisplayClass  VirtViewerDisplayClass;
typedef struct _VirtViewerDisplayPrivate VirtViewerDisplayPrivate;

typedef struct _VirtViewerDisplayChannel VirtViewerDisplayChannel;

typedef enum {
    VIRT_VIEWER_DISPLAY_SHOW_HINT_READY            = 1 << 0,
    VIRT_VIEWER_DISPLAY_SHOW_HINT_DISABLED         = 1 << 1,
    VIRT_VIEWER_DISPLAY_SHOW_HINT_SET              = 1 << 2,
} VirtViewerDisplayShowHintFlags;

/* perhaps this become an interface, and be pushed in gtkvnc and spice? */
struct _VirtViewerDisplay {
    GtkBin parent;

    VirtViewerDisplayPrivate *priv;
};

struct _VirtViewerDisplayClass {
    GtkBinClass parent_class;

    /* virtual methods */
    void (*send_keys)(VirtViewerDisplay *display,
                      const guint *keyvals, int nkeyvals);
    GdkPixbuf *(*get_pixbuf)(VirtViewerDisplay *display);
    void (*release_cursor)(VirtViewerDisplay *display);

    void (*close)(VirtViewerDisplay *display);
    gboolean (*selectable)(VirtViewerDisplay *display);

    /* signals */
    void (*display_pointer_grab)(VirtViewerDisplay *display);
    void (*display_pointer_ungrab)(VirtViewerDisplay *display);
    void (*display_keyboard_grab)(VirtViewerDisplay *display);
    void (*display_keyboard_ungrab)(VirtViewerDisplay *display);

    void (*display_desktop_resize)(VirtViewerDisplay *display);
    void (*enable)(VirtViewerDisplay *display);
    void (*disable)(VirtViewerDisplay *display);
};

GType virt_viewer_display_get_type(void);

GtkWidget *virt_viewer_display_new(void);

void virt_viewer_display_set_desktop_size(VirtViewerDisplay *display,
                                          guint width,
                                          guint height);

void virt_viewer_display_get_desktop_size(VirtViewerDisplay *display,
                                          guint *width,
                                          guint *height);

void virt_viewer_display_set_zoom_level(VirtViewerDisplay *display,
                                        guint zoom);
guint virt_viewer_display_get_zoom_level(VirtViewerDisplay *display);
void virt_viewer_display_set_zoom(VirtViewerDisplay *display,
                                  gboolean zoom);
gboolean virt_viewer_display_get_zoom(VirtViewerDisplay *display);

void virt_viewer_display_send_keys(VirtViewerDisplay *display,
                                   const guint *keyvals, int nkeyvals);
GdkPixbuf* virt_viewer_display_get_pixbuf(VirtViewerDisplay *display);
void virt_viewer_display_set_show_hint(VirtViewerDisplay *display, guint mask, gboolean enable);
guint virt_viewer_display_get_show_hint(VirtViewerDisplay *display);
VirtViewerSession* virt_viewer_display_get_session(VirtViewerDisplay *display);
void virt_viewer_display_set_monitor(VirtViewerDisplay *display, gint monitor);
gint virt_viewer_display_get_monitor(VirtViewerDisplay *display);
void virt_viewer_display_set_fullscreen(VirtViewerDisplay *display, gboolean fullscreen);
gboolean virt_viewer_display_get_fullscreen(VirtViewerDisplay *display);
void virt_viewer_display_release_cursor(VirtViewerDisplay *display);

void virt_viewer_display_close(VirtViewerDisplay *display);
void virt_viewer_display_set_enabled(VirtViewerDisplay *display, gboolean enabled);
void virt_viewer_display_enable(VirtViewerDisplay *display);
void virt_viewer_display_disable(VirtViewerDisplay *display);
gboolean virt_viewer_display_get_enabled(VirtViewerDisplay *display);
gboolean virt_viewer_display_get_selectable(VirtViewerDisplay *display);
void virt_viewer_display_queue_resize(VirtViewerDisplay *display);
void virt_viewer_display_get_preferred_monitor_geometry(VirtViewerDisplay *self, GdkRectangle* preferred);
gint virt_viewer_display_get_nth(VirtViewerDisplay *self);

G_END_DECLS

#endif /* _VIRT_VIEWER_DISPLAY_H */
/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
