//
// Created by Solomin on 18.06.19.
//

#include "vdi_vm_widget.h"

VdiVmWidget build_vm_widget(gint64 vmId, const gchar *vmName, GtkWidget *gtk_flow_box)
{
    VdiVmWidget vdi_vm_widget  = {};

    if(gtk_flow_box == NULL)
        return vdi_vm_widget;

    //GtkFrame
    gchar *vmIdStr = g_strdup_printf("id %ld  ", vmId);
    vdi_vm_widget.main_widget = gtk_frame_new (vmIdStr);
    g_free(vmIdStr);

    vdi_vm_widget.gtk_box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 3);
    // overlay
    vdi_vm_widget.gtk_overlay = gtk_overlay_new();
    gtk_container_add((GtkContainer *)vdi_vm_widget.gtk_overlay, vdi_vm_widget.gtk_box);

    // spinner
    vdi_vm_widget.vm_spinner = gtk_spinner_new ();
    gtk_overlay_add_overlay ((GtkOverlay *)vdi_vm_widget.gtk_overlay, vdi_vm_widget.vm_spinner);
    gtk_overlay_set_overlay_pass_through((GtkOverlay *)vdi_vm_widget.gtk_overlay, vdi_vm_widget.vm_spinner, TRUE);


    gtk_container_add((GtkContainer *)vdi_vm_widget.main_widget, vdi_vm_widget.gtk_overlay);
    // vm name
    vdi_vm_widget.vm_name_label = gtk_label_new (vmName);
    gtk_box_pack_start((GtkBox *)vdi_vm_widget.gtk_box, vdi_vm_widget.vm_name_label, TRUE, TRUE, 0);
    // vm image
    vdi_vm_widget.image_widget =
            gtk_image_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/other_icon.png");
    gtk_box_pack_start((GtkBox *)vdi_vm_widget.gtk_box, vdi_vm_widget.image_widget, TRUE, TRUE, 0);
    // vm start button
    vdi_vm_widget.vm_start_button = gtk_button_new_with_label ("Подключиться");
    g_object_set_data((GObject *)vdi_vm_widget.vm_start_button, "vmId", (gpointer)vmId);
    gtk_box_pack_start((GtkBox *)vdi_vm_widget.gtk_box, vdi_vm_widget.vm_start_button, TRUE, TRUE, 0);
    //
    gtk_widget_set_size_request(vdi_vm_widget.main_widget, 100, 120);
    gtk_flow_box_insert((GtkFlowBox *)gtk_flow_box, vdi_vm_widget.main_widget, 0);

    gtk_widget_show_all(vdi_vm_widget.main_widget);

    return vdi_vm_widget;
}

void enable_spinner_visible(VdiVmWidget *vdi_vm_widget, gboolean enable)
{
    if(vdi_vm_widget->vm_spinner == NULL)
        return;

    if(enable)
        gtk_spinner_start((GtkSpinner *)vdi_vm_widget->vm_spinner);
    else
        gtk_spinner_stop((GtkSpinner *)vdi_vm_widget->vm_spinner);
}

void destroy_vdi_vm_widget(VdiVmWidget *vdi_vm_widget)
{
    gtk_widget_destroy(vdi_vm_widget->vm_spinner);
    gtk_widget_destroy(vdi_vm_widget->vm_name_label);
    gtk_widget_destroy(vdi_vm_widget->image_widget);
    gtk_widget_destroy(vdi_vm_widget->vm_start_button);
    gtk_widget_destroy(vdi_vm_widget->gtk_box);
    gtk_widget_destroy(vdi_vm_widget->gtk_overlay);
    gtk_widget_destroy(vdi_vm_widget->main_widget);
}