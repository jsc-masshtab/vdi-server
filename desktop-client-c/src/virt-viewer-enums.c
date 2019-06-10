
/* Generated data (by glib-mkenums) */

/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2007-2012 Red Hat, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Marc-André Lureau <marcandre.lureau@redhat.com>
 */

#include "virt-viewer-enums.h"

#include "virt-viewer-display.h"

GType
virt_viewer_display_show_hint_flags_get_type (void)
{
  static volatile gsize g_define_type_id__volatile = 0;

  if (g_once_init_enter (&g_define_type_id__volatile))
    {
      static const GFlagsValue values[] = {
        { VIRT_VIEWER_DISPLAY_SHOW_HINT_READY, "VIRT_VIEWER_DISPLAY_SHOW_HINT_READY", "ready" },
        { VIRT_VIEWER_DISPLAY_SHOW_HINT_DISABLED, "VIRT_VIEWER_DISPLAY_SHOW_HINT_DISABLED", "disabled" },
        { VIRT_VIEWER_DISPLAY_SHOW_HINT_SET, "VIRT_VIEWER_DISPLAY_SHOW_HINT_SET", "set" },
        { 0, NULL, NULL }
      };
      GType g_define_type_id =
        g_flags_register_static (g_intern_static_string ("VirtViewerDisplayShowHintFlags"), values);
      g_once_init_leave (&g_define_type_id__volatile, g_define_type_id);
    }

  return g_define_type_id__volatile;
}


/* Generated data ends here */

