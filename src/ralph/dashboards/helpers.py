import base64
import json


def encode_params(params):
    return base64.urlsafe_b64encode(json.dumps(params).encode())


def decode_params(value):
    if not value:
        return {}
    return json.loads(base64.urlsafe_b64decode(value).decode())
