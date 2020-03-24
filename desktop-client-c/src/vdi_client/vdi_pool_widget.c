//
// Created by Solomin on 18.06.19.
//

#include "vdi_pool_widget.h"

VdiPoolWidget build_pool_widget(const gchar *pool_id, const gchar *pool_name,
                                const gchar *os_type, const gchar *status, GtkWidget *gtk_flow_box)
{
    VdiPoolWidget vdi_pool_widget  = {};

    if (gtk_flow_box == NULL)
        return vdi_pool_widget;

    vdi_pool_widget.pool_id = g_strdup(pool_id);

    //GtkFrame
    vdi_pool_widget.main_widget = gtk_frame_new(NULL); // status

    vdi_pool_widget.gtk_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 3);
    // overlay
    vdi_pool_widget.gtk_overlay = gtk_overlay_new();
    gtk_container_add((GtkContainer *)vdi_pool_widget.gtk_overlay, vdi_pool_widget.gtk_box);

    // spinner
    vdi_pool_widget.vm_spinner = gtk_spinner_new();
    gtk_overlay_add_overlay((GtkOverlay *)vdi_pool_widget.gtk_overlay, vdi_pool_widget.vm_spinner);
    gtk_overlay_set_overlay_pass_through((GtkOverlay *)vdi_pool_widget.gtk_overlay, vdi_pool_widget.vm_spinner, TRUE);

    gtk_container_add((GtkContainer *)vdi_pool_widget.main_widget, vdi_pool_widget.gtk_overlay);

    // os image
    gchar *os_icon_path = NULL;
    if (g_strcmp0(os_type, "Windows") == 0) {
        os_icon_path = g_strdup(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/windows_icon.png");

    } else if (g_strcmp0(os_type, "Linux") == 0) {
        os_icon_path = g_strdup(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/linux_icon.png");

    } else {
        os_icon_path = g_strdup(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png");
    }

    vdi_pool_widget.image_widget = gtk_image_new_from_resource(os_icon_path);
    gtk_widget_set_name(vdi_pool_widget.image_widget, "vdi_pool_widget_image");
    free_memory_safely(&os_icon_path);

    // vm start button
    vdi_pool_widget.vm_start_button = gtk_button_new_with_label(pool_name);
    gtk_widget_set_name(vdi_pool_widget.vm_start_button, "vdi_pool_widget_button");

    gtk_button_set_always_show_image(GTK_BUTTON (vdi_pool_widget.vm_start_button), TRUE);
    gtk_button_set_image(GTK_BUTTON (vdi_pool_widget.vm_start_button), vdi_pool_widget.image_widget);
    gtk_button_set_image_position(GTK_BUTTON (vdi_pool_widget.vm_start_button), GTK_POS_BOTTOM);

    g_object_set_data((GObject *)vdi_pool_widget.vm_start_button, "pool_id", (gpointer)vdi_pool_widget.pool_id);
    gtk_box_pack_start((GtkBox *)vdi_pool_widget.gtk_box, vdi_pool_widget.vm_start_button, TRUE, TRUE, 0);

    // main_widget setup
    gtk_widget_set_size_request(vdi_pool_widget.main_widget, 100, 120);
    gtk_flow_box_insert((GtkFlowBox *)gtk_flow_box, vdi_pool_widget.main_widget, 0);

    // if pool status is not ACTIVE them we disable the widget
    if (g_strcmp0(status, "ACTIVE") != 0) {
        gtk_widget_set_sensitive(vdi_pool_widget.main_widget, FALSE);
        gtk_frame_set_label(GTK_FRAME(vdi_pool_widget.main_widget), status);
    }

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
    free_memory_safely(&vdi_pool_widget->pool_id);

    gtk_widget_destroy(vdi_pool_widget->vm_spinner);
    gtk_widget_destroy(vdi_pool_widget->image_widget);
    gtk_widget_destroy(vdi_pool_widget->vm_start_button);
    gtk_widget_destroy(vdi_pool_widget->gtk_box);
    gtk_widget_destroy(vdi_pool_widget->gtk_overlay);
    gtk_widget_destroy(vdi_pool_widget->main_widget);
}
