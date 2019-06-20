//
// Created by Solomin on 18.06.19.
//

#ifndef VIRT_VIEWER_VEIL_VDI_VM_WIDGET_H
#define VIRT_VIEWER_VEIL_VDI_VM_WIDGET_H

#include <glib/gi18n.h>
#include <gdk/gdkkeysyms.h>
#include <gtk/gtk.h>
#include <gtk/gtktypes.h>

#include "virt-viewer-util.h"

typedef struct{

    GtkWidget *mainWidget;

    GtkWidget *gtkBox;
    GtkWidget *gtkOverlay;

    GtkWidget *vmSpinner;

    GtkWidget *vmNameLabel;
    GtkWidget *imageWidget;
    GtkWidget *vmStartButton;

} VdiVmWidget;

// build vm widget and insert it in gtk_flow_box
VdiVmWidget buildVmWidget(gint64 vmId, const gchar *vmName, GtkWidget *gtk_flow_box);

// start / stop spinner
void enableSpinnerVisible(VdiVmWidget *vdiVmWidget, gboolean enable);

// destroy widget
void destroyVdiVmWidget(VdiVmWidget *vdiVmWidget);

#endif //VIRT_VIEWER_VEIL_VDI_VM_WIDGET_H
