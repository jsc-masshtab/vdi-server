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

#include "virt-viewer-util.h"
#include "config.h"

#define MAX_KEY_COMBO 4
struct keyComboDef {
    guint keys[MAX_KEY_COMBO];
    const char *label;
    const gchar* accel_path;
};

typedef struct{
    GtkResponseType dialog_window_response;
    GMainLoop *loop;
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

static guint get_nkeys(const guint *keys)
{
    guint i;

    for (i = 0; keys[i] != GDK_KEY_VoidSymbol; )
        i++;

    return i;
}


void wair_for_mutex_and_clear(GMutex *cursor_mutex)
{
    g_mutex_lock(cursor_mutex);
    g_mutex_unlock(cursor_mutex);
    g_mutex_clear(cursor_mutex);
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
        //printf("%s ex_pointer->test_int: %i\n", (const char *)__func__,  ex_pointer->test_int);
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

static void rdp_viewer_item_about_activated(GtkWidget *menu G_GNUC_UNUSED, gpointer userdata)
{
    printf("%s\n", (const char *)__func__);
    // todo: code repeat with virt viewer
    GtkBuilder *about;
    GtkWidget *dialog;
    GdkPixbuf *icon;

    about = virt_viewer_util_load_ui("virt-viewer-about.ui");

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

GtkResponseType rdp_viewer_start(const gchar *usename, const gchar *password, gchar *ip, int port)
{
    RdpViewerData rdp_viewer_data;
    rdp_viewer_data.dialog_window_response = GTK_RESPONSE_CLOSE;

    // create RDP context
    UINT32 last_rdp_error = 0;
    ExtendedRdpContext *ex_context = create_rdp_context(&last_rdp_error); // deleted upon widget deletion
    rdp_client_set_credentials(ex_context, usename, password, ip, port);

    // gui
    GtkBuilder *builder = virt_viewer_util_load_ui("virt-viewer_veil.ui");

    gtk_widget_set_sensitive(GTK_WIDGET(gtk_builder_get_object(builder, "menu-file")), FALSE);

    GtkWidget *rdp_viewer_window = GTK_WIDGET(gtk_builder_get_object(builder, "viewer"));
    g_signal_connect_swapped(rdp_viewer_window, "delete-event",
                             G_CALLBACK(rdp_viewer_window_deleted_cb), &rdp_viewer_data);
    g_signal_connect(rdp_viewer_window, "map-event", G_CALLBACK(rdp_viewer_event_on_mapped), ex_context);

    GtkWidget *vbox = GTK_WIDGET(gtk_builder_get_object(builder, "viewer-box"));

    GtkWidget *menu_view = GTK_WIDGET(gtk_builder_get_object(builder, "menu-view"));
    gtk_widget_destroy(menu_view); // todo: view settings will be implemented in future (aproximately in 22nd century)

    GtkWidget *menu_usb = GTK_WIDGET(gtk_builder_get_object(builder, "menu-file-usb"));
    gtk_widget_destroy(menu_usb); // rdp automaticly redirects usb if app is launched with corresponding flag

    // remove inapropriate items from settings menu
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-file-smartcard-insert")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-file-smartcard-remove")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-change-cd")));
    gtk_widget_destroy(GTK_WIDGET(gtk_builder_get_object(builder, "menu-preferences")));

    GtkWidget *menu_send = GTK_WIDGET(gtk_builder_get_object(builder, "menu-send"));
    GtkMenu *sub_menu_send = GTK_MENU(gtk_menu_new()); // todo: when will it get deleted?
    gtk_menu_item_set_submenu(GTK_MENU_ITEM(menu_send), (GtkWidget*)sub_menu_send);
    // fill shortcuts
    fill_shortcuts_menu(sub_menu_send, ex_context);

    // help menu
    GtkWidget *item_external_link = GTK_WIDGET(gtk_builder_get_object(builder, "imagemenuitem10"));
    GtkWidget *item_about = GTK_WIDGET(gtk_builder_get_object(builder, "menu-help-guest-details"));
    g_signal_connect(item_external_link, "activate", G_CALLBACK(rdp_viewer_item_about_activated), rdp_viewer_window);
    g_signal_connect(item_about, "activate", G_CALLBACK(rdp_viewer_item_details_activated), NULL);

    // create RDP display
    GtkWidget *rdp_display = rdp_display_create(ex_context, &last_rdp_error);
    gtk_box_pack_end(GTK_BOX(vbox), GTK_WIDGET(rdp_display), TRUE, TRUE, 0);

    // show
    gtk_window_set_position((GtkWindow *)rdp_viewer_window, GTK_WIN_POS_CENTER);
    gtk_widget_show_all(rdp_viewer_window);
    guint g_timeout_id = g_timeout_add(16, (GSourceFunc)gtk_update_v2, rdp_display);
    //gtk_widget_add_tick_callback(rdp_display, gtk_update, context, NULL);

    create_loop_and_launch(&rdp_viewer_data.loop);

    // clear memory!
    destroy_rdp_context(ex_context);
    g_source_remove(g_timeout_id);
    g_object_unref(builder);
    gtk_widget_destroy(rdp_viewer_window);

    return rdp_viewer_data.dialog_window_response;
}
