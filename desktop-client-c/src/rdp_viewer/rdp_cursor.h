#ifndef RDP_CURSOR_H
#define RDP_CURSOR_H

#include <gtk/gtk.h>

#include <freerdp/freerdp.h>
#include <freerdp/constants.h>
#include <freerdp/gdi/gdi.h>
#include <freerdp/utils/signal.h>

typedef struct{
    rdpPointer pointer;

    BYTE* cursor_image_buffer;
    int test_int;
} ExtendedPointer;

BOOL rdp_register_pointer(rdpGraphics* graphics);

#endif // RDP_CURSOR_H
