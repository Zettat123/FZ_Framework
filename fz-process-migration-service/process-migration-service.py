from flask import Flask, request
import requests
import json
import subprocess
import os
import shutil

from config import *

app = Flask(__name__)


def get_container_name_by_container_id(container_id):
    container_name = subprocess.check_output(
        ["docker ps --no-trunc | grep %s | awk '{print $NF}'" % container_id], shell=True, encoding="utf8")
    container_name = container_name.strip()
    return container_name


def get_image_id_by_container_id(container_id):
    container_id = container_id.strip()
    image_name = subprocess.check_output(
        ["docker ps --no-trunc | grep %s | awk '{print $2}'" % container_id], shell=True, encoding="utf8")
    image_name = image_name.strip()
    image_id = subprocess.check_output(
        ["docker images --no-trunc | grep %s | awk '{print $3}' | cut -d: -f2" % image_name], shell=True, encoding="utf8")
    image_id = image_id.strip()
    return image_id


def check_image_id_exists(image_id):
    ret = False
    output = subprocess.check_output(
        ["docker images --no-trunc | grep %s | wc -l" % image_id], shell=True, encoding="utf8")
    count = int(output.strip())
    if count > 0:
        ret = True
    return ret


def check_container_name_exists(container_name):
    ret = False
    output = subprocess.check_output(
        ["docker ps -a --no-trunc | grep %s | wc -l" % container_name], shell=True, encoding="utf8")
    count = int(output.strip())
    if count > 0:
        ret = True
    return ret


def get_host_address(host_name):
    QUERY_HOST_URL = "http://127.0.0.1:%d/queryHost" % (
        HOST_MANAGER_SERVICE_PORT)
    resp = requests.get(QUERY_HOST_URL, params={
                        "hostname": host_name}).json()
    return resp["value"]


def generate_files_path(image_id, container_id):
    files_dir = "%s/image_%s" % (SHARED_DIR, image_id)
    image_save_path = "%s/%s.tar" % (files_dir, image_id)
    ckpt_save_path = "%s/containers" % (files_dir)
    return files_dir, image_save_path, ckpt_save_path


def move_ckpt_files(container_id, ckpt_save_path_shared_dir):
    src_path = "%s/%s" % (ckpt_save_path_shared_dir, DEFAULT_CHECKPOINT_NAME)
    dst_path = "/var/lib/docker/containers/%s/checkpoints/" % (container_id)
    if not os.path.exists(dst_path):
        os.makedirs(dst_path)
    dst_ckpt_path = "%s/%s" % (dst_ckpt_path, DEFAULT_CHECKPOINT_NAME)
    if os.path.exists(dst_ckpt_path):
        shutil.rmtree(dst_ckpt_path)
    subprocess.check_output(
        ["mv %s %s" % (src_path, dst_path)], shell=True, encoding="utf8")
    return dst_ckpt_path


@app.route("/dump", methods=["POST"])
def handle_dump_process():
    params = json.loads(request.data)
    container_id = params["containerId"]
    target_host_name = params["targetHostname"]
    optionStr = params["optionStr"]
    image_id = get_image_id_by_container_id(container_id)
    container_name = get_container_name_by_container_id(container_id)
    files_dir, image_save_path, ckpt_save_path = generate_files_path(
        image_id, container_id)
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)
    print(ckpt_save_path)
    if os.path.exists(ckpt_save_path):
        shutil.rmtree(ckpt_save_path)
    subprocess.run(["docker", "checkpoint", "create",
                    "--checkpoint-dir=%s" % (ckpt_save_path), container_id, DEFAULT_CHECKPOINT_NAME])
    if not os.path.exists(image_save_path):
        subprocess.run(["docker", "save", "--output",
                        image_save_path, image_id])
    subprocess.run(["chmod", "-R", "666", files_dir])
    target_host_address = get_host_address(target_host_name)
    print(target_host_address)
    requests.post("http://%s:%d/restore" % (target_host_address, PORT), json={
        "imageId": image_id,
        "containerName": container_name,
        "containerId": container_id,
        "optionStr": optionStr
    })
    return {
        "status": "OK",
        "image_save_path": image_save_path,
        "ckpt_save_path": ckpt_save_path,
        "container_name": container_name
    }


@app.route("/restore", methods=["POST"])
def handle_restore_process():
    params = json.loads(request.data)
    image_id = params["imageId"]
    container_id = params["containerId"]
    container_name = params["containerName"]
    optionStr = params["optionStr"]
    files_dir, image_save_path, _ = generate_files_path(
        image_id, container_id)
    ckpt_save_path = "%s/containers/%s/checkpoints" % (
        files_dir, container_id)
    container_dir_path = "%s/containers/%s" % (
        files_dir, container_id)
    if not check_image_id_exists(image_id):
        subprocess.run(["docker", "load", "-i", image_save_path])
    if check_container_name_exists(container_name):
        subprocess.run(["docker", "stop", container_name])
        subprocess.run(["docker", "rm", container_name])
    docker_create_options = ["--ipc=host --pid=host"]
    if optionStr:
        options = optionStr.split(' ')
        docker_create_options += options
    docker_create_command = ["docker", "create"] + \
        docker_create_options + ["--name", container_name, image_id]
    subprocess.run(docker_create_command)
    subprocess.run(["docker", "start", "--checkpoint=%s" %
                    (DEFAULT_CHECKPOINT_NAME), "--checkpoint-dir=%s" % (ckpt_save_path), container_name])
    subprocess.run(["rm", "-r", container_dir_path])
    return "OK"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=PORT, debug=True)
