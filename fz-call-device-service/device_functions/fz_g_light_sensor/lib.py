import os

DEVICE_FILE_PATH = "/dev/fz_g_light_sensor"


def call_fz_g_light_sensor(params):
    fd = os.open(DEVICE_FILE_PATH, os.O_RDWR | os.O_SYNC)
    try:
        read_ret = os.read(fd, 1)
    finally:
        os.close(fd)
    ret = list(read_ret)
    return ret[0]
