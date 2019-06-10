/* -*- Mode: C; c-basic-offset: 4; indent-tabs-mode: nil -*- */
/*
 * Virt Viewer: A virtual machine console viewer
 *
 * Copyright (C) 2016 Red Hat, Inc.
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
#include <glib-object.h>
#include <gtk/gtk.h>

#include "virt-viewer-app.h"

G_BEGIN_DECLS

#define VIRT_VIEWER_TEST_TYPE virt_viewer_test_get_type()
#define VIRT_VIEWER_TEST(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), VIRT_VIEWER_TEST_TYPE, VirtViewerTest))
#define VIRT_VIEWER_TEST_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST ((klass), VIRT_VIEWER_TEST_TYPE, VirtViewerTestClass))
#define VIRT_VIEWER_TEST_IS(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), VIRT_VIEWER_TEST_TYPE))
#define VIRT_VIEWER_TEST_IS_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE ((klass), VIRT_VIEWER_TEST_TYPE))
#define VIRT_VIEWER_TEST_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), VIRT_VIEWER_TEST_TYPE, VirtViewerTestClass))

typedef struct {
    VirtViewerApp parent;
} VirtViewerTest;

typedef struct {
    VirtViewerAppClass parent_class;
} VirtViewerTestClass;

GType virt_viewer_test_get_type (void);

G_DEFINE_TYPE (VirtViewerTest, virt_viewer_test, VIRT_VIEWER_TYPE_APP)

VirtViewerTest *virt_viewer_test_new (void);

G_END_DECLS

static void
virt_viewer_test_class_init (VirtViewerTestClass *klass G_GNUC_UNUSED)
{
}

static void
virt_viewer_test_init(VirtViewerTest *self G_GNUC_UNUSED)
{
}

static void
test_hotkeys_good(void)
{
    const gchar *hotkeys[] = {
        "toggle-fullscreen=shift+f11",
        "release-cursor=shift+f12,secure-attention=ctrl+shift+b",
        "smartcard-insert=shift+I,smartcard-remove=shift+R",
    };

    guint i;

    VirtViewerTest *viewer = g_object_new(VIRT_VIEWER_TEST_TYPE, NULL);
    VirtViewerApp *app = VIRT_VIEWER_APP(viewer);
    for (i = 0; i < G_N_ELEMENTS(hotkeys); i++) {
        virt_viewer_app_set_hotkeys(app, hotkeys[i]);
    }
    g_object_unref(viewer);
}

static void
test_hotkeys_bad(void)
{
    const struct {
        const gchar *hotkey_str;
        const GLogLevelFlags log_level;
        const gchar *message;
    } hotkeys[] = {
        {
            "no_value",
            G_LOG_LEVEL_WARNING,
            "missing value for key 'no_value'"
        },{
            "smartcard-insert=",
            G_LOG_LEVEL_WARNING,
            "missing value for key 'smartcard-insert'"
        },{
            "toggle-fullscreen=A,unknown_command=B",
            G_LOG_LEVEL_WARNING,
            "Unknown hotkey command unknown_command"
        },{
            "secure-attention=value",
            G_LOG_LEVEL_WARNING,
            "Invalid value 'value' for key 'secure-attention'"
        },
    };

    guint i;

    VirtViewerTest *viewer = g_object_new(VIRT_VIEWER_TEST_TYPE, NULL);
    VirtViewerApp *app = VIRT_VIEWER_APP(viewer);
    for (i = 0; i < G_N_ELEMENTS(hotkeys); i++) {
        g_test_expect_message(G_LOG_DOMAIN, hotkeys[i].log_level, hotkeys[i].message);
        virt_viewer_app_set_hotkeys(app, hotkeys[i].hotkey_str);
        g_test_assert_expected_messages();
    }
    g_object_unref(viewer);
}

int main(int argc, char* argv[])
{
    gtk_init_check(&argc, &argv);
    g_test_init(&argc, &argv, NULL);

    g_test_add_func("/virt-viewer/good-hotkeys", test_hotkeys_good);
    g_test_add_func("/virt-viewer/bad-hotkeys", test_hotkeys_bad);

    return g_test_run();
}
