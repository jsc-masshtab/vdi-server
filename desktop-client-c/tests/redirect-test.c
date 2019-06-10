/*
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
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

/* This small program test redirection inside Remote Viewer
 */

#include <config.h>

/* force assert to be compiler, on Windows are usually disabled */
#undef NDEBUG
#undef DEBUG
#define DEBUG 1

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <io.h>
#include <glib.h>

static BOOL has_console = FALSE;
static HANDLE h_console = INVALID_HANDLE_VALUE;
static FILE *log_f = NULL;
static int num_test = 0;

static int
has_inherit(HANDLE h)
{
    DWORD flags;
    if (GetHandleInformation(h, &flags))
        return flags & HANDLE_FLAG_INHERIT;
    return 0;
}

static BOOL is_handle_valid(HANDLE h)
{
    if (h == INVALID_HANDLE_VALUE || h == NULL)
        return FALSE;

    DWORD flags;
    return GetHandleInformation(h, &flags);
}

static int
called_test(int argc G_GNUC_UNUSED, char **argv)
{
    STARTUPINFO si;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    GetStartupInfo(&si);
    fprintf(log_f, "handles %p %p - %p %p %d %d\n", si.hStdOutput, si.hStdError,
            GetStdHandle(STD_OUTPUT_HANDLE), GetStdHandle(STD_ERROR_HANDLE),
            has_inherit(GetStdHandle(STD_OUTPUT_HANDLE)), has_inherit(GetStdHandle(STD_ERROR_HANDLE)));

    /* Get redirection from parent */
    BOOL out_valid = is_handle_valid(GetStdHandle(STD_OUTPUT_HANDLE));
    BOOL err_valid = is_handle_valid(GetStdHandle(STD_ERROR_HANDLE));

    /*
     * If not all output are redirected try to redirect to parent console.
     * If parent has no console (for instance as launched from GUI) just
     * rely on default (no output).
     */
    if ((!out_valid || !err_valid) && AttachConsole(ATTACH_PARENT_PROCESS)) {
        fprintf(log_f, "attached\n");
        if (!out_valid) {
            freopen("CONOUT$", "w", stdout);
            dup2(fileno(stdout), STDOUT_FILENO);
        }
        if (!err_valid) {
            freopen("CONOUT$", "w", stderr);
            dup2(fileno(stderr), STDERR_FILENO);
        }
    }

    printf("stdout %s line\n", argv[0]);
    fflush(stdout);
    fprintf(stderr, "stderr %s line\n", argv[0]);
    fflush(stderr);
    return 0;
}

static enum {
    METHOD_CREATEPROCESS,
    METHOD_STDHANDLE
} redir_method = METHOD_CREATEPROCESS;

static void
exec(HANDLE redir_out, HANDLE redir_err)
{
    char program[MAX_PATH+128];
    GetModuleFileName(NULL, program+1, MAX_PATH);
    program[0] = '\"';
    sprintf(strchr(program, 0) , "\" %d", num_test);

    HANDLE old_out = GetStdHandle(STD_OUTPUT_HANDLE);
    HANDLE old_err = GetStdHandle(STD_ERROR_HANDLE);

    BOOL inherit = FALSE;
    STARTUPINFO si;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = 0;
    si.hStdOutput = si.hStdError = si.hStdInput = INVALID_HANDLE_VALUE;
    if (redir_out != INVALID_HANDLE_VALUE || redir_err != INVALID_HANDLE_VALUE) {
        if (redir_method == METHOD_CREATEPROCESS)
            si.dwFlags |= STARTF_USESTDHANDLES;
        inherit = TRUE;
        if (redir_out != INVALID_HANDLE_VALUE) {
            SetHandleInformation(redir_out, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);
            if (redir_method == METHOD_CREATEPROCESS) {
                si.hStdOutput = redir_out;
            } else {
                SetStdHandle(STD_OUTPUT_HANDLE, redir_out);
            }
        }
        if (redir_err != INVALID_HANDLE_VALUE) {
            SetHandleInformation(redir_err, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);
            if (redir_method == METHOD_CREATEPROCESS) {
                si.hStdError = redir_err;
            } else {
                SetStdHandle(STD_ERROR_HANDLE, redir_err);
            }
        }
    }

    fprintf(log_f, "handles %p %p - %p %p %d %d\n", si.hStdOutput, si.hStdError,
            GetStdHandle(STD_OUTPUT_HANDLE), GetStdHandle(STD_ERROR_HANDLE),
            has_inherit(GetStdHandle(STD_OUTPUT_HANDLE)), has_inherit(GetStdHandle(STD_ERROR_HANDLE)));

    fprintf(log_f, "sub command ---->\n");
    fclose(log_f);
    log_f = NULL;

    PROCESS_INFORMATION pi = { 0, };
    assert(CreateProcess(NULL, program, NULL, NULL, inherit, 0, NULL, NULL, &si, &pi));
    CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess, INFINITE);
    CloseHandle(pi.hProcess);

    log_f = fopen("log.txt", "a");
    assert(log_f);
    setbuf(log_f, NULL);
    fprintf(log_f, "<---- sub command\n");

    SetStdHandle(STD_OUTPUT_HANDLE, old_out);
    SetStdHandle(STD_ERROR_HANDLE,  old_err);
}

// simple dirty function to read first line in a file
static char *
read_file(const char *fn)
{
    FILE *f = fopen(fn, "r");
    assert(f);

    // dirty but fast
    static char buf[1024];

    memset(buf, 0, sizeof(buf));
    if (!fgets(buf, sizeof(buf), f))
        memset(buf, 0, sizeof(buf));

    fclose(f);
    return buf;
}

static char *
read_console(void)
{
    CONSOLE_SCREEN_BUFFER_INFO csbiInfo;
    assert(GetConsoleScreenBufferInfo(h_console, &csbiInfo));

    fprintf(log_f, "size %d %d\n", csbiInfo.dwSize.X, csbiInfo.dwSize.Y);
    fprintf(log_f, "win %d %d %d %d\n", csbiInfo.srWindow.Left, csbiInfo.srWindow.Top, csbiInfo.srWindow.Right, csbiInfo.srWindow.Bottom);

    COORD size;
    size.Y = csbiInfo.srWindow.Bottom + 1;
    size.X = csbiInfo.srWindow.Right + 1;

    COORD coord = { 0, 0 };

    CHAR_INFO *buf = calloc(size.Y * size.X, sizeof(CHAR_INFO));
    assert(buf);

    SMALL_RECT rect;
    rect.Top = 0;
    rect.Left = 0;
    rect.Bottom = size.Y - 1;
    rect.Right = size.X - 1;

    // read console content
    assert(ReadConsoleOutput(h_console, buf, size, coord, &rect));

    // convert to just text
    unsigned n;
    char *char_buf = (char *) buf;
    for (n = 0; n < size.X * size.Y; ++n)
        char_buf[n] = buf[n].Char.AsciiChar;
    char_buf[n] = 0;

    // remove additional spaces
    char *p;
    while ((p=strstr(char_buf, "  ")) != NULL)
        memmove(p, p+1, strlen(p));

    return char_buf;
}

static void
check(BOOL redir_out, BOOL redir_err)
{
    ++num_test;
    fprintf(log_f, "check method %d console %d redir_out %d redir_err %d\n",
            (int) redir_method, has_console, redir_out, redir_err);

    char stdout_line[64], stderr_line[64];

    sprintf(stdout_line, "stdout %d line", num_test);
    sprintf(stderr_line, "stderr %d line", num_test);

    DeleteFile("stdout.txt");
    DeleteFile("stderr.txt");

    HANDLE out = CreateFile("stdout.txt", GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, 0, NULL);
    assert(out != INVALID_HANDLE_VALUE);
    HANDLE err = CreateFile("stderr.txt", GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, 0, NULL);
    assert(err != INVALID_HANDLE_VALUE);

    exec(redir_out ? out : INVALID_HANDLE_VALUE,
         redir_err ? err : INVALID_HANDLE_VALUE);

    CloseHandle(out);
    CloseHandle(err);

    // check file output
    if (redir_out) {
        char *data = read_file("stdout.txt");
        assert(strstr(data, stdout_line) != NULL);
    }
    if (redir_err) {
        char *data = read_file("stderr.txt");
        assert(strstr(data, stderr_line) != NULL);
    }

    DeleteFile("stdout.txt");
    DeleteFile("stderr.txt");

    // check console output
    if (!has_console)
        return;

    char *data = read_console();
    fprintf(log_f, "\nconsole: %s\nstdout expected: %s\nstderr expected: %s\n", data, stdout_line, stderr_line);
    if (!redir_out)
        assert(strstr(data, stdout_line) != NULL);

    if (!redir_err)
        assert(strstr(data, stderr_line) != NULL);
    free(data);
}

static void
all_checks(void)
{
    check(TRUE, FALSE);
    check(FALSE, TRUE);
    check(TRUE, TRUE);

    assert(AllocConsole());
    has_console = TRUE;
    h_console = GetStdHandle(STD_OUTPUT_HANDLE);
    fprintf(log_f, "got console handles %p %p\n", h_console, GetStdHandle(STD_ERROR_HANDLE));

    check(FALSE, FALSE);
    check(TRUE, FALSE);
    check(FALSE, TRUE);
    check(TRUE, TRUE);

    assert(FreeConsole());
    has_console = FALSE;
    h_console = INVALID_HANDLE_VALUE;
}

int WINAPI WinMain(HINSTANCE hInstance G_GNUC_UNUSED, HINSTANCE hPrevInstance G_GNUC_UNUSED,
                   LPSTR lpCmdLine, int nShowCmd G_GNUC_UNUSED)
{
    static const char cmd_seps[] = " \t\r\n\v";

    char *argv[10], *p;
    int argc = 0;

    // parse arguments
    for (p = strtok(lpCmdLine, cmd_seps); p && argc < 10; p = strtok(NULL, cmd_seps))
        argv[argc++] = p;
    argv[argc] = NULL;

    log_f = fopen("log.txt", argc >= 1 ? "a" : "w");
    assert(log_f);
    setbuf(log_f, NULL);

    fprintf(log_f, "argc %d argv[0] %s \n", argc, argv[0]);

    if (argc >= 1) {
        return called_test(argc, argv);
    }

    // main program, call ourself with different arguments and settings
    redir_method = METHOD_CREATEPROCESS;
    all_checks();

    redir_method = METHOD_STDHANDLE;
    all_checks();

    fprintf(log_f, "everything ok\n");

    fclose(log_f);
    return 0;
}
