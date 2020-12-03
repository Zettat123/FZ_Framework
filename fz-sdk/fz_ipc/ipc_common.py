import signal
import os
import time
import threading
from multiprocessing import shared_memory
from fz_ipc.__fz_signal_utils import ffi, lib

# Use SIGUSR1 as FZ_SIGNAL
FZ_SIGNAL = signal.SIGUSR1

# CMD is union sigval.sival_int
# if CMD > 0, it means the length of shm
# else:
IPC_CMD_COMMUNICATION = 0
IPC_CMD_ESTABLISH = -1
IPC_CMD_CLOSE = -2


def usleep(micro_seconds):
    lib.usleep(micro_seconds)
