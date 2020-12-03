from cffi import FFI

ffi = FFI()

ffi.cdef(
    """
    typedef int pid_t;  
    typedef unsigned int uid_t;

    union sigval {
        int sival_int;
        ...;
    };

    typedef union sigval sigval_t;

    typedef struct {
        int         si_signo;    /* Signal number */
        pid_t       si_pid;      /* Sending process ID */
        uid_t       si_uid;      /* Real user ID of sending process */
        sigval_t    si_value;
        ...;
    } siginfo_t;

    typedef struct {
        ...; 
    } sigset_t;

    struct sigaction{
        void     (*sa_handler)(int);
        void     (*sa_sigaction)(int, siginfo_t *, void *);
        sigset_t   sa_mask;
        int        sa_flags;
    };

    int sigaction(int signum, const struct sigaction *act, struct sigaction *oldact);
    int installHandler(int signum, void(*handler)(int, siginfo_t *, void *));
    int sigqueue(pid_t pid, int sig, const union sigval value);
    int sigqueueWithInt(pid_t target_pid, int signum, int value);

    void usleep(int micro_seconds);

    extern "Python" void signal_action_callback(int, siginfo_t *, void *);
    """
)

ffi.set_source("__fz_signal_utils",
               """
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>

int installHandler(int signum, void(*handler)(int, siginfo_t *, void *)) {
    struct sigaction act;
    act.sa_flags = SA_SIGINFO;
    act.sa_sigaction = handler;
    return sigaction(signum, &act, NULL);
}

int sigqueueWithInt(pid_t target_pid, int signum, int value) {
    union sigval sv;
    sv.sival_int = value;
    return sigqueue(target_pid, signum, sv);
}


"""
               )


ffi.compile(verbose=True)
