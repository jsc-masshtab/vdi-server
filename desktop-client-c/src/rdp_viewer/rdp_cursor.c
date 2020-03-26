// Черновой вариант. Не продумана нормально передача данных в update_cursor_callback

#include "rdp_client.h"

/* Pointer Class */
static BOOL xf_Pointer_New(rdpContext* context, rdpPointer* pointer)
{
    //printf("%s\n", (const char *)__func__);
    //ExtendedRdpContext *ex_rdp_context = (ExtendedRdpContext*)context;
    ExtendedPointer *ex_pointer = (ExtendedPointer *)pointer;

    UINT32 cursor_format = PIXEL_FORMAT_RGBA32; // todo: random pick. think about this

    // create buffer
    size_t size = pointer->height * pointer->width * GetBytesPerPixel(cursor_format);

    ex_pointer->cursor_image_buffer = malloc(size * sizeof(BYTE));

    if (!freerdp_image_copy_from_pointer_data(
            ex_pointer->cursor_image_buffer, cursor_format,
            0, 0, 0, pointer->width, pointer->height,
            pointer->xorMaskData, pointer->lengthXorMask,
            pointer->andMaskData, pointer->lengthAndMask,
            pointer->xorBpp, &context->gdi->palette)) {

        return FALSE;
    }

    static int counter = 0;
    ex_pointer->test_int = counter++;
    printf("%s ex_pointer->test_int: %i\n", (const char *)__func__,  ex_pointer->test_int);

    return TRUE;
}

static void xf_Pointer_Free(rdpContext* context G_GNUC_UNUSED, rdpPointer* pointer)
{
    //ExtendedRdpContext* ex_rdp_context = (ExtendedRdpContext*)context;
    ExtendedPointer *ex_pointer = (ExtendedPointer *)pointer;

    free(ex_pointer->cursor_image_buffer);
}

static BOOL xf_Pointer_Set(rdpContext* context, const rdpPointer* pointer)
{
    //printf("%s\n", (const char *)__func__);
    ExtendedRdpContext* ex_rdp_context = (ExtendedRdpContext*)context;
    const ExtendedPointer *ex_pointer = (const ExtendedPointer *)pointer;
    //printf("%s ex_pointer->test_int: %i\n", (const char *)__func__,  ex_pointer->test_int);

    // create pix_buff. used for creating ciursor
    UINT32 cursor_format = PIXEL_FORMAT_RGBA32;
    UINT32 rowstride = pointer->width * GetBytesPerPixel(cursor_format);
    GdkPixbuf *pix_buff = gdk_pixbuf_new_from_data(ex_pointer->cursor_image_buffer,
                         GDK_COLORSPACE_RGB,
                         TRUE,
                         8,
                         (int)pointer->width, (int)pointer->height,
                         (int)rowstride,
                         NULL, NULL);

    // create cursor
    GdkDisplay *display = gdk_display_get_default();
    if (!display) {
        return TRUE;
    }

    g_mutex_lock(&ex_rdp_context->cursor_mutex);
    if (ex_rdp_context->gdk_cursor)
        g_object_unref(ex_rdp_context->gdk_cursor);
    ex_rdp_context->gdk_cursor = gdk_cursor_new_from_pixbuf(display, pix_buff, (gint)pointer->xPos, (gint)pointer->yPos);
    g_mutex_unlock(&ex_rdp_context->cursor_mutex);

    g_object_unref(pix_buff);

    // invoke callback to set cursor in main (gui) thread.
    g_idle_add((GSourceFunc)ex_rdp_context->update_cursor_callback, context);
    return TRUE;
}

static BOOL xf_Pointer_SetNull(rdpContext* context G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    return TRUE;
}

static BOOL xf_Pointer_SetDefault(rdpContext* context G_GNUC_UNUSED)
{
    printf("%s\n", (const char *)__func__);
    return TRUE;
}

static BOOL xf_Pointer_SetPosition(rdpContext* context G_GNUC_UNUSED, UINT32 x, UINT32 y)
{
    printf("%s x %i y %i \n", (const char *)__func__, x, y);
    return TRUE;
}

BOOL rdp_register_pointer(rdpGraphics* graphics)
{
    rdpPointer* pointer = NULL;

    if (!(pointer = (rdpPointer*) calloc(1, sizeof(rdpPointer))))
        return FALSE;

    pointer->size = sizeof(ExtendedPointer);
    pointer->New = xf_Pointer_New;
    pointer->Free = xf_Pointer_Free;
    pointer->Set = xf_Pointer_Set;
    pointer->SetNull = xf_Pointer_SetNull;
    pointer->SetDefault = xf_Pointer_SetDefault;
    pointer->SetPosition = xf_Pointer_SetPosition;

    graphics_register_pointer(graphics, pointer);

    free(pointer);

    return TRUE;
}
