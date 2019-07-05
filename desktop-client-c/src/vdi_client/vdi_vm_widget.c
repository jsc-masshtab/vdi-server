//
// Created by Solomin on 18.06.19.
//

#include "vdi_vm_widget.h"

VdiVmWidget buildVmWidget(gint64 vmId, const gchar *vmName, GtkWidget *gtk_flow_box)
{
    VdiVmWidget vdiVmWidget  = {};

    if(gtk_flow_box == NULL)
        return vdiVmWidget;

    //GtkFrame
    gchar *vmIdStr = g_strdup_printf("id %ld  ", vmId);
    vdiVmWidget.mainWidget = gtk_frame_new (vmIdStr);
    g_free(vmIdStr);

    vdiVmWidget.gtkBox = gtk_box_new (GTK_ORIENTATION_VERTICAL, 3);
    // overlay
    vdiVmWidget.gtkOverlay = gtk_overlay_new();
    gtk_container_add((GtkContainer *)vdiVmWidget.gtkOverlay, vdiVmWidget.gtkBox);

    // spinner
    vdiVmWidget.vmSpinner = gtk_spinner_new ();
    gtk_overlay_add_overlay ((GtkOverlay *)vdiVmWidget.gtkOverlay, vdiVmWidget.vmSpinner);
    gtk_overlay_set_overlay_pass_through((GtkOverlay *)vdiVmWidget.gtkOverlay, vdiVmWidget.vmSpinner, TRUE);


    gtk_container_add((GtkContainer *)vdiVmWidget.mainWidget, vdiVmWidget.gtkOverlay);
    // vm name
    vdiVmWidget.vmNameLabel = gtk_label_new (vmName);
    gtk_box_pack_start((GtkBox *)vdiVmWidget.gtkBox, vdiVmWidget.vmNameLabel, TRUE, TRUE, 0);
    // vm image
    vdiVmWidget.imageWidget =
            gtk_image_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/other_icon.png");
    gtk_box_pack_start((GtkBox *)vdiVmWidget.gtkBox, vdiVmWidget.imageWidget, TRUE, TRUE, 0);
    // vm start button
    vdiVmWidget.vmStartButton = gtk_button_new_with_label ("Подключиться");
    g_object_set_data((GObject *)vdiVmWidget.vmStartButton, "vmId", (gpointer)vmId);
    gtk_box_pack_start((GtkBox *)vdiVmWidget.gtkBox, vdiVmWidget.vmStartButton, TRUE, TRUE, 0);
    //
    gtk_widget_set_size_request(vdiVmWidget.mainWidget, 100, 120);
    gtk_flow_box_insert((GtkFlowBox *)gtk_flow_box, vdiVmWidget.mainWidget, 0);

    gtk_widget_show_all(vdiVmWidget.mainWidget);

    return vdiVmWidget;
}

void enableSpinnerVisible(VdiVmWidget *vdiVmWidget, gboolean enable)
{
    if(vdiVmWidget->vmSpinner == NULL)
        return;

    if(enable)
        gtk_spinner_start((GtkSpinner *)vdiVmWidget->vmSpinner);
    else
        gtk_spinner_stop((GtkSpinner *)vdiVmWidget->vmSpinner);
}

void destroyVdiVmWidget(VdiVmWidget *vdiVmWidget)
{
    gtk_widget_destroy(vdiVmWidget->vmSpinner);
    gtk_widget_destroy(vdiVmWidget->vmNameLabel);
    gtk_widget_destroy(vdiVmWidget->imageWidget);
    gtk_widget_destroy(vdiVmWidget->vmStartButton);
    gtk_widget_destroy(vdiVmWidget->gtkBox);
    gtk_widget_destroy(vdiVmWidget->gtkOverlay);
    gtk_widget_destroy(vdiVmWidget->mainWidget);
}