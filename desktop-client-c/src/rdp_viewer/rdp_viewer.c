#include <config.h>
#include <gio/gio.h>
#include <gtk/gtk.h>

#include "rdp_viewer.h"


static void
child_watch_cb (GPid     pid,
                gint     status,
                gpointer user_data)
{
    g_message("Child %" G_PID_FORMAT " exited %s", pid,
              g_spawn_check_exit_status (status, NULL) ? "normally" : "abnormally");

    // Free any resources associated with the child process
    g_spawn_close_pid(pid);

    // stop process event loop
    GMainLoop *loop = user_data;
    g_main_loop_quit(loop);
}

void
rdp_viewer_start(const gchar *usename, const gchar *password, gchar *ip, gchar *port)
{
    g_autoptr(GError) error = NULL;

    gchar *username_arg = g_strconcat("/u:", usename, NULL);
    gchar *password_arg = g_strconcat("/p:", password, NULL);

    gchar *adress_arg;
    if (port)
        adress_arg = g_strconcat("/v:", ip, ":", port, NULL);
    else
        adress_arg = g_strconcat("/v:", ip, NULL);

    printf("username_arg test %s\n", username_arg);
    const gchar * const argv[] = { "xfreerdp",
                                   username_arg,
                                   password_arg,
                                   adress_arg,
                                   "/sound:rate:44100,channel:2",
                                   "/gfx-h264:AVC444",
                                   "/video",
                                   "/log-level:INFO",
                                   "/w:1920",
                                   "/h:1080",
                                   "/gdi:hw",
                                   "/multimon",
                                   "+decorations",
                                   "/cert-ignore",
                                   //"/f",
                                   NULL };

    //gint child_stdout, child_stderr;
    GPid child_pid;

    // Spawn child process.
    g_spawn_async(NULL, argv, NULL, G_SPAWN_SEARCH_PATH | G_SPAWN_DO_NOT_REAP_CHILD, NULL,
                             NULL, &child_pid, &error);

    g_free(username_arg);
    g_free(password_arg);
    g_free(adress_arg);

    if (error != NULL) {
        printf("%s: Spawning child failed: %s\n", (const char *)__func__, error->message);
        return;
    }

    GMainLoop *loop = g_main_loop_new(NULL, FALSE);

    // add calback upon the process return
    g_child_watch_add(child_pid, child_watch_cb, loop);

    // start loop
    g_main_loop_run(loop);
}
