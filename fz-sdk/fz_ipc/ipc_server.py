from fz_ipc.ipc_common import *


class HandlerItem:
    shm = None
    thread = None
    lock = None

    def __init__(self, shm, thread, lock):
        self.shm = shm
        self.thread = thread
        self.lock = lock


class SignalHandlerThread(threading.Thread):
    outer = None
    client_pid = -1
    thread_name = ""
    item_name = ""
    shm_name = ""
    lock = None
    current_cmd = 0

    def __init__(self, outer, client_pid, lock):
        threading.Thread.__init__(self)
        self.outer = outer
        self.client_pid = client_pid
        self.thread_name = "%d_handler_thread" % (client_pid)
        self.item_name = str(client_pid)
        self.lock = lock
        self.current_cmd = IPC_CMD_ESTABLISH

    def update_cmd(self, new_cmd):
        self.current_cmd = new_cmd

    def run(self):
        while True:
            self.lock.acquire()
            cmd = self.current_cmd
            if cmd == IPC_CMD_COMMUNICATION:
                shm_buf = self.outer.handler_item_dict[self.item_name].shm.buf
                self.outer.user_handler(shm_buf)
                lib.sigqueueWithInt(
                    self.client_pid, FZ_SIGNAL, IPC_CMD_COMMUNICATION)
            elif cmd == IPC_CMD_ESTABLISH:
                lib.sigqueueWithInt(
                    self.client_pid, FZ_SIGNAL, IPC_CMD_ESTABLISH)
            elif cmd == IPC_CMD_CLOSE:
                break
            else:
                raise Exception(
                    "Invalid cmd: %d in client signal handler" % (cmd))

        self.outer.remove_handler_item(self.item_name)


class Server:
    server_pid = os.getpid()
    handler_item_dict = {}
    user_handler = None

    def __init__(self, user_handler):
        self.user_handler = user_handler
        print("Server start running")

        # install handler
        @ffi.def_extern()
        def signal_action_callback(signum, info, ctx):
            self.signal_handler(signum, info, ctx)

        lib.installHandler(FZ_SIGNAL, lib.signal_action_callback)

    def create_shm(self, client_pid):
        shm_name = str(client_pid)
        shm = shared_memory.SharedMemory(shm_name, create=False)
        return shm

    def remove_handler_item(self, handler_item_name):
        if handler_item_name in self.handler_item_dict:
            self.handler_item_dict[handler_item_name].shm.close()
            self.handler_item_dict[handler_item_name].shm.unlink()
            del self.handler_item_dict[handler_item_name]
        print("handler_item %s has been removed." % (handler_item_name))

    def signal_handler(self, signum, info, ctx):
        cmd = info.si_value.sival_int
        client_pid = info.si_pid
        print("Receive signal from %d, cmd: %d" % (client_pid, cmd))
        handler_item_name = str(client_pid)
        if handler_item_name not in self.handler_item_dict:
            lock = threading.Lock()
            thread = SignalHandlerThread(self, client_pid, lock)
            shm = self.create_shm(client_pid)
            self.handler_item_dict[handler_item_name] = HandlerItem(
                shm, thread, lock)
            self.handler_item_dict[handler_item_name].thread.start()
        else:
            self.handler_item_dict[handler_item_name].thread.update_cmd(cmd)
            self.handler_item_dict[handler_item_name].lock.release()
