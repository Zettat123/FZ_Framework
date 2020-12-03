import os

DEVICE_FILE_PATH = "/dev/fz_g_test_dev"


def call_fz_g_test_dev(params):
    fd = os.open(DEVICE_FILE_PATH, os.O_RDWR | os.O_SYNC)
    try:
        length = params["length"]
        read_ret = os.read(fd, length)
    finally:
        os.close(fd)
    ret = read_ret.decode()
    return ret
