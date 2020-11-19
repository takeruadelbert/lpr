import json

import easyocr
from kafka import KafkaConsumer
from kafka import KafkaProducer

from helper.generalHelper import decode_base64_to_image, encode_image_to_base64
from src.licensePlateRecognition import *
from storage.storage import api_post

bootstrap_server = "{}:{}".format(os.getenv("KAFKA_HOST"), os.getenv("KAFKA_PORT"))
consume_topic = os.getenv("KAFKA_PROCESS_TOPIC", "LPRProcess")
consume_topic_image = os.getenv("KAFKA_PROCESS_IMAGE_TOPIC", "LPRImageService")
consume_topic_group_id = os.getenv("KAFKA_PROCESS_TOPIC_GROUP_ID", "lpr-service")
produce_topic = os.getenv("KAFKA_RESULT_TOPIC", "LPRResult")
produce_image_topic = os.getenv("KAFKA_RESULT_IMAGE_TOPIC", "LPRImageServiceResult")

url_upload = "{}:{}/{}".format(os.getenv("STORAGE_HOST"), os.getenv("STORAGE_PORT"), os.getenv("STORAGE_UPLOAD_URL"))
url_get_image = "{}:{}/{}".format(os.getenv("STORAGE_HOST"), os.getenv("STORAGE_PORT"),
                                  os.getenv("STORAGE_GET_IMAGE_URL"))


class Broker:
    def __init__(self, logger):
        self.consumer = KafkaConsumer(bootstrap_servers=bootstrap_server, group_id=consume_topic_group_id,
                                      max_poll_records=KAFKA_MAX_POLL_RECORD)
        self.consumer.subscribe([consume_topic, consume_topic_image])
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_server,
                                      value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        self.logger = logger
        self.logger.info('Loading Reader ...')
        print("Loading Reader ...")
        self.reader = easyocr.Reader(['id'], gpu=True)
        print("Loaded.")
        self.logger.info('Loaded.')
        self.lpr = LicensePlateRecognition(self.reader)
        self.lpr2 = LicensePlateRecognition(self.reader, True)

    def consume(self):
        try:
            for message in self.consumer:
                data = json.loads(message.value)
                if message.topic == consume_topic:
                    self.process_frame_result(data)
                else:
                    self.process_image_result(data)
        except Exception as error:
            self.logger.error(error)

    def process_frame_result(self, data):
        self.logger.info('consuming data from {} queue : {}'.format(consume_topic, data))
        gate_id = data['gate_id']
        token = data['token']
        self.logger.info('processing {} from {}...'.format(token, consume_topic))
        image_origin = self.get_image_from_storage(token)
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
        self.produce(produce_topic=produce_topic, payload=produce_payload)
        self.logger.info('{} processed.'.format(token))
        self.consumer.commit()

    def process_image_result(self, data):
        self.logger.info('consuming data from {} Queue: {}'.format(consume_topic_image, data))
        token = data['token']
        ticket_number = data['ticket_number']
        self.logger.info('processing {} from {}...'.format(token, consume_topic_image))
        image_origin = self.get_image_from_storage(token)
        self.lpr2.set_image(image_origin)
        result = self.lpr2.run()
        if result['type'] != UNKNOWN_VEHICLE and result['license_plate_number'] != UNDETECTED:
            token = self.upload_lpr_image_result(True)
            result['token'] = token
        produce_payload = {
            'ticket_number': ticket_number,
            'result': result,
        }
        self.logger.info('sending {} to queue'.format(produce_payload))
        self.produce(produce_topic=produce_image_topic, payload=produce_payload)
        self.logger.info('{} processed.'.format(token))
        self.consumer.commit()

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

    def upload_lpr_image_result(self, is_process_raw_image=False):
        filename = DEFAULT_NAME_LPR_IMAGE_RESULT if not is_process_raw_image else DEFAULT_NAME_LPR_RAW_IMAGE_RESULT
        encoded_image = encode_image_to_base64(filename)
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
            topic = kwargs.get('produce_topic')
            payload = kwargs.get('payload')
            self.producer.send(topic, payload)
            self.logger.info('payload sent to queue.')
        except Exception as err:
            self.logger.error("Produce Error : {}".format(err))
