import os

import cv2
import numpy as np


def crop_bounding_box(img, x, y, x_plus_w, y_plus_h):
    return img[y:y_plus_h, x:x_plus_w]


def get_output_layers(net):
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers


class LicensePlateRecognition:
    scale = 0.00392  # 1 / 255
    weight = os.getcwd() + os.getenv("yolo-weight", "/yolo-obj_final.weights")
    config = os.getcwd() + os.getenv("yolo-config", "/yolo-obj.cfg")
    classPath = os.getcwd() + os.getenv("yolo-class", "/classes.txt")
    dataAllowList = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self, reader, image):
        self.reader = reader
        self.image = image
        self.width = image.shape[1]
        self.height = image.shape[0]
        self.classes = open(self.classPath).read().strip().split("\n")
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))

    def draw_bounding_box(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h, license_plate_number):
        if license_plate_number is None:
            label = "{}: {:.4f}".format(str(self.classes[class_id]), confidence)
        else:
            label = license_plate_number
        color = self.colors[class_id]
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def optical_character_recognition(self, img):
        return self.reader.readtext(img, detail=0, allowlist=self.dataAllowList, paragraph=True, mag_ratio=3)

    def get_data_from_output_layer(self, outs, class_ids, confidences, boxes):
        conf_threshold = 0.5
        nms_threshold = 0.4
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
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
        net = cv2.dnn.readNet(self.weight, self.config)
        blob = cv2.dnn.blobFromImage(self.image, self.scale, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(get_output_layers(net))

        class_ids = []
        confidences = []
        boxes = []
        indices = self.get_data_from_output_layer(outs, class_ids, confidences, boxes)

        for i in indices:
            i = i[0]
            box = boxes[i]
            x = box[0]
            y = box[1]
            w = box[2]
            h = box[3]
            detected_image = crop_bounding_box(self.image, round(x), round(y), round(x + w), round(y + h))
            result = self.optical_character_recognition(detected_image)[0]
            print('result = ', result)
            self.draw_bounding_box(self.image, class_ids[i], confidences[i], round(x), round(y), round(x + w),
                                   round(y + h), result)

        cv2.imshow("LPR Detection", self.image)
        cv2.imwrite("lpr-detection.jpg", self.image)
        cv2.waitKey()
        cv2.destroyAllWindows()
