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

    GtkWidget *main_widget;

    GtkWidget *gtk_box;
    GtkWidget *gtk_overlay;

    GtkWidget *vm_spinner;

    GtkWidget *vm_name_label;
    GtkWidget *image_widget;
    GtkWidget *vm_start_button;

} VdiVmWidget;

// build vm widget and insert it in gtk_flow_box
VdiVmWidget build_vm_widget(gint64 vmId, const gchar *vmName, GtkWidget *gtk_flow_box);

// start / stop spinner
void enable_spinner_visible(VdiVmWidget *vdi_vm_widget, gboolean enable);

// destroy widget
void destroy_vdi_vm_widget(VdiVmWidget *vdi_vm_widget);

#endif //VIRT_VIEWER_VEIL_VDI_VM_WIDGET_H
