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

#ifdef __linux__
#include <X11/Xlib.h>
#endif

#include <config.h>
#include <locale.h>
#include <gio/gio.h>
#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <stdlib.h>

#include "remote-viewer.h"
#include "virt-viewer-util.h"
#include "crashhandler.h"
#include "vdi_api_session.h"

void
setup_logging()
{
    // get ts
    gint64 cur_ts = g_get_real_time();
    gchar *ts_string = g_strdup_printf("%lld", (long long int)cur_ts);
    const gchar *log_dir = "log/";

    // crash handler
    gchar *bt_file_name = g_strconcat(log_dir, ts_string, "_backtrace.txt", NULL);
    install_crash_handler(bt_file_name);

    //error output
    gchar *stderr_file_name = g_strconcat(log_dir, ts_string, "_stderr.txt", NULL);
    freopen(stderr_file_name, "w", stderr);

//    //stdout output
//    gchar *stdout_file_name = g_strconcat(log_dir, ts_string, "_stdout.txt", NULL);
//    freopen(stdout_file_name, "w", stdout);

    // free memory
    g_free(ts_string);
    g_free(bt_file_name);
    g_free(stderr_file_name);
    //g_free(stdout_file_name);
}

void
setup_css()
{
//    gtk_widget_set_name(vdi_manager.label_vdi_online, "label_vdi_online");
//    GtkCssProvider *cssProvider = gtk_css_provider_new();
//    gtk_css_provider_load_from_path(cssProvider, "css_style.css", NULL);
//    gtk_style_context_add_provider(gtk_widget_get_style_context(vdi_manager.label_vdi_online),
//                                       GTK_STYLE_PROVIDER(cssProvider),
//                                       GTK_STYLE_PROVIDER_PRIORITY_USER);
}

int
main(int argc, char **argv)
{
#ifdef NDEBUG // logging errors and traceback in release mode
    setup_logging();
#else

#endif
    // disable stdout buffering
    setbuf(stdout, NULL);

#ifdef __linux__
    XInitThreads();
#endif

    // print version
    printf("APP VERSION %s\n", VERSION);

    // start session
    start_vdi_session();

    // start app
    int ret = 1;
    GApplication *app = NULL;
    virt_viewer_util_init("Veil VDI Тонкий клиент");
    app = G_APPLICATION(remote_viewer_new());

    // css
    setup_css(); // someday in future

    ret = g_application_run(app, argc, argv);

    // free resources
    stop_vdi_session();
    g_object_unref(app);

    return ret;
}
//
/*
 * Local variables:
 *  c-indent-level: 4
 *  c-basic-offset: 4
 *  indent-tabs-mode: nil
 * End:
 */
