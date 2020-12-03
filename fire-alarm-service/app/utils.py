import time
import os
import subprocess
import base64
from fz_sdk.fz_sdk import fz_call_device

dht11_dev_name = "fz_g_dht11"
mq2_dev_name = "fz_g_mq2"
light_sensor_dev_name = "fz_g_light_sensor"
webcam_dev_name = "fz_s_webcam"
picture_file_name = "alarm.jpg"

temprature_threshold = 50


def get_tempreture():
    ret = fz_call_device(dht11_dev_name)
    if ret[0] + ret[1] + ret[2] + ret[3] != ret[4]:
        return -1
    temprature = ret[2] + ret[3] / 100
    return temprature


def take_picture(params={}):
    subprocess.check_output(["./take_picture_tool.out 320 240 %s /dev/%s" %
                             (picture_file_name, webcam_dev_name)], shell=True, encoding="utf8")
    with open(picture_file_name, 'rb') as f:
        pic = f.read()
        pic_b64 = str(base64.b64encode(pic), encoding="utf8")
    return pic_b64


def process():
    alarm = False
    temprature = get_tempreture()
    smoke = fz_call_device(mq2_dev_name)
    light = fz_call_device(light_sensor_dev_name)
    pic_b64 = None
    # if temprature > temprature_threshold or light == 1 or smoke == 1:
    if light == 1:
        alarm = True
        pic_b64 = fz_call_device(webcam_dev_name,
                                 customized_device_call_function=take_picture)
    return {
        "alarm": alarm,
        "temprature": temprature,
        "smoke": smoke,
        "light": light,
        "picture": pic_b64
    }
