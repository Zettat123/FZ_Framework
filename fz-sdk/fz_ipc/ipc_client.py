from fz_ipc.ipc_common import *


class Client:
    client_pid = os.getpid()
    server_pid = -1
    shm_length = 0
    shm_name = ""
    shm = None
    user_handler = None
    can_communicate = False

    def __init__(self, server_pid, shm_length, user_handler, first_data):
        self.server_pid = server_pid
        self.shm_length = shm_length
        self.shm_name = str(self.client_pid)
        self.user_handler = user_handler

        # install handler
        @ffi.def_extern()
        def signal_action_callback(signum, info, ctx):
            self.signal_handler(signum, info, ctx)

        lib.installHandler(FZ_SIGNAL, lib.signal_action_callback)

        self.initialize_shm(first_data)



    def initialize_shm(self, first_data):
        self.shm = shared_memory.SharedMemory(
            self.shm_name, create=True, size=self.shm_length)
        first_data_len = len(first_data)
        self.shm.buf[0:first_data_len] = first_data
        lib.sigqueueWithInt(self.server_pid, FZ_SIGNAL, IPC_CMD_ESTABLISH)
        while not self.can_communicate:
            time.sleep(1)

    def signal_handler(self, signum, info, ctx):
        cmd = info.si_value.sival_int
        if cmd == IPC_CMD_COMMUNICATION:
            shm_buf = self.shm.buf
            ret = self.user_handler(shm_buf)
            if ret < 0:
                self.close()
            else:
                lib.sigqueueWithInt(self.server_pid, FZ_SIGNAL,
                                    IPC_CMD_COMMUNICATION)
        elif cmd == IPC_CMD_ESTABLISH:
            self.can_communicate = True
            lib.sigqueueWithInt(self.server_pid, FZ_SIGNAL,
                                IPC_CMD_COMMUNICATION)
        else:
            raise Exception(
                "Invalid cmd: %d in client signal handler" % (cmd,))

    def close(self):
        self.shm.close()
        lib.sigqueueWithInt(self.server_pid, FZ_SIGNAL, IPC_CMD_CLOSE)
