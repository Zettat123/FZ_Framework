import socket
import sys
import os

DEVICE_LIST = ["/dev/fz_g_test_dev",        # 0
               "/dev/fz_g_dht11",           # 1
               "/dev/fz_g_light_sensor",    # 2
               "/dev/fz_g_mq2"              # 3
               ]


def run_tcp_server(thread_name):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'
    port = 29701
    serversocket.bind((host, port))
    serversocket.listen(5)

    while True:
        clientsocket, addr = serversocket.accept()
        print("Connection address: %s" % str(addr))

        client_data = clientsocket.recv(4096)
        print(client_data)
        mv = memoryview(client_data)
        params = mv[:12]
        data = mv[12:]
        params = params.cast('i')
        print(params[0], params[1], params[2])
        device_number = params[0]
        operation_type = params[1]
        read_len = params[2]

        msg = bytes()
        if device_number > (len(DEVICE_LIST) - 1):
            msg_str = "No such device: {}".format(device_number)
            msg = msg_str.encode('utf-8')

        elif operation_type == 1:
            print("READ")
            fd = os.open(DEVICE_LIST[device_number], os.O_RDWR | os.O_SYNC)
            read_ret = os.read(fd, read_len)
            os.close(fd)
            msg = read_ret

        elif operation_type == 2:
            print("WRITE")
            fd = os.open(DEVICE_LIST[device_number], os.O_RDWR | os.O_SYNC)
            write_ret = os.write(fd, data)
            os.close(fd)
            msg = str(write_ret)
            msg = msg.encode('utf-8')

        # clientsocket.send(msg.encode('utf-8'))
        clientsocket.send(msg)
        clientsocket.close()
