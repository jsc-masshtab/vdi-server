/**
 * FreeRDP: A Remote Desktop Protocol Implementation
 * GTK GUI
 * Solomin a.solomin@mashtab.otg
 */


//HGDI_RGN cinvalid = gdi->primary->hdc->hwnd->cinvalid;
//int ninvalid = gdi->primary->hdc->hwnd->ninvalid;

//int x1 = cinvalid[0].x;
//int y1 = cinvalid[0].y;
//int x2 = cinvalid[0].x + cinvalid[0].w;
//int y2 = cinvalid[0].y + cinvalid[0].h;

//for (int i = 0; i < ninvalid; i++)
//{
//    x1 = MIN(x1, cinvalid[i].x);
//    y1 = MIN(y1, cinvalid[i].y);
//    x2 = MAX(x2, cinvalid[i].x + cinvalid[i].w);
//    y2 = MAX(y2, cinvalid[i].y + cinvalid[i].h);
//}



#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <errno.h>
#include <stdio.h>
#include <string.h>

#include <freerdp/freerdp.h>
#include <freerdp/constants.h>
#include <freerdp/gdi/gdi.h>
#include <freerdp/utils/signal.h>

#include <freerdp/client/file.h>
#include <freerdp/client/cmdline.h>
#include <freerdp/client/cliprdr.h>
#include <freerdp/client/channels.h>
#include <freerdp/channels/channels.h>

#include <freerdp/locale/keyboard.h>

#include <freerdp/error.h>

#include <winpr/crt.h>
#include <winpr/synch.h>
#include <freerdp/log.h>

#include <gio/gio.h>
#include <gtk/gtk.h>

#include "rdp_channels.h"
#include "rdp_client.h"
#include "rdp_cursor.h"

#include "virt-viewer-util.h"

#define PROGRAMM_NAME "rdp_gtk_client"
#define TAG CLIENT_TAG(PROGRAMM_NAME)


static DWORD WINAPI rdp_client_thread_proc(ExtendedRdpContext *tf);
static int rdp_client_entry(RDP_CLIENT_ENTRY_POINTS* pEntryPoints);


rdpContext* rdp_client_create_context()
{
    RDP_CLIENT_ENTRY_POINTS clientEntryPoints;
    rdpContext* context;
    rdp_client_entry(&clientEntryPoints);
    context = freerdp_client_context_new(&clientEntryPoints);
    return context;
}


void rdp_client_set_credentials(ExtendedRdpContext *ex_context,
                                const gchar *usename, const gchar *password, gchar *ip, int port)
{
    ex_context->usename = g_strdup(usename);
    ex_context->password = g_strdup(password);
    ex_context->ip = g_strdup(ip);
    ex_context->port = port;
}
//===============================Thread for client routine==================================
void rdp_client_routine(GTask   *task,
                 gpointer       source_object G_GNUC_UNUSED,
                 gpointer       task_data G_GNUC_UNUSED,
                 GCancellable  *cancellable G_GNUC_UNUSED)
{
    int rc = -1;
    int status;
    rdpContext *context = g_task_get_task_data(task);

    ExtendedRdpContext* tf = (ExtendedRdpContext*)context;
    g_mutex_lock(&tf->rdp_routine_mutex);

    if (!context)
        goto fail;

    // /v:192.168.20.104 /u:solomin /p:5555 -clipboard /sound:rate:44100,channel:2 /cert-ignore
    //int argc = 8;
    char* argv[] = {
        g_strdup(PROGRAMM_NAME),
        g_strdup_printf("/v:%s", tf->ip),
        g_strdup_printf("/u:%s", tf->usename),
        g_strdup_printf("/p:%s", tf->password),
        g_strdup("-clipboard"),
        g_strdup("/sound:rate:44100,channel:2"),
        g_strdup("/cert-ignore"),
        NULL
    };
    int argc = sizeof(argv) / sizeof(char*) - 1;
    printf("sizeof(argv): %lu, argc: %i", sizeof(argv), argc);

    status = freerdp_client_settings_parse_command_line(context->settings, argc, argv, FALSE);
    status = freerdp_client_settings_command_line_status_print(context->settings, status, argc, argv);

    for(int i = 0; i < argc; ++i) {
        g_free(argv[i]);
    }

    if (status) {
        g_mutex_unlock(&tf->rdp_routine_mutex);
        return;
    }

    if (freerdp_client_start(context) != 0)
        goto fail;

    tf->is_running = TRUE;

    rc = (int)rdp_client_thread_proc(tf);

    // stopping
    if (freerdp_client_stop(context) != 0)
        rc = -1;

fail:
    //freerdp_client_context_free(context);
    printf("%s: g_mutex_unlock\n", (const char *)__func__);
    g_mutex_unlock(&tf->rdp_routine_mutex);
    tf->is_running = FALSE;
}

//static BOOL update_send_synchronize(rdpContext* context)
//{
//    //printf("%s\n", (const char *)__func__);
//}

/* This function is called whenever a new frame starts.
 * It can be used to reset invalidated areas. */
static BOOL rdp_begin_paint(rdpContext* context)
{
    //printf("%s\n", (const char *)__func__);
	rdpGdi* gdi = context->gdi;
	gdi->primary->hdc->hwnd->invalid->null = TRUE;

    // Lock mutex to protect buffer
    ExtendedRdpContext* tf = (ExtendedRdpContext*)context;

    g_mutex_lock(&tf->primary_buffer_mutex);
	return TRUE;
}

/* This function is called when the library completed composing a new
 * frame. Read out the changed areas and blit them to your output device.
 * The image buffer will have the format specified by gdi_init
 */
static BOOL rdp_end_paint(rdpContext* context)
{
    //printf("%s\n", (const char *)__func__);

    rdpGdi* gdi = context->gdi;
    ExtendedRdpContext* tf = (ExtendedRdpContext*)context;

    if (gdi->primary->hdc->hwnd->invalid->null) {
        g_mutex_unlock(&tf->primary_buffer_mutex);
        return TRUE;
    }

    if (gdi->primary->hdc->hwnd->ninvalid < 1) {
        g_mutex_unlock(&tf->primary_buffer_mutex);
        return TRUE;
    }

//   printf("STATS: %i %i %i %i \n", gdi->primary->hdc->hwnd->invalid->x,
//           gdi->primary->hdc->hwnd->invalid->y,
//           gdi->primary->hdc->hwnd->invalid->w,
//           gdi->primary->hdc->hwnd->invalid->h);


    gdi->primary->hdc->hwnd->invalid->null = TRUE;
    gdi->primary->hdc->hwnd->ninvalid = 0;

    g_mutex_unlock(&tf->primary_buffer_mutex);
    return TRUE;
}

/* This function is called to output a System BEEP */
static BOOL rdp_play_sound(rdpContext* context, const PLAY_SOUND_UPDATE* play_sound)
{
	/* TODO: Implement */
	WINPR_UNUSED(context);
	WINPR_UNUSED(play_sound);
	return TRUE;
}

/* This function is called to update the keyboard indocator LED */
static BOOL rdp_keyboard_set_indicators(rdpContext* context, UINT16 led_flags)
{
	/* TODO: Set local keyboard indicator LED status */
	WINPR_UNUSED(context);
	WINPR_UNUSED(led_flags);
	return TRUE;
}

/* This function is called to set the IME state */
static BOOL rdp_keyboard_set_ime_status(rdpContext* context, UINT16 imeId, UINT32 imeState,
                                       UINT32 imeConvMode)
{
	if (!context)
		return FALSE;

	WLog_WARN(TAG,
	          "KeyboardSetImeStatus(unitId=%04" PRIx16 ", imeState=%08" PRIx32
	          ", imeConvMode=%08" PRIx32 ") ignored",
	          imeId, imeState, imeConvMode);
	return TRUE;
}
// XInitThreads  GDK_SYNCHRONIZE
/* Called before a connection is established.
 * Set all configuration options to support and load channels here. */
static BOOL rdp_pre_connect(freerdp* instance)
{
    printf("%s\n", (const char *)__func__);
	rdpSettings* settings;
	settings = instance->settings;
	/* Optional OS identifier sent to server */
    settings->OsMajorType = OSMAJORTYPE_UNSPECIFIED;
    settings->OsMinorType = OSMINORTYPE_UNSPECIFIED;


    settings->BitmapCacheEnabled = false;
    settings->OffscreenSupportLevel = false;
//    settings->OffscreenCacheSize;    /* 2817 */
//    settings->OffscreenCacheEntries; /* 2818 */
    settings->CompressionEnabled = false;

//    settings->OrderSupport[NEG_DSTBLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_PATBLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_SCRBLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_OPAQUE_RECT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_DRAWNINEGRID_INDEX] = TRUE;

//    settings->OrderSupport[NEG_MULTIDSTBLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_MULTIPATBLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_MULTISCRBLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_MULTIOPAQUERECT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_MULTI_DRAWNINEGRID_INDEX] = TRUE;
//    settings->OrderSupport[NEG_LINETO_INDEX] = TRUE;
//    settings->OrderSupport[NEG_POLYLINE_INDEX] = TRUE;
////    settings->OrderSupport[NEG_MEMBLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_MEM3BLT_INDEX] = TRUE;
//    settings->OrderSupport[NEG_SAVEBITMAP_INDEX] = TRUE;

//    settings->OrderSupport[NEG_GLYPH_INDEX_INDEX] = TRUE;
//    settings->OrderSupport[NEG_FAST_INDEX_INDEX] = TRUE;
//    settings->OrderSupport[NEG_FAST_GLYPH_INDEX] = TRUE;
//    settings->OrderSupport[NEG_POLYGON_SC_INDEX] = TRUE;
//    settings->OrderSupport[NEG_POLYGON_CB_INDEX] = TRUE;
//    settings->OrderSupport[NEG_ELLIPSE_SC_INDEX] = TRUE;
//    settings->OrderSupport[NEG_ELLIPSE_CB_INDEX] = TRUE;



	/* settings->OrderSupport is initialized at this point.
	 * Only override it if you plan to implement custom order
	 * callbacks or deactiveate certain features. */
	/* Register the channel listeners.
	 * They are required to set up / tear down channels if they are loaded. */
    PubSub_SubscribeChannelConnected(instance->context->pubSub, rdp_OnChannelConnectedEventHandler);
    PubSub_SubscribeChannelDisconnected(instance->context->pubSub,
                                        rdp_OnChannelDisconnectedEventHandler);

	/* Load all required plugins / channels / libraries specified by current
	 * settings. */
	if (!freerdp_client_load_addins(instance->context->channels, instance->settings))
		return FALSE;

    // its required for key event sending
    freerdp_keyboard_init(instance->context->settings->KeyboardLayout);

	/* TODO: Any code your client requires */
	return TRUE;
}

/* Called after a RDP connection was successfully established.
 * Settings might have changed during negociation of client / server feature
 * support.
 *
 * Set up local framebuffers and paing callbacks.
 * If required, register pointer callbacks to change the local mouse cursor
 * when hovering over the RDP window
 */
static BOOL rdp_post_connect(freerdp* instance)
{
    printf("%s\n", (const char *)__func__);
    if (!gdi_init(instance, PIXEL_FORMAT_RGB16)) // PIXEL_FORMAT_RGBA32
		return FALSE;

    if (!rdp_register_pointer(instance->context->graphics))
        return FALSE;

    instance->update->BeginPaint = rdp_begin_paint;
    instance->update->EndPaint = rdp_end_paint;
    instance->update->PlaySound = rdp_play_sound;
    instance->update->SetKeyboardIndicators = rdp_keyboard_set_indicators;
    instance->update->SetKeyboardImeStatus = rdp_keyboard_set_ime_status;
    //instance->update->Synchronize = update_send_synchronize;

    // create image surface. TODO: must be recreated on resize
    ExtendedRdpContext* tf = (ExtendedRdpContext*)instance->context;
    rdpGdi* gdi = tf->context.gdi;

    g_mutex_lock(&tf->primary_buffer_mutex);

    cairo_format_t cairo_format = CAIRO_FORMAT_RGB16_565;
    printf("%s W: %i H: %i\n", (const char *)__func__, gdi->width, gdi->height);
    int stride = cairo_format_stride_for_width(cairo_format, gdi->width);
    tf->surface = cairo_image_surface_create_for_data((unsigned char*)gdi->primary_buffer,
                                                      cairo_format, gdi->width, gdi->height, stride);

    g_mutex_unlock(&tf->primary_buffer_mutex);

	return TRUE;
}

/* This function is called whether a session ends by failure or success.
 * Clean up everything allocated by pre_connect and post_connect.
 */
static void rdp_post_disconnect(freerdp* instance)
{
    printf("%s\n", (const char *)__func__);

	if (!instance)
		return;

	if (!instance->context)
		return;

    ExtendedRdpContext* context = (ExtendedRdpContext*)instance->context;
    PubSub_UnsubscribeChannelConnected(instance->context->pubSub,
                                       rdp_OnChannelConnectedEventHandler);
    PubSub_UnsubscribeChannelDisconnected(instance->context->pubSub,
                                          rdp_OnChannelDisconnectedEventHandler);

    g_mutex_lock(&context->primary_buffer_mutex);
    cairo_surface_destroy(context->surface);
    context->surface = NULL;
    g_mutex_unlock(&context->primary_buffer_mutex);

    *(context->last_rdp_error_p) = freerdp_get_last_error(instance->context);
    printf("%s last_error_code: %u\n", (const char *)__func__, *context->last_rdp_error_p);
//    if (last_error_code == ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION) {
//        printf("%s ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION\n", (const char *)__func__);
//    }
    //rdp_print_errinfo();

	gdi_free(instance);
	/* TODO : Clean up custom stuff */
}

/* RDP main loop.
 * Connects RDP, loops while running and handles event and dispatch, cleans up
 * after the connection ends. */
static DWORD WINAPI rdp_client_thread_proc(ExtendedRdpContext* tf)
{
    freerdp* instance = (freerdp*)tf->context.instance;
	DWORD nCount;
	DWORD status;
	HANDLE handles[64];

	if (!freerdp_connect(instance))
	{
		WLog_ERR(TAG, "connection failure");
		return 0;
	}

    while (!freerdp_shall_disconnect(instance))
	{
		nCount = freerdp_get_event_handles(instance->context, &handles[0], 64);

		if (nCount == 0)
		{
			WLog_ERR(TAG, "%s: freerdp_get_event_handles failed", __FUNCTION__);
			break;
		}

		status = WaitForMultipleObjects(nCount, handles, FALSE, 100);

		if (status == WAIT_FAILED)
		{
			WLog_ERR(TAG, "%s: WaitForMultipleObjects failed with %" PRIu32 "", __FUNCTION__,
			         status);
			break;
		}

		if (!freerdp_check_event_handles(instance->context))
		{
			if (freerdp_get_last_error(instance->context) == FREERDP_ERROR_SUCCESS)
				WLog_ERR(TAG, "Failed to check FreeRDP event handles");

			break;
		}
	}

    BOOL res = freerdp_disconnect(instance);
    printf("diss conn res: %i\n", res);
	return 0;
}


/* Optional global initializer.
 * Here we just register a signal handler to print out stack traces
 * if available. */
static BOOL rdp_client_global_init(void)
{
	if (freerdp_handle_signals() != 0)
		return FALSE;

	return TRUE;
}

/* Optional global tear down */
static void rdp_client_global_uninit(void)
{
}

static int rdp_logon_error_info(freerdp* instance, UINT32 data, UINT32 type)
{
    ExtendedRdpContext* tf;
	const char* str_data = freerdp_get_logon_error_info_data(data);
	const char* str_type = freerdp_get_logon_error_info_type(type);

	if (!instance || !instance->context)
		return -1;

    tf = (ExtendedRdpContext*)instance->context;
	WLog_INFO(TAG, "Logon Error Info %s [%s]", str_data, str_type);
	WINPR_UNUSED(tf);

	return 1;
}

static BOOL rdp_client_new(freerdp* instance, rdpContext* context)
{
    ExtendedRdpContext* tf = (ExtendedRdpContext*)context;
    printf("%s: tf->test_int: %i\n", (const char *)__func__, tf->test_int);

	if (!instance || !context)
		return FALSE;

    instance->PreConnect = rdp_pre_connect;
    instance->PostConnect = rdp_post_connect;
    instance->PostDisconnect = rdp_post_disconnect;
	instance->Authenticate = client_cli_authenticate;
	instance->GatewayAuthenticate = client_cli_gw_authenticate;
	instance->VerifyCertificateEx = client_cli_verify_certificate_ex;
	instance->VerifyChangedCertificateEx = client_cli_verify_changed_certificate_ex;
    instance->LogonErrorInfo = rdp_logon_error_info;
	/* TODO: Client display set up */

	return TRUE;
}

static void rdp_client_free(freerdp* instance G_GNUC_UNUSED, rdpContext* context)
{
    printf("%s\n", (const char *)__func__);
    //ExtendedRdpContext* tf = (ExtendedRdpContext*)instance->context;

	if (!context)
		return;

    // some clean. todo: use safe string free
    ExtendedRdpContext* ex_context = (ExtendedRdpContext*)context;
//    ex_context->usename;
//    ex_context->password;
//    ex_context->ip;
    free_memory_safely(&ex_context->usename);
    free_memory_safely(&ex_context->password);
    free_memory_safely(&ex_context->ip);
}

static int rdp_client_start(rdpContext* context)
{
	/* TODO: Start client related stuff */
    ExtendedRdpContext* tf = (ExtendedRdpContext*)context;
    printf("%s: %i\n", (const char *)__func__, tf->test_int);

    g_mutex_init(&tf->primary_buffer_mutex); // todo: clear

	return 0;
}

static int rdp_client_stop(rdpContext* context)
{
	/* TODO: Stop client related stuff */
    ExtendedRdpContext* tf = (ExtendedRdpContext*)context;
    printf("%s: %i\n", (const char *)__func__, tf->test_int);

    g_mutex_lock(&tf->primary_buffer_mutex);
    g_mutex_unlock(&tf->primary_buffer_mutex);
    g_mutex_clear(&tf->primary_buffer_mutex);

	return 0;
}

static int rdp_client_entry(RDP_CLIENT_ENTRY_POINTS* pEntryPoints)
{
    ZeroMemory(pEntryPoints, sizeof(RDP_CLIENT_ENTRY_POINTS));
    pEntryPoints->Version = RDP_CLIENT_INTERFACE_VERSION;
    pEntryPoints->Size = sizeof(RDP_CLIENT_ENTRY_POINTS_V1);
    pEntryPoints->GlobalInit = rdp_client_global_init;
    pEntryPoints->GlobalUninit = rdp_client_global_uninit;
    pEntryPoints->ContextSize = sizeof(ExtendedRdpContext);
    pEntryPoints->ClientNew = rdp_client_new;
    pEntryPoints->ClientFree = rdp_client_free;
    pEntryPoints->ClientStart = rdp_client_start;
    pEntryPoints->ClientStop = rdp_client_stop;
    return 0;
}
