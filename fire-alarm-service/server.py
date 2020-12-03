from flask import Flask, request, redirect, url_for
from flask_cors import CORS
import base64
import json
import os

SHARED_DIR = os.path.normpath(os.path.join(
    os.path.abspath(__file__), "../../shared-dir"))
HOSTNAME = os.uname()[1]

app = Flask(__name__)
CORS(app, supports_credentials=True, origins="*")

data = {}


@app.route("/running", methods=["GET"])
def handle_running():
    return "Running"


@app.route("/", methods=["GET"])
def handle_index():
    return redirect(url_for('static', filename="index.html"))


@app.route("/recvData", methods=["POST"])
def handle_recv_data():
    recv_data = json.loads(request.data)
    data.update(recv_data)
    return "OK"


@app.route("/data", methods=["GET"])
def handle_get_data():
    return json.dumps(data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=29600, debug=True)
