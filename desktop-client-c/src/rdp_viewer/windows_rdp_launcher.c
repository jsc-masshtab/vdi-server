#include <config.h>
#include <gio/gio.h>
#include <gtk/gtk.h>

#ifdef _WIN32
#include <windows.h>
#include <stdio.h>
#include <tchar.h>
#endif

#include "rdp_viewer.h"

/// В msys2 не нашел gspawn-win32-helper. Без него запуск ппроцессов с помощтю gtk невозможен


void
launch_windows_rdp_client(const gchar *usename, const gchar *password G_GNUC_UNUSED,
                          const gchar *ip, int port G_GNUC_UNUSED)
{
#ifdef __linux__
    (void)usename;
    (void)ip;
#elif defined _WIN32
    //create rdp file based on template
    //open template for reading and take its content
    FILE *sourceFile;
    FILE *destFile;
    int count;

    const char *src_file_name = "rdp_data/rdp_template_file.txt";
    sourceFile = fopen(src_file_name,"r");
    const char *dest_file_name = "rdp_data/rdp_file.rdp";
    destFile = fopen(dest_file_name, "w");

    /* fopen() return NULL if unable to open file in given mode. */
    if (sourceFile == NULL || destFile == NULL)
    {
        // Unable to open
        printf("\nUnable to open file.\n");
        printf("Please check if file exists and you have read/write privilege.\n");
        return;
    }
    // Copy file
    char ch;
    /* Copy file contents character by character. */
    while ((ch = fgetc(sourceFile)) != EOF)
    {
        fputc(ch, destFile);
        //printf("symbol: %i.\n", ch);
    }

    // apend unique data
    //full address:s:192.168.7.99
    //username:s:User1
    gchar *full_address = g_strdup_printf("full address:s:%s\n", ip);
    fputs(full_address, destFile);
    g_free(full_address);
    gchar *full_username = g_strdup_printf("username:s:%s", usename);
    fputs(full_username, destFile);
    g_free(full_username);

    /* Close files to release resources */
    fclose(sourceFile);
    fclose(destFile);

    // launch process
    STARTUPINFO si;
    PROCESS_INFORMATION pi;

    ZeroMemory( &si, sizeof(si) );
    si.cb = sizeof(si);
    ZeroMemory( &pi, sizeof(pi) );

    // Start the child process.
    gchar *cmd_line = g_strdup_printf("mstsc %s", dest_file_name);
//    gchar *cmd_line = g_strdup(
//            "mstsc C:\\job\\vdiserver\\desktop-client-c\\cmake-build-release\\rdp_datardp_file.rdp");
    if( !CreateProcess( NULL,   // No module name (use command line)
                        cmd_line,        // Command line
                        NULL,           // Process handle not inheritable
                        NULL,           // Thread handle not inheritable
                        FALSE,          // Set handle inheritance to FALSE
                        0,              // No creation flags
                        NULL,           // Use parent's environment block
                        NULL,           // Use parent's starting directory
                        &si,            // Pointer to STARTUPINFO structure
                        &pi )           // Pointer to PROCESS_INFORMATION structure
            )
    {
        printf( "CreateProcess failed (%d).\n", GetLastError() );
        g_free(cmd_line);
        return;
    }
    g_free(cmd_line);

    // Wait until child process exits.
    WaitForSingleObject( pi.hProcess, INFINITE );

    // Close process and thread handles.
    CloseHandle( pi.hProcess );
    CloseHandle( pi.hThread );
#endif
}
