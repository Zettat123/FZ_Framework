import requests
import time
from utils import process

POST_URL = "http://172.17.0.1:29600/recvData"

while True:
    time.sleep(2)
    process_ret = process()
    try:
        requests.post(POST_URL, json=process_ret)
    except:
        pass
