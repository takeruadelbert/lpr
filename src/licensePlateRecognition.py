import os

import cv2
import numpy as np

from src.misc.value import DATA_ALLOW_LIST, CONFIDENCE_LIMIT, DEFAULT_SCALE, LICENSE_PLATE_LABEL, \
    DEFAULT_JPG_IMAGE_QUALITY, DEFAULT_NAME_LPR_IMAGE_RESULT, DEFAULT_NAME_LPR_RAW_IMAGE_RESULT, UNDETECTED, \
    UNKNOWN_VEHICLE

parent_dir = os.getcwd()
weight = '{}{}'.format(parent_dir, os.getenv("YOLO_WEIGHT", "/yolo-obj_final.weights"))
config = '{}{}'.format(parent_dir, os.getenv("YOLO_CONFIG", "/yolo-obj.cfg"))
classPath = '{}{}'.format(parent_dir, os.getenv("YOLO_CLASS", "/classes.txt"))


def crop_bounding_box(img, x, y, x_plus_w, y_plus_h):
    return img[y:y_plus_h, x:x_plus_w]


def get_output_layers(net):
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers


class LicensePlateRecognition:
    def __init__(self, reader, is_process_raw_image=False):
        self.reader = reader
        self.image = None
        self.width = None
        self.height = None
        self.classes = open(classPath).read().strip().split("\n")
        self.is_process_raw_image = is_process_raw_image

    def set_image(self, image):
        self.image = image
        self.width = image.shape[1]
        self.height = image.shape[0]

    def draw_bounding_box(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h, license_plate_number=None):
        if license_plate_number is None:
            label = "{}: {:.4f}".format(str(self.classes[class_id]), confidence)
        else:
            label = "{}: {}".format(str(self.classes[class_id]), license_plate_number)
        color = (213, 255, 0)
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def optical_character_recognition(self, img):
        return self.reader.readtext(img, detail=0, allowlist=DATA_ALLOW_LIST, paragraph=True, mag_ratio=3.5)

    def get_data_from_output_layer(self, outs, class_ids, confidences, boxes):
        conf_threshold = 0.5
        nms_threshold = 0.4
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > CONFIDENCE_LIMIT:
                    center_x = int(detection[0] * self.width)
                    center_y = int(detection[1] * self.height)
                    w = int(detection[2] * self.width)
                    h = int(detection[3] * self.height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])
        return cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    def run(self):
        net = cv2.dnn.readNet(weight, config)
        blob = cv2.dnn.blobFromImage(self.image, DEFAULT_SCALE, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(get_output_layers(net))

        class_ids = []
        confidences = []
        boxes = []
        indices = self.get_data_from_output_layer(outs, class_ids, confidences, boxes)
        output = {
            "type": UNKNOWN_VEHICLE,
            "license_plate_number": UNDETECTED
        }

        for i in indices:
            i = i[0]
            box = boxes[i]
            x = box[0]
            y = box[1]
            w = box[2]
            h = box[3]
            class_label = self.classes[class_ids[i]]
            result = None
            if class_label.lower() == LICENSE_PLATE_LABEL:
                detected_image = crop_bounding_box(self.image, round(x), round(y), round(x + w), round(y + h))
                result = self.optical_character_recognition(detected_image)
                if result:
                    output["license_plate_number"] = result[0]
            else:
                output["type"] = class_label
            output["confidence"] = confidences[i]
            self.draw_bounding_box(self.image, class_ids[i], confidences[i], round(x), round(y), round(x + w),
                                   round(y + h), result)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),
                            int(os.getenv("JPG_IMAGE_QUALITY", DEFAULT_JPG_IMAGE_QUALITY))]
            filename = DEFAULT_NAME_LPR_IMAGE_RESULT if not self.is_process_raw_image else DEFAULT_NAME_LPR_RAW_IMAGE_RESULT
            cv2.imwrite('{}'.format(filename), self.image, encode_param)
        return output
