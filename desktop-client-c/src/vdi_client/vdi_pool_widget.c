//
// Created by Solomin on 18.06.19.
//

#include "vdi_pool_widget.h"

VdiPoolWidget build_pool_widget(gint64 pool_id, const gchar *pool_name, GtkWidget *gtk_flow_box)
{
    VdiPoolWidget vdi_pool_widget  = {};

    if(gtk_flow_box == NULL)
        return vdi_pool_widget;

    //GtkFrame
    gchar *pool_idStr = g_strdup_printf("id %ld  ", pool_id);
    vdi_pool_widget.main_widget = gtk_frame_new (pool_idStr);
    g_free(pool_idStr);

    vdi_pool_widget.gtk_box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 3);
    // overlay
    vdi_pool_widget.gtk_overlay = gtk_overlay_new();
    gtk_container_add((GtkContainer *)vdi_pool_widget.gtk_overlay, vdi_pool_widget.gtk_box);

    // spinner
    vdi_pool_widget.vm_spinner = gtk_spinner_new ();
    gtk_overlay_add_overlay ((GtkOverlay *)vdi_pool_widget.gtk_overlay, vdi_pool_widget.vm_spinner);
    gtk_overlay_set_overlay_pass_through((GtkOverlay *)vdi_pool_widget.gtk_overlay, vdi_pool_widget.vm_spinner, TRUE);


    gtk_container_add((GtkContainer *)vdi_pool_widget.main_widget, vdi_pool_widget.gtk_overlay);
    // vm name
    vdi_pool_widget.vm_name_label = gtk_label_new (pool_name);
    gtk_box_pack_start((GtkBox *)vdi_pool_widget.gtk_box, vdi_pool_widget.vm_name_label, TRUE, TRUE, 0);
    // vm image
    vdi_pool_widget.image_widget =
            gtk_image_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/other_icon.png");
    gtk_box_pack_start((GtkBox *)vdi_pool_widget.gtk_box, vdi_pool_widget.image_widget, TRUE, TRUE, 0);
    // vm start button
    vdi_pool_widget.vm_start_button = gtk_button_new_with_label ("Подключиться");
    g_object_set_data((GObject *)vdi_pool_widget.vm_start_button, "pool_id", (gpointer)pool_id);
    gtk_box_pack_start((GtkBox *)vdi_pool_widget.gtk_box, vdi_pool_widget.vm_start_button, TRUE, TRUE, 0);
    //
    gtk_widget_set_size_request(vdi_pool_widget.main_widget, 100, 120);
    gtk_flow_box_insert((GtkFlowBox *)gtk_flow_box, vdi_pool_widget.main_widget, 0);

    gtk_widget_show_all(vdi_pool_widget.main_widget);

    return vdi_pool_widget;
}

void enable_spinner_visible(VdiPoolWidget *vdi_pool_widget, gboolean enable)
{
    if(vdi_pool_widget->vm_spinner == NULL)
        return;

    if(enable)
        gtk_spinner_start((GtkSpinner *)vdi_pool_widget->vm_spinner);
    else
        gtk_spinner_stop((GtkSpinner *)vdi_pool_widget->vm_spinner);
}

void destroy_vdi_pool_widget(VdiPoolWidget *vdi_pool_widget)
{
    gtk_widget_destroy(vdi_pool_widget->vm_spinner);
    gtk_widget_destroy(vdi_pool_widget->vm_name_label);
    gtk_widget_destroy(vdi_pool_widget->image_widget);
    gtk_widget_destroy(vdi_pool_widget->vm_start_button);
    gtk_widget_destroy(vdi_pool_widget->gtk_box);
    gtk_widget_destroy(vdi_pool_widget->gtk_overlay);
    gtk_widget_destroy(vdi_pool_widget->main_widget);
}
