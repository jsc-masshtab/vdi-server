/* -*- Mode: C; c-basic-offset: 4; indent-tabs-mode: nil -*- */
/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2015 Red Hat, Inc.
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
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
 */

#include <config.h>
#include <glib.h>
#include <virt-viewer-util.h>

gboolean doDebug = FALSE;

int main(void)
{
    g_assert(virt_viewer_compare_buildid("1-1", "1-1") == 0);
    g_assert(virt_viewer_compare_buildid("1-1", "1-1.1") < 0);
    g_assert(virt_viewer_compare_buildid("1-1", "1-2") < 0);
    g_assert(virt_viewer_compare_buildid("1-3", "1-2") > 0);
    g_assert(virt_viewer_compare_buildid("2-3", "1-2") > 0);
    g_assert(virt_viewer_compare_buildid("2-3", "3-2") < 0);
    g_assert(virt_viewer_compare_buildid("2-3", "3-4") < 0);
    g_assert(virt_viewer_compare_buildid("4-3", "3-4") > 0);

    g_assert(virt_viewer_compare_buildid("4.0-", "3-4") > 0);
    g_assert(virt_viewer_compare_buildid("4.0-", "3.4-4") > 0);
    g_assert(virt_viewer_compare_buildid(".0-", "3.4-4") < 0);
    g_assert(virt_viewer_compare_buildid("4-", "3-4") > 0);
    g_assert(virt_viewer_compare_buildid("4-3", "3-") > 0);
    g_assert(virt_viewer_compare_buildid("-3", "3-4") < 0);
    g_assert(virt_viewer_compare_buildid("4-3", "-4") > 0);
    g_assert(virt_viewer_compare_buildid("-3", "-4") < 0);
    g_assert(virt_viewer_compare_buildid("4", "3-4") > 0);
    g_assert(virt_viewer_compare_buildid("4-3", "3") > 0);
    g_assert(virt_viewer_compare_buildid("3", "3-4") < 0);
    g_assert(virt_viewer_compare_buildid("4-3", "4") > 0);
    g_assert(virt_viewer_compare_buildid("-3", "-4") < 0);

    /* These trigger runtime warnings */
    g_assert(virt_viewer_compare_buildid("-3", "-") > 0);
    g_assert(virt_viewer_compare_buildid("", "-") == 0);
    g_assert(virt_viewer_compare_buildid("", "") == 0);
    g_assert(virt_viewer_compare_buildid("", NULL) == 0);
    g_assert(virt_viewer_compare_buildid(NULL, NULL) == 0);

    return 0;
}
