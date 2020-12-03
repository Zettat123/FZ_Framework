from flask import Flask, request
import requests
import socket
import threading
import subprocess
import os
import time
import sys
import json
import signal
from config import *
from utils import *


HOST_IP = get_host_ip()

hosts = {HOSTNAME: HOST_IP}
devices = {}
heartbeat_timeout_count = {}

app = Flask(__name__)


def initialize_thread_function(one_existing_host_address):
    def get_url(addr):
        return "http://%s:%d/addNewHost?newHostName=%s" % (addr, PORT, HOSTNAME)
    hosts_dict = requests.get(get_url(one_existing_host_address)).json()
    hosts.update(hosts_dict)


def update_devices_thread_function():
    # as heartbeat
    while True:
        update_devices_internal()
        time.sleep(HEARTBEAT_INTERVAL)


def update_devices_internal():
    hosts_view = list(hosts.items())
    for h_name, h_address in hosts_view:
        ret_devices = []
        if h_name == HOSTNAME:
            ret_devices = get_local_devices()
        else:
            url = "http://%s:%d/devices" % (h_address, PORT)
            try:
                resp = requests.get(url)
                ret_devices = resp.json()
            except requests.exceptions.RequestException as e:
                print(e)
                handle_heartbeat_timeout(h_name)

        if h_name == HOSTNAME:
            h_name = "localhost"
        for device_name in ret_devices:
            devices.update({device_name: h_name})
        devices_key_view = list(devices.keys())
        for device_name in devices_key_view:
            if devices.get(device_name) == h_name and device_name not in ret_devices:
                devices.pop(device_name)


def handle_heartbeat_timeout(hostname):
    htc_key_view = list(heartbeat_timeout_count.keys())
    if hostname not in htc_key_view:
        heartbeat_timeout_count.update({hostname: 1})
    else:
        heartbeat_timeout_count.update(
            {hostname: heartbeat_timeout_count.get(hostname) + 1})
    if heartbeat_timeout_count.get(hostname) > HEARTBEAT_MAX_TIMEOUT_COUNT:
        hosts.pop(hostname)
        heartbeat_timeout_count.pop(hostname)


def add_new_host(name, address):
    hosts.update({name: address})
    # update_devices_internal()


def get_other_hosts():
    ret = {}
    hosts_key_view = list(hosts.keys())
    for hostname in hosts_key_view:
        if hostname == HOSTNAME:
            continue
        ret[hostname] = hosts.get(hostname)
    return ret


def get_local_devices():
    ret = []
    fz_device_file_list = list(
        filter(lambda x: x.startswith("fz_"), os.listdir("/dev")))
    for device_name in fz_device_file_list:
        if device_name not in IGNORE_DEVICES:
            ret.append(device_name)
    for device_name in EXTRA_DEVICES:
        ret.append(device_name)
    return ret


@app.route("/running", methods=["GET"])
def handle_running():
    return "Running"
    # print(os.getpid())
    # return json.dumps(dict(os.environ))


@app.route("/devices", methods=["GET"])
def handle_get_devices():
    local_devices = get_local_devices()
    return json.dumps(local_devices)


@app.route("/allDevices", methods=["GET"])
def handle_get_all_devices():
    return json.dumps(devices)


@app.route("/allHosts", methods=["GET"])
def handle_get_all_hosts():
    return json.dumps(hosts)


@app.route("/addNewHost", methods=["GET"])
def handle_add_new_host():
    new_device_name = request.args.get("newHostName")
    new_device_address = request.remote_addr
    add_new_host(new_device_name, new_device_address)
    return json.dumps(hosts)


@app.route("/queryDevice", methods=["GET"])
def handle_query_device():
    device_name = request.args.get("deviceName")
    while devices.get(device_name) not in list(hosts.keys()) and devices.get(device_name) != "localhost":
        device_name = devices.get(device_name)
    return json.dumps({
        "hostName": devices.get(device_name)
    })


@app.route("/queryHost", methods=["GET"])
def handle_query_host():
    code = 0
    value = ""
    hostname = request.args.get("hostname")
    hosts_key_view = list(hosts.keys())
    if hostname not in hosts_key_view:
        code = -1
        value = "Not Found"
    else:
        value = hosts.get(hostname)
    return json.dumps({
        "code": code,
        "value": value
    })


@app.route("/currentHostName", methods=["GET"])
def handle_current_host():
    return json.dumps({"currentHostName": HOSTNAME})


if __name__ == '__main__':
    update_devices_thread = threading.Thread(
        None, target=update_devices_thread_function, name="update_devices_thread")
    update_devices_thread.start()
    if len(sys.argv) < 2:
        print("First host")
    else:
        existing_host_address = sys.argv[1]
        print("Will initialize with %s" % (existing_host_address))
        initialize_thread = threading.Thread(
            None, target=initialize_thread_function, name="initialize_thread", args=(existing_host_address,))
        initialize_thread.start()

    app.run(host="0.0.0.0", port=PORT, debug=True)