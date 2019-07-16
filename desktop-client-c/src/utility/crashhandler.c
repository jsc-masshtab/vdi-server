#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#ifdef __linux__
#include <execinfo.h>
#elif defined _WIN32
#else
#error "current OS is not supported"
#endif



#include "crashhandler.h"


//static const int nameSize = 200;
#define nameSize 200
static char fileName[nameSize];

void crush_handler(int sig){

#ifdef __linux__
    const int arraySize = 20;
    void *array[arraySize];
    int size;

    fprintf(stderr, "Oops! Error: %s.\n", strsignal(sig));

    // get void*'s for all entries on the stack
    size = backtrace(array, arraySize);

    // to console
    backtrace_symbols_fd(array, size, STDERR_FILENO);
    // // to file
    int pfd;
    if ((pfd = open(fileName, O_WRONLY | O_CREAT | O_TRUNC,
                    S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)) == -1){
        perror("Cannot open output file\n");
    }
    else{
        const char *buf = "Backtrace\n";
        ssize_t sizeWritten = write(pfd, buf, strlen(buf));
        (void)sizeWritten;
        backtrace_symbols_fd(array, size, pfd);
    }
#elif defined _WIN32
    (void)sig;
#else
#error "current OS is not supported"
#endif

    _Exit(0);
}
//========================================================================
void install_crash_handler(const char *logFileName){

    memcpy(&fileName[0], logFileName, strlen(logFileName));

    signal(SIGSEGV, crush_handler);
    signal(SIGABRT, crush_handler);
    signal(SIGFPE, crush_handler);
}


