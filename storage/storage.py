import json

import requests

from misc.value import HTTP_STATUS_BAD_REQUEST, HTTP_STATUS_OK


def api_post(url, payload):
    try:
        response = requests.post(url, json=payload)
        data = json.loads(response.text)
        returned_data = data['data'] if response.status_code == HTTP_STATUS_OK else None
        return {
            'status': response.status_code,
            'message': data['message'],
            'data': returned_data
        }
    except Exception as err:
        print("error = ", err)
        return {
            'status': HTTP_STATUS_BAD_REQUEST,
            'message': err,
        }
