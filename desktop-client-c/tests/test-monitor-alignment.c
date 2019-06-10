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
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111NULL307  USA
 */

#include <config.h>
#include <glib.h>
#include <gdk/gdk.h>

#include <virt-viewer-util.h>

/* GLIB_CHECK_VERSION(2, 40, 0) */
#ifndef g_assert_nonnull
#define g_assert_nonnull g_assert
#endif

gboolean doDebug = FALSE;

#define MAX_DISPLAYS 4

typedef struct test_case {
    const guint display_cnt;
    const GdkRectangle *displays_in[MAX_DISPLAYS];
    const GdkRectangle *displays_out[MAX_DISPLAYS];
    const GLogLevelFlags log_level;
    const gchar *messages[3];
} TestCase;

typedef void (*MonitorAlignFunc) (GHashTable *);

static void
test_monitor_align(MonitorAlignFunc monitor_align, const TestCase *test_cases, const guint cases)
{
    guint i;

    for (i = 0; i < cases; i++) {
        GdkRectangle *displays_in[MAX_DISPLAYS];
        guint j;
        GHashTable *displays = g_hash_table_new_full(g_direct_hash, g_direct_equal, NULL, g_free);
        g_assert_nonnull(displays);
        for (j = 0; j < test_cases[i].display_cnt; j++) {
            if (test_cases[i].displays_in[j] != NULL) {
                GdkRectangle *monitor = g_new(GdkRectangle, 1);
                *monitor = *test_cases[i].displays_in[j];
                displays_in[j] = monitor;
            } else {
                displays_in[j] = NULL;
            }
            g_hash_table_insert(displays, GUINT_TO_POINTER(j), displays_in[j]);
        }
        for (j = 0; j < G_N_ELEMENTS(test_cases[i].messages) && test_cases[i].messages[j]; j++) {
            g_test_expect_message(NULL, test_cases[i].log_level, test_cases[i].messages[j]);
        }
        monitor_align(displays);
        g_test_assert_expected_messages();
        for (j = 0; j < test_cases[i].display_cnt; j++) {
            if (displays_in[j] == NULL) {
                g_assert_null(test_cases[i].displays_out[j]);
                continue;
            }
            g_assert_cmpint(displays_in[j]->x, ==, test_cases[i].displays_out[j]->x);
            g_assert_cmpint(displays_in[j]->y, ==, test_cases[i].displays_out[j]->y);
            g_assert_cmpint(displays_in[j]->width, ==, test_cases[i].displays_out[j]->width);
            g_assert_cmpint(displays_in[j]->height, ==, test_cases[i].displays_out[j]->height);
        }
        g_hash_table_unref(displays);
    }
}

static void
test_monitor_shift(void)
{
    const GdkRectangle rects[] = {
                                    {4240, 0, 1280, 1024},
                                    {0, 0, 1280, 1024},
                                    {100, 1000, 1024, 768},
                                    {420, 680, 1024, 768},
                                    {320, 320, 1024, 768},
                                    {0, 1000, 1024, 768},
                                    {4140, 0, 1280, 1024},
                                    {220, 320, 1024, 768},
                                    {320, 680, 1024, 768},
                                 };
    const TestCase test_cases[] = {
        {
            0, {NULL}, {NULL}, 0, {NULL}
        },{
            1,
            {NULL},
            {NULL},
            G_LOG_LEVEL_CRITICAL,
            {"*assertion 'display != NULL' failed"}
        },{
            2,
            {NULL, &rects[0]},
            {NULL, &rects[0]},
            G_LOG_LEVEL_CRITICAL,
            {"*assertion 'display != NULL' failed"}
        },{
            2,
            {&rects[2], NULL},
            {&rects[2], NULL},
            G_LOG_LEVEL_CRITICAL,
            {"*assertion 'display != NULL' failed"}
        },{
            2,
            {&rects[0], &rects[0]},
            {&rects[1], &rects[1]},
            0,
            {NULL}
        },{
            2,
            {&rects[0], &rects[1]},
            {&rects[0], &rects[1]},
            0,
            {NULL}
        },{
            4,
            {&rects[0], &rects[2], &rects[4], &rects[3]},
            {&rects[6], &rects[5], &rects[7], &rects[8]},
            0,
            {NULL}
        },
    };

    test_monitor_align(virt_viewer_shift_monitors_to_origin, test_cases, G_N_ELEMENTS(test_cases));
}

static void
test_monitor_align_linear(void)
{
    const GdkRectangle rects[] = {
                                    {0, 0, 1280, 1024},
                                    {100, 1000, 1024, 768},
                                    {1280, 0, 1024, 768},
                                    {0, 0, 1024, 768},
                                    {3328, 0, 1024, 768},
                                    {1024, 0, 1280, 1024},
                                    {2304, 0, 1024, 768},
                                 };
    const TestCase test_cases[] = {
        {
            0, {NULL}, {NULL}, 0, {NULL}
        },{
            1,
            {NULL},
            {NULL},
            G_LOG_LEVEL_CRITICAL,
            {"*assertion 'rect != NULL' failed"}
        },{
            2,
            {NULL, &rects[1]},
            {NULL, &rects[1]},
            G_LOG_LEVEL_CRITICAL,
            {
                "*displays_cmp: assertion 'm1 != NULL && m2 != NULL' failed",
                "*assertion 'rect != NULL' failed"
            }
        },{
            3,
            {&rects[1], NULL, &rects[0]},
            {&rects[3], NULL, &rects[0]},
            G_LOG_LEVEL_CRITICAL,
            {
                "*displays_cmp: assertion 'm1 != NULL && m2 != NULL' failed",
                "*displays_cmp: assertion 'm1 != NULL && m2 != NULL' failed",
                "*assertion 'rect != NULL' failed"
            }
        },{
            2,
            {&rects[0], &rects[1]},
            {&rects[0], &rects[2]},
            0,
            {NULL}
        },{
            2,
            {&rects[1], &rects[0]},
            {&rects[2], &rects[0]},
            0,
            {NULL}
        },{
            4,
            {&rects[2], &rects[3], &rects[0], &rects[1]},
            {&rects[4], &rects[3], &rects[5], &rects[6]},
            0,
            {NULL}
        },
    };

    test_monitor_align(virt_viewer_align_monitors_linear, test_cases, G_N_ELEMENTS(test_cases));
}

int main(int argc, char* argv[])
{
    gtk_init_check(&argc, &argv);
    g_test_init(&argc, &argv, NULL);

    g_test_add_func("/virt-viewer-util/monitor-shift", test_monitor_shift);
    g_test_add_func("/virt-viewer-util/monitor-align-linear", test_monitor_align_linear);

    return g_test_run();
}
