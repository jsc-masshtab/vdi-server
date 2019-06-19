//
// Created by ubuntu on 18.06.19.
//

#include "vdi_vm_widget.h"

VdiVmWidget buildVmWidget(gint64 vmId, const gchar *vmName, GtkWidget *gtk_flow_box)
{
    VdiVmWidget vdiVmWidget;

    if(gtk_flow_box == NULL)
        return vdiVmWidget;

    //GtkFrame
    vdiVmWidget.mainWidget = gtk_frame_new ("вм");

    vdiVmWidget.gtkBox = gtk_box_new (GTK_ORIENTATION_VERTICAL, 3);
    gtk_container_add(vdiVmWidget.mainWidget, vdiVmWidget.gtkBox);
    // vm name
    vdiVmWidget.vmNameLabel = gtk_label_new (vmName);
    gtk_box_pack_start(vdiVmWidget.gtkBox, vdiVmWidget.vmNameLabel, TRUE, TRUE, 0);
    // vm image
    vdiVmWidget.imageWidget =
            gtk_image_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/other_icon.png");
    gtk_box_pack_start(vdiVmWidget.gtkBox, vdiVmWidget.imageWidget, TRUE, TRUE, 0);
    // vm start button
    vdiVmWidget.vmStartButton = gtk_button_new_with_label ("Подключиться");
    g_object_set_data(vdiVmWidget.vmStartButton, "vmId", vmId);
    gtk_box_pack_start(vdiVmWidget.gtkBox, vdiVmWidget.vmStartButton, TRUE, TRUE, 0);
    //
    gtk_widget_set_size_request(vdiVmWidget.mainWidget, 100, 120);
    gtk_flow_box_insert(gtk_flow_box, vdiVmWidget.mainWidget, 0);

    gtk_widget_show_all(vdiVmWidget.mainWidget);

    return vdiVmWidget;
}

void destroyVdiVmWidget(VdiVmWidget *vdiVmWidget)
{
    gtk_widget_destroy(vdiVmWidget->vmNameLabel);
    gtk_widget_destroy(vdiVmWidget->imageWidget);
    gtk_widget_destroy(vdiVmWidget->vmStartButton);
    gtk_widget_destroy(vdiVmWidget->gtkBox);
    gtk_widget_destroy(vdiVmWidget->mainWidget);
}