/*
 * Veil VDI thin client
 * Based on virt-viewer and freerdp
 *
 */

#ifndef REMOTE_VIEWER_H
#define REMOTE_VIEWER_H

#include <glib-object.h>
#include "virt-viewer-app.h"

G_BEGIN_DECLS

#define REMOTE_VIEWER_TYPE remote_viewer_get_type()
#define REMOTE_VIEWER(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), REMOTE_VIEWER_TYPE, RemoteViewer))
#define REMOTE_VIEWER_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST ((klass), REMOTE_VIEWER_TYPE, RemoteViewerClass))
#define REMOTE_VIEWER_IS(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), REMOTE_VIEWER_TYPE))
#define REMOTE_VIEWER_IS_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE ((klass), REMOTE_VIEWER_TYPE))
#define REMOTE_VIEWER_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), REMOTE_VIEWER_TYPE, RemoteViewerClass))

typedef struct _RemoteViewerPrivate RemoteViewerPrivate;

typedef struct {
    VirtViewerApp parent;
    RemoteViewerPrivate *priv;
} RemoteViewer;

typedef struct {
    VirtViewerAppClass parent_class;
} RemoteViewerClass;

void virt_viewer_start_reconnect_poll(VirtViewerApp *self);
void virt_viewer_stop_reconnect_poll(VirtViewerApp *self);

GType remote_viewer_get_type (void);

RemoteViewer *remote_viewer_new (void);

G_END_DECLS

#endif /* REMOTE_VIEWER_H */
/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
