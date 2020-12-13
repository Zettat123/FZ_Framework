import requests
import os
import subprocess
import time
from .fz_ipc.ipc_client import Client
from .fz_ipc.ipc_common import usleep
from .fz_ipc.ipc_data_utils import *

CALL_DEVICE_SERVICE_PORT = 29601


def get_call_device_url(target_address):
    return "http://%s:%d/callDevice" % (target_address, CALL_DEVICE_SERVICE_PORT)


PROCESS_MIGRATION_SERVICE_PORT = 29602
DUMP_PROCESS_URL = "http://172.17.0.1:%d/dump" % (
    PROCESS_MIGRATION_SERVICE_PORT)

HOST_MANAGER_SERVICE_PORT = 29603
QUERY_DEVICE_URL = "http://172.17.0.1:%d/queryDevice" % (
    HOST_MANAGER_SERVICE_PORT)
QUERY_CURRENT_HOST_NAME_URL = "http://172.17.0.1:%d/currentHostName" % (
    HOST_MANAGER_SERVICE_PORT)
QUERY_HOST_ADDRESS_URL = "http://172.17.0.1:%d/queryHost" % (
    HOST_MANAGER_SERVICE_PORT)
SHM_LENGTH = 4*1024


def get_call_device_service_pid():
    service_pid = subprocess.check_output(
        ["ps aux | grep \"/call_device_service.py\" | head -1 | awk '{print $2}'"], shell=True, encoding="utf8")
    service_pid = service_pid.strip()
    return int(service_pid)


def get_container_id():
    output = subprocess.check_output(
        ["cat /proc/self/cgroup | grep docker | head -1 | cut -d/ -f3"], shell=True, encoding="utf8")
    container_id = output.strip()
    return container_id


def check_special_device(device_name):
    return device_name[3] == "s"


def get_current_host_name():
    resp = requests.get(QUERY_CURRENT_HOST_NAME_URL).json()
    return resp["currentHostName"]


def get_host_name_of_device(device_name):
    resp = requests.get(QUERY_DEVICE_URL, params={
                        "deviceName": device_name}).json()
    host_name = resp["hostName"]
    real_device_name = resp["realDeviceName"]
    return host_name, real_device_name


def get_host_address_by_host_name(host_name):
    resp = requests.get(QUERY_HOST_ADDRESS_URL, params={
                        "hostname": host_name}).json()
    return resp["value"]


def fz_call_device(device_name, params={}, customized_device_call_function=None):
    print(device_name)
    target_host_name, real_device_name = get_host_name_of_device(device_name)
    print(target_host_name)
    print(real_device_name)
    device_name = real_device_name
    if target_host_name == "localhost":
        if customized_device_call_function is None:
            # ipc
            print("will ipc")
            return ipc_with_call_device_service(device_name, params)
        else:
            return customized_device_call_function(params)
    else:
        if check_special_device(device_name):
            # migration to
            old_host_name = get_current_host_name()
            print("Old hostname: {}, target hostname: {}".format(
                old_host_name, target_host_name))
            migrate_process(target_host_name)
            # call device
            # print("hello")
            ret = customized_device_call_function(params)
            # migration back
            migrate_process(old_host_name)
            return ret
        else:
            target_address = get_host_address_by_host_name(target_host_name)
            resp = requests.post(get_call_device_url(
                target_address), json={"deviceName": device_name, "params": params}).json()
            return resp["value"]


def ipc_with_call_device_service(device_name, params):
    service_pid = get_call_device_service_pid()
    global result
    result = None

    def user_handler(buf):
        data = decode_ipc_data(buf)
        global result
        result = data["value"]
        return -1
    Client(service_pid, SHM_LENGTH, user_handler, encode_ipc_data(
        {"deviceName": device_name, "params": params}))
    while result is None:
        usleep(1000*1000*60)
    return result


def migrate_process(target_host_name):
    if get_current_host_name() == target_host_name:
        return
    container_id = get_container_id()
    try:
        requests.post(DUMP_PROCESS_URL, json={
            "containerId": container_id,
            "targetHostname": target_host_name,
            "optionStr": os.getenv("RUN_OPTIONS", None)
        }, timeout=0.8)
    except:
        pass
    while get_current_host_name() != target_host_name:
        time.sleep(1)


# print(fz_call_device("fz_g_test_dev", {"length": 5}))
