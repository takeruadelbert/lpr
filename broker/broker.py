import json

import easyocr
from kafka import KafkaConsumer
from kafka import KafkaProducer

from helper.generalHelper import decode_base64_to_image, encode_image_to_base64
from src.licensePlateRecognition import *
from storage.storage import api_post

bootstrap_server = "{}:{}".format(os.getenv("KAFKA_HOST"), os.getenv("KAFKA_PORT"))
consume_topic = os.getenv("KAFKA_PROCESS_TOPIC", "LPRProcess")
consume_topic_group_id = os.getenv("KAFKA_PROCESS_TOPIC_GROUP_ID", "lpr-service")

url_upload = "{}:{}/{}".format(os.getenv("STORAGE_HOST"), os.getenv("STORAGE_PORT"), os.getenv("STORAGE_UPLOAD_URL"))
url_get_image = "{}:{}/{}".format(os.getenv("STORAGE_HOST"), os.getenv("STORAGE_PORT"),
                                  os.getenv("STORAGE_GET_IMAGE_URL"))


class Broker:
    def __init__(self, logger):
        self.consumer = KafkaConsumer(consume_topic, bootstrap_servers=bootstrap_server,
                                      group_id=consume_topic_group_id)
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_server,
                                      value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        self.logger = logger
        self.logger.info('Loading Reader ...')
        print("Loading Reader ...")
        self.reader = easyocr.Reader(['id'], gpu=True)
        print("Loaded.")
        self.logger.info('Loaded.')
        self.lpr = LicensePlateRecognition(self.reader)

    def consume(self):
        for message in self.consumer:
            data = json.loads(message.value)
            self.logger.info('consuming data {} from queue'.format(data))
            gate_id = data['gate_id']
            token = data['token']
            self.logger.info('processing {} ...'.format(token))
            image_origin = self.get_image_from_storage(token)
            cv2.imwrite('{}'.format(DEFAULT_NAME_LPR_IMAGE_RESULT), image_origin)
            self.lpr.set_image(image_origin)
            result = self.lpr.run()
            if result['type'] != UNKNOWN_VEHICLE and result['license_plate_number'] != UNDETECTED:
                token = self.upload_lpr_image_result()
                result['token'] = token
            produce_payload = {
                'gate_id': gate_id,
                'result': result,
            }
            self.logger.info('sending {} to queue'.format(produce_payload))
            self.produce(payload=produce_payload)
            self.logger.info('{} processed.'.format(token))

    def get_image_from_storage(self, token):
        payload = {'token': token}
        response = api_post(url_get_image, payload)
        if response['status'] == HTTP_STATUS_OK:
            return decode_base64_to_image(response['data'])
        elif response['status'] == HTTP_STATUS_NOT_FOUND:
            self.logger.warning("[{}] Image not found.".format(token))
        else:
            self.logger.error(response['message'])
        return None

    def upload_lpr_image_result(self):
        encoded_image = encode_image_to_base64(DEFAULT_NAME_LPR_IMAGE_RESULT)
        payload = [{
            'filename': '{}'.format(DEFAULT_NAME_LPR_IMAGE_RESULT),
            'encoded_file': '{}{}'.format(DEFAULT_PREFIX_BASE64, encoded_image)
        }]
        upload_response = api_post(url_upload, payload)
        if upload_response['status'] == HTTP_STATUS_OK:
            self.logger.info('upload success : {}'.format(upload_response['data'][0]['token']))
            return upload_response['data'][0]['token']
        else:
            self.logger.error(upload_response['message'])
            return None

    def produce(self, **kwargs):
        try:
            produce_topic = os.getenv("KAFKA_RESULT_TOPIC")
            payload = kwargs.get('payload')
            self.producer.send(produce_topic, payload)
            self.logger.info('payload sent to queue.')
        except Exception as err:
            self.logger.error("Produce Error : {}".format(err))
