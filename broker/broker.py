import json
import os

from kafka import KafkaConsumer

from misc.value import *
from storage.storage import api_post

bootstrap_server = "{}:{}".format(os.getenv("KAFKA_HOST"), os.getenv("KAFKA_PORT"))
consume_topic = os.getenv("KAFKA_PROCESS_TOPIC", "LPRProcess")

url_upload = "{}:{}/{}".format(os.getenv("STORAGE_HOST"), os.getenv("STORAGE_PORT"), os.getenv("STORAGE_UPLOAD_URL"))
url_get_image = "{}:{}/{}".format(os.getenv("STORAGE_HOST"), os.getenv("STORAGE_PORT"),
                                  os.getenv("STORAGE_GET_IMAGE_URL"))


class Broker:
    def __init__(self):
        self.consumer = KafkaConsumer(consume_topic, bootstrap_servers=bootstrap_server, auto_offset_reset='smallest')

    def consume(self):
        for message in self.consumer:
            data = json.loads(message.value)
            gate_id = data['gate_id']
            token = data['token']
            self.get_image_from_storage(token)

    def get_image_from_storage(self, token):
        payload = {'token': token}
        response = api_post(url_get_image, payload)
        if response['status'] == HTTP_STATUS_OK:
            print(response['encoded_file'])
        elif response['status'] == HTTP_STATUS_NOT_FOUND:
            print("Image not found.")
        else:
            print(response['message'])
