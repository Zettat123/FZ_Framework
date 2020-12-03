from flask import Flask, request
import requests
import json
import os
import subprocess
import array
import _thread

from config import *
from device_functions import get_call_device_function
from fz_ipc.ipc_server import Server
from fz_ipc.ipc_data_utils import *
from tcp_server import run_tcp_server

app = Flask(__name__)


def check_special_device(device_name):
    return device_name[3] == "s"


def query_device(device_name):
    ret = requests.get("http://127.0.0.1:%d/queryDevice" % (HOST_SERVICE_MANAGER_PORT), params={
        "deviceName": device_name
    }).json()
    hostname = ret["value"]
    print("%s - %s" % (device_name, hostname))
    return hostname


def query_host(hostname):
    ret = requests.get("http://127.0.0.1:%d/queryHost" % (HOST_SERVICE_MANAGER_PORT), params={
        "hostname": hostname
    }).json()
    address = ret["value"]
    print("%s - %s" % (hostname, address))
    return address


@app.route("/running", methods=["GET"])
def handle_running():
    return "Running"


@app.route("/callDevice", methods=["POST"])
def handle_call_device():
    data = json.loads(request.data)
    device_name = data["deviceName"]
    params = data.get("params", {})
    ret = get_call_device_function(device_name)(params)
    ret_body = {"value": ret}
    return json.dumps(ret_body)


def signal_handler(buf):
    data = decode_ipc_data(buf)
    device_name = data["deviceName"]
    params = data.get("params", {})

    ret = get_call_device_function(device_name)(params)
    ret_dict = {"value": ret}

    ret_buf = encode_ipc_data(ret_dict)

    buf[0:len(ret_buf)] = ret_buf


if __name__ == '__main__':
    print("call_device_service pid: %d" % (os.getpid()))
    Server(signal_handler)
    _thread.start_new_thread(run_tcp_server, ("tcp_server thread",))
    app.run(host="0.0.0.0", port=29601, debug=True)
