#include "rdp_display.h"

#include <gio/gio.h>
#include <gtk/gtk.h>
#include <glib/garray.h>
#include <gdk-pixbuf/gdk-pixbuf.h>

#include <cairo/cairo.h>

#include <freerdp/locale/keyboard.h>
#include <freerdp/scancode.h>

static const gchar *error_to_str(UINT32 rdp_error)
{
    //rdp_error = (rdp_error >= 0x10000 && rdp_error < 0x00020000) ? (rdp_error & 0xFFFF) : rdp_error;

    if (rdp_error >= 0x10000 && rdp_error < 0x00020000) {
        rdp_error = (rdp_error & 0xFFFF);

        switch (rdp_error) {
        case ERRINFO_RPC_INITIATED_DISCONNECT:
            return "ERRINFO_RPC_INITIATED_DISCONNECT";
        case ERRINFO_RPC_INITIATED_LOGOFF:
            return "ERRINFO_RPC_INITIATED_LOGOFF";
        case ERRINFO_IDLE_TIMEOUT:
            return "ERRINFO_IDLE_TIMEOUT";
        case ERRINFO_LOGON_TIMEOUT:
            return "ERRINFO_LOGON_TIMEOUT";
        case ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION:
            return "ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION";
        case ERRINFO_OUT_OF_MEMORY:
            return "ERRINFO_OUT_OF_MEMORY";
        case ERRINFO_SERVER_DENIED_CONNECTION:
            return "ERRINFO_SERVER_DENIED_CONNECTION";
        case ERRINFO_SERVER_INSUFFICIENT_PRIVILEGES:
            return "ERRINFO_SERVER_INSUFFICIENT_PRIVILEGES";
        case ERRINFO_SERVER_FRESH_CREDENTIALS_REQUIRED:
            return "ERRINFO_SERVER_FRESH_CREDENTIALS_REQUIRED";
        case ERRINFO_RPC_INITIATED_DISCONNECT_BY_USER:
            return "ERRINFO_RPC_INITIATED_DISCONNECT_BY_USER";
        case ERRINFO_LOGOFF_BY_USER:
            return "ERRINFO_LOGOFF_BY_USER";
        case ERRINFO_CLOSE_STACK_ON_DRIVER_NOT_READY:
            return "ERRINFO_CLOSE_STACK_ON_DRIVER_NOT_READY";
        case ERRINFO_SERVER_DWM_CRASH:
            return "ERRINFO_SERVER_DWM_CRASH";
        case ERRINFO_CLOSE_STACK_ON_DRIVER_FAILURE:
            return "ERRINFO_CLOSE_STACK_ON_DRIVER_FAILURE";
        case ERRINFO_CLOSE_STACK_ON_DRIVER_IFACE_FAILURE:
            return "ERRINFO_CLOSE_STACK_ON_DRIVER_IFACE_FAILURE";
        case ERRINFO_SERVER_WINLOGON_CRASH:
            return "ERRINFO_SERVER_WINLOGON_CRASH";
        case ERRINFO_SERVER_CSRSS_CRASH:
            return "ERRINFO_SERVER_CSRSS_CRASH";
        default:
            return "";
        }
    }
    else {
        rdp_error = (rdp_error & 0xFFFF);

        switch (rdp_error) {
        case ERRCONNECT_PRE_CONNECT_FAILED:
            return "ERRCONNECT_PRE_CONNECT_FAILED";
        case ERRCONNECT_CONNECT_UNDEFINED:
            return "ERRCONNECT_CONNECT_UNDEFINED";
        case ERRCONNECT_POST_CONNECT_FAILED:
            return "ERRCONNECT_POST_CONNECT_FAILED";
        case ERRCONNECT_DNS_ERROR:
            return "ERRCONNECT_DNS_ERROR";
        case ERRCONNECT_DNS_NAME_NOT_FOUND:
            return "ERRCONNECT_DNS_NAME_NOT_FOUND";
        case ERRCONNECT_CONNECT_FAILED:
            return "ERRCONNECT_CONNECT_FAILED";
        case ERRCONNECT_MCS_CONNECT_INITIAL_ERROR:
            return "ERRCONNECT_MCS_CONNECT_INITIAL_ERROR";
        case ERRCONNECT_TLS_CONNECT_FAILED:
            return "ERRCONNECT_TLS_CONNECT_FAILED";
        case ERRCONNECT_AUTHENTICATION_FAILED:
            return "ERRCONNECT_AUTHENTICATION_FAILED";
        case ERRCONNECT_INSUFFICIENT_PRIVILEGES:
            return "ERRCONNECT_INSUFFICIENT_PRIVILEGES";
        case ERRCONNECT_CONNECT_CANCELLED:
            return "ERRCONNECT_CONNECT_CANCELLED";
        case ERRCONNECT_SECURITY_NEGO_CONNECT_FAILED:
            return "ERRCONNECT_SECURITY_NEGO_CONNECT_FAILED";
        case ERRCONNECT_CONNECT_TRANSPORT_FAILED:
            return "ERRCONNECT_CONNECT_TRANSPORT_FAILED";
        case ERRCONNECT_PASSWORD_EXPIRED:
            return "ERRCONNECT_PASSWORD_EXPIRED";
        default:
            return "";
        }
    }
}

// TODO: Почему-то не работает переключение языка
static gboolean rdp_display_key_pressed(GtkWidget *widget G_GNUC_UNUSED, GdkEventKey *event, gpointer user_data)
{
    ExtendedRdpContext* tf = (ExtendedRdpContext*)user_data;
    if (!tf || !tf->is_running)
        return TRUE;

    rdpInput *input = tf->context.input;

    //printf("%s: key %i\n", (const char *)__func__, event->keyval);

    // todo: guess its not gonna work on Windows
    DWORD rdp_scancode = freerdp_keyboard_get_rdp_scancode_from_x11_keycode(event->hardware_keycode);
    BOOL is_success = freerdp_input_send_keyboard_event_ex(input, TRUE, rdp_scancode);
    //BOOL is_success = freerdp_input_send_keyboard_event(input, (UINT16)1, (UINT16)event->hardware_keycode);

    printf("%s: key %i %i %i\n", (const char *)__func__, event->hardware_keycode, rdp_scancode, is_success);
    //printf("%s:  %i\n", (const char *)__func__, );

    return TRUE;
}
// TODO: Get rid of code repeat
static gboolean rdp_display_key_released(GtkWidget *widget G_GNUC_UNUSED, GdkEventKey *event, gpointer user_data)
{
    ExtendedRdpContext* tf = (ExtendedRdpContext*)user_data;
    if (!tf || !tf->is_running)
        return TRUE;

    rdpContext* context = user_data;
    rdpInput *input = context->input;

    DWORD rdp_scancode = freerdp_keyboard_get_rdp_scancode_from_x11_keycode(event->hardware_keycode);
    BOOL is_success = freerdp_input_send_keyboard_event_ex(input, FALSE, rdp_scancode);
    printf("%s: key %i %i %i\n", (const char *)__func__, event->hardware_keycode, rdp_scancode, is_success);

    return TRUE;
}

static gboolean rdp_display_mouse_moved(GtkWidget *widget G_GNUC_UNUSED, GdkEventMotion *event, gpointer user_data)
{
    ExtendedRdpContext* tf = (ExtendedRdpContext*)user_data;
    if (!tf || !tf->is_running)
        return TRUE;

    rdpContext* context = user_data;
    rdpInput *input = context->input;

    BOOL is_success = freerdp_input_send_mouse_event(input, PTR_FLAGS_MOVE, (UINT16)event->x, (UINT16)event->y);
    (void)is_success;
    //printf("%s: event->x %f, event->y %f  %i\n", (const char *)__func__, event->x, event->y, is_success);

    return TRUE;
}

static void rdp_viewer_handle_mouse_btn_event(GtkWidget *widget G_GNUC_UNUSED, GdkEventButton *event, gpointer user_data,
                                                  UINT16 additional_flags)
{
    ExtendedRdpContext* tf = (ExtendedRdpContext*)user_data;
    if (!tf || !tf->is_running)
        return;

    rdpContext* context = user_data;
    rdpInput *input = context->input;

    UINT16 button = 0;
    switch (event->button)
    {
    case GDK_BUTTON_PRIMARY:{
        button = PTR_FLAGS_BUTTON1;
        break;
    }
    case GDK_BUTTON_SECONDARY:{
        button = PTR_FLAGS_BUTTON2;
        break;
    }
    case GDK_BUTTON_MIDDLE:{
        button = PTR_FLAGS_BUTTON3;
        break;
    }
    }

    if (button) {
        //event->state;
        freerdp_input_send_mouse_event(input, additional_flags | button, (UINT16)event->x, (UINT16)event->y);
//        printf("%s: event->x %f, event->y %f  %i %i\n", (const char *)__func__,
//               event->x, event->y, event->button, event->state);
    }
}
// PTR_FLAGS_DOWN
static gboolean rdp_display_mouse_btn_pressed(GtkWidget *widget, GdkEventButton *event, gpointer user_data)
{
    if (event->type == GDK_BUTTON_PRESS)
        rdp_viewer_handle_mouse_btn_event(widget, event, user_data, PTR_FLAGS_DOWN);

    return TRUE;
}

static gboolean rdp_display_mouse_btn_released(GtkWidget *widget, GdkEventButton *event, gpointer user_data)
{
    if (event->type == GDK_BUTTON_RELEASE)
        rdp_viewer_handle_mouse_btn_event(widget, event, user_data, 0);
    return TRUE;
}

static gboolean rdp_display_wheel_scrolled(GtkWidget *widget G_GNUC_UNUSED, GdkEventScroll  *event, gpointer   user_data)
{
    ExtendedRdpContext* tf = (ExtendedRdpContext*)user_data;
    if (!tf || !tf->is_running)
        return TRUE;

    rdpContext* context = user_data;
    rdpInput *input = context->input;
    //printf("%s event->delta_y %f event->delta_x %f\n", (const char *)__func__, event->delta_y, event->delta_x);
    if ( event->delta_y > 0.5)
        freerdp_input_send_mouse_event(input, PTR_FLAGS_WHEEL | PTR_FLAGS_WHEEL_NEGATIVE | 0x0078, 0, 0);
    else if (event->delta_y < -0.5)
        freerdp_input_send_mouse_event(input, PTR_FLAGS_WHEEL | 0x0078, 0, 0);

    return TRUE;
}

static gboolean rdp_display_event_on_draw(GtkWidget* widget, cairo_t* context, gpointer user_data)
{
    //printf("%s START\n", (const char *)__func__);
//    //TRACE_CALL(__func__);
    ExtendedRdpContext *rdp_contect = user_data;
    if (rdp_contect && rdp_contect->is_running) {

        g_mutex_lock(&rdp_contect->primary_buffer_mutex);

        if (rdp_contect->surface) {

            cairo_set_source_surface(context, rdp_contect->surface, 0, 0);
            cairo_set_operator(context, CAIRO_OPERATOR_OVER);     // Ignore alpha channel from FreeRDP
            cairo_set_antialias(context, CAIRO_ANTIALIAS_FAST);
            cairo_set_tolerance(context, 10);

            cairo_paint(context);
            //cairo_fill(context);
        }
        //printf("%s END\n", (const char *)__func__);

        g_mutex_unlock(&rdp_contect->primary_buffer_mutex);

    } else {
        /* Draw text */
        UINT32 *last_rdp_error_p = (g_object_get_data(G_OBJECT(widget), "last_rdp_error"));
        UINT32 last_rdp_error = *last_rdp_error_p;
        gchar *msg = g_strdup_printf(("Нет соединения. Код: %i %s"), last_rdp_error,
                                     error_to_str(last_rdp_error));

        cairo_select_font_face(context, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
        cairo_set_font_size(context, 15);
        cairo_set_source_rgb(context, 0.1, 0.2, 0.9);

        cairo_move_to(context, 50, 50);
        cairo_show_text(context, msg);

        g_free(msg);
    }

    return TRUE;
}

GtkWidget *rdp_display_create(ExtendedRdpContext *ex_context, UINT32 *last_rdp_error_p)
{
    GtkWidget *rdp_display = gtk_drawing_area_new(); // todo: free memory

    ex_context->rdp_display = rdp_display;

    gtk_widget_add_events(rdp_display, GDK_POINTER_MOTION_MASK | GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK |
                          GDK_SCROLL_MASK);

    g_object_set_data(G_OBJECT(rdp_display), "last_rdp_error", last_rdp_error_p);

    g_signal_connect(rdp_display, "key-press-event", G_CALLBACK(rdp_display_key_pressed), ex_context);
    g_signal_connect(rdp_display, "key-release-event", G_CALLBACK(rdp_display_key_released), ex_context);
    g_signal_connect(rdp_display, "motion-notify-event",G_CALLBACK (rdp_display_mouse_moved), ex_context);
    g_signal_connect(rdp_display, "button-press-event",G_CALLBACK (rdp_display_mouse_btn_pressed), ex_context);
    g_signal_connect(rdp_display, "button-release-event",G_CALLBACK (rdp_display_mouse_btn_released), ex_context);
    g_signal_connect(rdp_display, "scroll-event",G_CALLBACK (rdp_display_wheel_scrolled), ex_context);
    g_signal_connect(rdp_display, "draw", G_CALLBACK(rdp_display_event_on_draw), ex_context);

    return rdp_display;
}