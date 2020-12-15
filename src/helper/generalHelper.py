import base64
import os

import cv2
import numpy as np


def decode_base64_to_image(base64_string):
    decoded_string = base64.b64decode(base64_string)
    np_arr = np.fromstring(decoded_string, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_ANYCOLOR)


def encode_image_to_base64(filename):
    with open(filename, 'rb') as imageFile:
        return base64.b64encode(imageFile.read()).decode('utf-8')


def create_log_dir_if_does_not_exists(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
