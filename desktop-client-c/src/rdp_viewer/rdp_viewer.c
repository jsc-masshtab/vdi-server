/**
 * FreeRDP: A Remote Desktop Protocol Implementation
 * GTK GUI
 * Solomin a.solomin@mashtab.otg
 */

#include <gio/gio.h>
#include <gtk/gtk.h>
#include <glib/garray.h>
#include <gdk-pixbuf/gdk-pixbuf.h>

#include <cairo/cairo.h>

#include <freerdp/locale/keyboard.h>
#include <freerdp/scancode.h>

#include "rdp_viewer.h"
#include "rdp_client.h"
#include "rdp_display.h"

#include "remote-viewer-util.h"
#include "remote-viewer-timed-revealer.h"
#include "config.h"

#include "vdi_api_session.h"

#define MAX_KEY_COMBO 4
struct keyComboDef {
    guint keys[MAX_KEY_COMBO];
    const char *label;
    const gchar* accel_path;
};

typedef struct{
    GtkResponseType dialog_window_response;
    GMainLoop *loop;

    GtkWidget *rdp_viewer_window;
    GtkWidget *overlay_toolbar;
    VirtViewerTimedRevealer *revealer;
    GtkWidget *top_menu;

} RdpViewerData;

// static variables and constants
static const struct keyComboDef keyCombos[] = {
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_DELETE, GDK_KEY_VoidSymbol }, "Ctrl+Alt+_Del", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, GDK_KEY_BackSpace, GDK_KEY_VoidSymbol }, "Ctrl+Alt+_Backspace", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F1, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_1", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F2, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_2", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F3, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_3", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F4, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_4", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F5, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_5", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F6, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_6", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F7, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_7", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F8, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_8", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F9, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F_9", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F10, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F1_0", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F11, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F11", NULL},
    { { RDP_SCANCODE_LCONTROL, RDP_SCANCODE_LMENU, RDP_SCANCODE_F12, GDK_KEY_VoidSymbol }, "Ctrl+Alt+F12", NULL},
    { { RDP_SCANCODE_PRINTSCREEN, GDK_KEY_VoidSymbol }, "_PrintScreen", NULL},
};

// function declarations
static ExtendedRdpContext* create_rdp_context(UINT32 *last_rdp_error_p);
static void destroy_rdp_context(ExtendedRdpContext* ex_context);

// function implementations

static GdkRectangle get_default_monitor_geometry()
{
    GdkDisplay *display = gdk_display_get_default();
    GdkMonitor *monitor = gdk_display_get_monitor(display, 0);
    GdkRectangle geometry;
    gdk_monitor_get_geometry(monitor, &geometry);
    printf ("TESTT W: %u x H:%u\n", geometry.width, geometry.height);

    return geometry;
}

static guint get_nkeys(const guint *keys)
{
    guint i;

    for (i = 0; keys[i] != GDK_KEY_VoidSymbol; )
        i++;

    return i;
}

// if rdp session closed the context contains trash
static gboolean rdp_viewer_window_deleted_cb(gpointer userdata)
{
    printf("%s\n", (const char *)__func__);
    RdpViewerData *rdp_viewer_data = (RdpViewerData *)userdata;
    shutdown_loop(rdp_viewer_data->loop);

    return TRUE;
}

////static GTimer *timer = NULL;
//static gboolean gtk_update(GtkWidget *widget, GdkFrameClock *frame_clock, gpointer user_data)
//{
////    static int counter = 0;

////    if (!timer) {
////        timer = g_timer_new();
////        g_timer_start(timer);
////    }

////    gdouble time_elapsed = g_timer_elapsed(timer, NULL);
////    printf("%s time_elapsed: %f \n", (const char *)__func__, time_elapsed);


////    if (!is_running)
////        return TRUE;

//    //printf("%s BEG \n", (const char *)__func__);

//    //rdpContext* context = user_data;
//    //ExtendedRdpContext* tf = (ExtendedRdpContext*)context;

//    //int hor_squeez = 0;
//    //gtk_widget_queue_draw_area(widget, hor_squeez, 0, 1024 - hor_squeez *2, 768);
//    gtk_widget_queue_draw(widget);

//    return TRUE;
//}

static gboolean gtk_update_v2(gpointer user_data)
{
    //ExtendedRdpContext* tf = (ExtendedRdpContext*)user_data;
    GtkWidget *rdp_display = (GtkWidget *)user_data;
    gtk_widget_queue_draw(rdp_display);

    return TRUE;
}

void rdp_viewer_event_on_mapped(GtkWidget *widget G_GNUC_UNUSED, GdkEvent *event G_GNUC_UNUSED, gpointer user_data)
{
    rdpContext* context = user_data;
    // launch RDP routine in thread. Stop its when GTK window closed
    GTask *task = g_task_new(NULL, NULL, NULL, NULL);
    g_task_set_task_data(task, context, NULL);
    g_task_run_in_thread(task, rdp_client_routine);
    g_object_unref(task);
}

static gboolean update_cursor_callback(rdpContext* context)
{
    ExtendedRdpContext* ex_context = (ExtendedRdpContext*)context;

    if (!ex_context || !ex_context->is_running)
        return TRUE;

    GdkWindow *parent_window = gtk_widget_get_parent_window(ex_context->rdp_display);
    if (parent_window) {
        g_mutex_lock(&ex_context->cursor_mutex);
        //printf("%s ex_pointer->test_int: \n", (const char *)__func__);
        gdk_window_set_cursor(parent_window,  ex_context->gdk_cursor);
        //g_object_unref(ex_context->gdk_cursor); // TODO: problems
        g_mutex_unlock(&ex_context->cursor_mutex);
    }

    return FALSE;
}

static void rdp_viewer_item_details_activated(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    GError *error = NULL;
    gtk_show_uri_on_window(NULL, "http://mashtab.org/files/veil/index.html", GDK_CURRENT_TIME, &error);
}

static void rdp_viewer_item_fullscreen_activated(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata)
{
    RdpViewerData *rdp_viewer_data = (RdpViewerData *)userdata;

    gtk_window_set_resizable(GTK_WINDOW(rdp_viewer_data->rdp_viewer_window), TRUE);
    gtk_window_fullscreen(GTK_WINDOW(rdp_viewer_data->rdp_viewer_window));
    //gtk_window_set_resizable(GTK_WINDOW(rdp_viewer_window), FALSE);

    // show toolbar
    gtk_widget_hide(rdp_viewer_data->top_menu);
    gtk_widget_show(rdp_viewer_data->overlay_toolbar);
    virt_viewer_timed_revealer_force_reveal(rdp_viewer_data->revealer, TRUE);
}

static void rdp_viewer_item_about_activated(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata)
{
    printf("%s\n", (const char *)__func__);
    // todo: code repeat with virt viewer
    GtkBuilder *about;
    GtkWidget *dialog;
    GdkPixbuf *icon;

    about = remote_viewer_util_load_ui("virt-viewer-about.ui");

    dialog = GTK_WIDGET(gtk_builder_get_object(about, "about"));
    gtk_about_dialog_set_version ((GtkAboutDialog *)dialog, VERSION);
    gtk_about_dialog_set_license ((GtkAboutDialog *)dialog, "");

    //gtk_about_dialog_set_version(GTK_ABOUT_DIALOG(dialog), VERSION BUILDID);

    icon = gdk_pixbuf_new_from_resource(VIRT_VIEWER_RESOURCE_PREFIX"/icons/content/img/veil-32x32.png", NULL);
    if (icon != NULL) {
        gtk_about_dialog_set_logo(GTK_ABOUT_DIALOG(dialog), icon);
        g_object_unref(icon);
    } else {
        gtk_about_dialog_set_logo_icon_name(GTK_ABOUT_DIALOG(dialog), "virt-viewer_veil");
    }

    GtkWindow *rdp_viewer_window = userdata;
    gtk_window_set_transient_for(GTK_WINDOW(dialog), rdp_viewer_window);

    gtk_builder_connect_signals(about, rdp_viewer_window);

    gtk_widget_show_all(dialog);

    g_object_unref(G_OBJECT(about));
}

static void send_key_shortcut(rdpContext* context, int key_shortcut_index)
{
    rdpInput *input = context->input;

    guint key_array_size = get_nkeys(keyCombos[key_shortcut_index].keys);

    for (guint i = 0; i < key_array_size; ++i)
        freerdp_input_send_keyboard_event_ex(input, TRUE, keyCombos[key_shortcut_index].keys[i]);
    for (guint i = 0; i < key_array_size; ++i)
        freerdp_input_send_keyboard_event_ex(input, FALSE, keyCombos[key_shortcut_index].keys[i]);
}

static void rdp_viewer_window_menu_send(GtkWidget *menu, gpointer userdata)
{
    ExtendedRdpContext* ex_context = (ExtendedRdpContext*)userdata;
    if (!ex_context || !ex_context->is_running)
        return;

    rdpContext context = ex_context->context;

    int *key_shortcut_index = (g_object_get_data(G_OBJECT(menu), "key_shortcut_index"));
    printf("%s %i %i %i\n", (const char *)__func__,
           keyCombos[*key_shortcut_index].keys[0], keyCombos[*key_shortcut_index].keys[1],
            keyCombos[*key_shortcut_index].keys[2]);
    send_key_shortcut(&context, *key_shortcut_index);
}

static void
rdp_viewer_window_menu_switch_off(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata)
{
    printf("%s\n", (const char *)__func__);
    RdpViewerData *rdp_viewer_data = (RdpViewerData *)userdata;
    rdp_viewer_data->dialog_window_response = GTK_RESPONSE_CANCEL;
    shutdown_loop(rdp_viewer_data->loop);
}

static void
rdp_viewer_window_menu_start_vm(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    do_action_on_vm_async("start", FALSE);
}

static void
rdp_viewer_window_menu_suspend_vm(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    do_action_on_vm_async("suspend", FALSE);
}

static void
rdp_viewer_window_menu_shutdown_vm(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    do_action_on_vm_async("shutdown", FALSE);
}

static void
rdp_viewer_window_menu_shutdown_vm_force(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    do_action_on_vm_async("shutdown", TRUE);
}

static void
rdp_viewer_window_menu_reboot_vm(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    do_action_on_vm_async("reboot", FALSE);
}

static void
rdp_viewer_window_menu_reboot_vm_force(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    do_action_on_vm_async("reboot", TRUE);
}

static void rdp_viewer_control_menu_setup(GtkBuilder *builder, RdpViewerData *rdp_viewer_data)
{
    GtkMenuItem *menu_switch_off = GTK_MENU_ITEM(gtk_builder_get_object(builder, "menu-switch-off"));
    GtkMenuItem *menu_start_vm = GTK_MENU_ITEM(gtk_builder_get_object(builder, "menu-start-vm"));
    GtkMenuItem *menu_suspend_vm = GTK_MENU_ITEM(gtk_builder_get_object(builder, "menu-suspend-vm"));
    GtkMenuItem *menu_shutdown_vm = GTK_MENU_ITEM(gtk_builder_get_object(builder, "menu-shutdown-vm"));
    GtkMenuItem *menu_shutdown_vm_force = GTK_MENU_ITEM(gtk_builder_get_object(builder, "menu-shutdown-vm-force"));
    GtkMenuItem *menu_reboot_vm = GTK_MENU_ITEM(gtk_builder_get_object(builder, "menu-reboot-vm"));
    GtkMenuItem *menu_reboot_vm_force = GTK_MENU_ITEM(gtk_builder_get_object(builder, "menu-reboot-vm-force"));

    g_signal_connect(menu_switch_off, "activate", G_CALLBACK(rdp_viewer_window_menu_switch_off), rdp_viewer_data);
    g_signal_connect(menu_start_vm, "activate", G_CALLBACK(rdp_viewer_window_menu_start_vm), NULL);
    g_signal_connect(menu_suspend_vm, "activate", G_CALLBACK(rdp_viewer_window_menu_suspend_vm), NULL);
    g_signal_connect(menu_shutdown_vm, "activate", G_CALLBACK(rdp_viewer_window_menu_shutdown_vm), NULL);
    g_signal_connect(menu_shutdown_vm_force, "activate", G_CALLBACK(rdp_viewer_window_menu_shutdown_vm_force), NULL);
    g_signal_connect(menu_reboot_vm, "activate", G_CALLBACK(rdp_viewer_window_menu_reboot_vm), NULL);
    g_signal_connect(menu_reboot_vm_force, "activate", G_CALLBACK(rdp_viewer_window_menu_reboot_vm_force), NULL);
}

static void rdp_viewer_window_toolbar_leave_fullscreen(GtkWidget *button G_GNUC_UNUSED, gpointer userdata)
{
    RdpViewerData *rdp_viewer_data = (RdpViewerData *)userdata;

    gtk_widget_hide(rdp_viewer_data->overlay_toolbar);
    //gtk_widget_set_size_request(priv->window, -1, -1);
    gtk_window_unfullscreen(GTK_WINDOW(rdp_viewer_data->rdp_viewer_window));
    gtk_widget_show(rdp_viewer_data->top_menu);
}

static void rdp_viewer_toolbar_setup(GtkBuilder *builder, RdpViewerData *rdp_viewer_data)
{
    GtkWidget *button;

    // create a toolbar which will be shown in fullscreen mode
    rdp_viewer_data->overlay_toolbar = gtk_toolbar_new();
    gtk_toolbar_set_show_arrow(GTK_TOOLBAR(rdp_viewer_data->overlay_toolbar), FALSE);
    gtk_widget_set_no_show_all(rdp_viewer_data->overlay_toolbar, TRUE);
    gtk_toolbar_set_style(GTK_TOOLBAR(rdp_viewer_data->overlay_toolbar), GTK_TOOLBAR_BOTH_HORIZ);

    /* Leave fullscreen */
    button = GTK_WIDGET(gtk_tool_button_new(NULL, NULL));
    gtk_tool_button_set_icon_name(GTK_TOOL_BUTTON(button), "view-restore");
    gtk_tool_button_set_label(GTK_TOOL_BUTTON(button), ("Покинуть полный экран"));
    gtk_tool_item_set_tooltip_text(GTK_TOOL_ITEM(button), ("Покинуть полный экран"));
    gtk_tool_item_set_is_important(GTK_TOOL_ITEM(button), TRUE);
    gtk_widget_show(button);
    gtk_toolbar_insert(GTK_TOOLBAR(rdp_viewer_data->overlay_toolbar), GTK_TOOL_ITEM(button), 0);
    g_signal_connect(button, "clicked", G_CALLBACK(rdp_viewer_window_toolbar_leave_fullscreen), rdp_viewer_data);

    // add tollbar to overlay
    rdp_viewer_data->revealer = virt_viewer_timed_revealer_new(rdp_viewer_data->overlay_toolbar);
    GtkWidget *overlay = GTK_WIDGET(gtk_builder_get_object(builder, "viewer-overlay"));
    gtk_overlay_add_overlay(GTK_OVERLAY(overlay), GTK_WIDGET(rdp_viewer_data->revealer));
}

static void fill_shortcuts_menu(GtkMenu *sub_menu_send, ExtendedRdpContext* ex_context)
{
    int num_of_shortcuts = G_N_ELEMENTS(keyCombos);
    for (int i = 0; i < num_of_shortcuts; ++i) {
        GtkWidget *menu_item = gtk_menu_item_new_with_mnemonic(keyCombos[i].label); // todo: when will it get deleted?
        gtk_container_add(GTK_CONTAINER(sub_menu_send), menu_item);

        int *key_shortcut_index = malloc(sizeof(int));
        *key_shortcut_index = i;
        g_object_set_data_full(G_OBJECT(menu_item), "key_shortcut_index", key_shortcut_index, free);
        g_signal_connect(menu_item, "activate", G_CALLBACK(rdp_viewer_window_menu_send), ex_context);
    }
}

static ExtendedRdpContext* create_rdp_context(UINT32 *last_rdp_error_p)
{
    rdpContext* context = rdp_client_create_context();
    ExtendedRdpContext* ex_context = (ExtendedRdpContext*)context;
    ex_context->is_running = FALSE;
    //ex_context->update_image_callback = (UpdateImageCallback)update_image_callback;
    ex_context->update_cursor_callback = (UpdateCursorCallback)update_cursor_callback;
    ex_context->test_int = 666; // temp
    ex_context->last_rdp_error_p = last_rdp_error_p;
    // init mutex for rdp_routine syncronization
    g_mutex_init(&ex_context->rdp_routine_mutex);
    g_mutex_init(&ex_context->cursor_mutex);

    return ex_context;
}

static void destroy_rdp_context(ExtendedRdpContext* ex_context)
{
    if (ex_context && ex_context->is_running) {
        // stopping RDP routine

        printf("%s: abort now: %i\n", (const char *)__func__, ex_context->test_int);

        freerdp_abort_connect(ex_context->context.instance);
        // wait untill rdp thread finished. todo: seriously think if some sort of event primitive could be used
        wair_for_mutex_and_clear(&ex_context->rdp_routine_mutex);
        wair_for_mutex_and_clear(&ex_context->cursor_mutex);

        printf("%s: context free now: %i\n", (const char *)__func__, ex_context->test_int);
        freerdp_client_context_free((rdpContext*)ex_context);
        ex_context = NULL;
    }
}

GtkResponseType rdp_viewer_start(const gchar *usename, const gchar *password, gchar *domain, gchar *ip, int port)
{
    printf("%s domain %s\n", (const char *)__func__, domain);
    RdpViewerData rdp_viewer_data;
    rdp_viewer_data.dialog_window_response = GTK_RESPONSE_CLOSE;

    GdkRectangle default_monitor_geometry = get_default_monitor_geometry();

    // create RDP context
    UINT32 last_rdp_error = 0;
    ExtendedRdpContext *ex_context = create_rdp_context(&last_rdp_error); // deleted upon widget deletion
    rdp_client_set_credentials(ex_context, usename, password, domain, ip, port);

    const int max_image_width = 1920;
    const int max_image_height = 1080;
    int optimal_image_width = MIN(max_image_width, default_monitor_geometry.width);
    int optimal_image_height = MIN(max_image_height, default_monitor_geometry.height);
    rdp_client_set_optimilal_image_size(ex_context, optimal_image_width, optimal_image_height);

    // gui
    GtkBuilder *builder = remote_viewer_util_load_ui("virt-viewer_veil.ui");

    GtkWidget *rdp_viewer_window = rdp_viewer_data.rdp_viewer_window =
            GTK_WIDGET(gtk_builder_get_object(builder, "viewer"));
    g_signal_connect_swapped(rdp_viewer_window, "delete-event",
                             G_CALLBACK(rdp_viewer_window_deleted_cb), &rdp_viewer_data);
    g_signal_connect(rdp_viewer_window, "map-event", G_CALLBACK(rdp_viewer_event_on_mapped), ex_context);

    rdp_viewer_data.top_menu = GTK_WIDGET(gtk_builder_get_object(builder, "top-menu"));

    // usb menu is not required for rdp
    GtkWidget *menu_usb = GTK_WIDGET(gtk_builder_get_object(builder, "menu-file-usb"));
    gtk_widget_destroy(menu_usb); // rdp automaticly redirects usb if app is launched with corresponding flag

    // remove inapropriate items from settings menu
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-file-smartcard-insert")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-file-smartcard-remove")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-change-cd")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-preferences")));

    // control menu
    rdp_viewer_control_menu_setup(builder, &rdp_viewer_data);

    // controll toolbar used in fullscreen
    rdp_viewer_toolbar_setup(builder, &rdp_viewer_data);

    // view menu
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-view-zoom")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-displays")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-view-release-cursor")));
    GtkWidget *item_fullscreen = GTK_WIDGET(gtk_builder_get_object(builder, "menu-view-fullscreen"));
    g_signal_connect(item_fullscreen, "activate", G_CALLBACK(rdp_viewer_item_fullscreen_activated), &rdp_viewer_data);

    // shortcuts
    GtkWidget *menu_send = GTK_WIDGET(gtk_builder_get_object(builder, "menu-send"));
    GtkMenu *sub_menu_send = GTK_MENU(gtk_menu_new()); // todo: when will it get deleted?
    gtk_menu_item_set_submenu(GTK_MENU_ITEM(menu_send), (GtkWidget*)sub_menu_send);
    fill_shortcuts_menu(sub_menu_send, ex_context);

    // help menu
    GtkWidget *item_external_link = GTK_WIDGET(gtk_builder_get_object(builder, "imagemenuitem10"));
    GtkWidget *item_about = GTK_WIDGET(gtk_builder_get_object(builder, "menu-help-guest-details"));
    g_signal_connect(item_external_link, "activate", G_CALLBACK(rdp_viewer_item_about_activated), rdp_viewer_window);
    g_signal_connect(item_about, "activate", G_CALLBACK(rdp_viewer_item_details_activated), NULL);

    // create RDP display
    GtkWidget *rdp_display = rdp_display_create(rdp_viewer_window, ex_context, &last_rdp_error);
    GtkWidget *vbox = GTK_WIDGET(gtk_builder_get_object(builder, "viewer-box"));
    gtk_box_pack_end(GTK_BOX(vbox), GTK_WIDGET(rdp_display), TRUE, TRUE, 0);

    // show
    gtk_window_set_position(GTK_WINDOW(rdp_viewer_window), GTK_WIN_POS_CENTER);
    gtk_window_resize(GTK_WINDOW(rdp_viewer_window), optimal_image_width, optimal_image_height);
    gtk_widget_show_all(rdp_viewer_window);

    guint g_timeout_id = g_timeout_add(30, (GSourceFunc)gtk_update_v2, rdp_display);
    //gtk_widget_add_tick_callback(rdp_display, gtk_update, context, NULL);

    create_loop_and_launch(&rdp_viewer_data.loop);

    // clear memory!
    destroy_rdp_context(ex_context);
    g_source_remove(g_timeout_id);
    g_object_unref(builder);
    gtk_widget_destroy(rdp_viewer_window);

    return rdp_viewer_data.dialog_window_response;
}
