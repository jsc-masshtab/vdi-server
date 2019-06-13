/*
 * Remote Viewer: A spice/vnc client based on virt-viewer
 *
 * Copyright (C) 2011-2012 Red Hat, Inc.
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

#include <config.h>
#include <locale.h>
#include <gio/gio.h>
#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <stdlib.h>

#include "remote-viewer.h"
#include "virt-viewer-util.h"
#include "crashhandler.h"

int
main(int argc, char **argv)
{
    // get ts
    gint64 cur_ts = g_get_real_time();
    gchar *ts_string = g_strdup_printf("%lld", cur_ts);
    const gchar *log_dir = "log/";

    // crash handler
    gchar *bt_file_name = g_strconcat(log_dir, ts_string, "_backtrace.txt", NULL);
    installHandler(bt_file_name);

    //error output
    gchar *stderr_file_name = g_strconcat(log_dir, ts_string, "_stderr.txt", NULL);
    freopen(stderr_file_name, "w", stderr);

    // free memory
    g_free(ts_string);
    g_free(bt_file_name);
    g_free(stderr_file_name);

    // app
    int ret = 1;
    GApplication *app = NULL;

    virt_viewer_util_init("Veil VDI Тонкий клиент");
    app = G_APPLICATION(remote_viewer_new());

    ret = g_application_run(app, argc, argv);
    g_object_unref(app);
    return ret;
}

/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
