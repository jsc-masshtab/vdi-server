#include <stdio.h>
#include <execinfo.h>
#include <signal.h>
#include <stdlib.h>
#include <unistd.h>

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#include "crashhandler.h"


//static const int nameSize = 200;
#define nameSize 200
static char fileName[nameSize];

void crush_handler(int sig){

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
        write(pfd, buf, strlen(buf));
        backtrace_symbols_fd(array, size, pfd);
    }

    _Exit(0);
}
//========================================================================
void installHandler(const char *logFileName){

    memcpy(&fileName[0], logFileName, strlen(logFileName));

    signal(SIGSEGV, crush_handler);
    signal(SIGABRT, crush_handler);
    signal(SIGFPE, crush_handler);
    signal(SIGPIPE, crush_handler);
}


