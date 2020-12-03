import array
import json


def decode_ipc_data(buf):
    length_section = memoryview(buf[0:4]).cast('I')
    length = length_section[0]

    content_section = bytearray(buf[4:4+length])
    content_str = content_section.decode()
    content = json.loads(content_str)
    return content


def encode_ipc_data(content):
    content_json = json.dumps(content)
    content_json_bytes = bytes(content_json, encoding="utf-8")
    content_json_bytes_len = len(content_json)

    arr = array.array('I', [content_json_bytes_len])
    length_memory_view = memoryview(arr)
    length_bytes = length_memory_view.tobytes()
    length_bytes_len = len(length_bytes)

    ret = bytearray(length_bytes_len+content_json_bytes_len)
    ret[0:length_bytes_len] = length_bytes
    ret[length_bytes_len:length_bytes_len +
        content_json_bytes_len] = content_json_bytes

    return ret
