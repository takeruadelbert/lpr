import easyocr
from broker.broker import Broker
from src.licensePlateRecognition import *

if __name__ == "__main__":
    broker = Broker()
    broker.consume()

    # print("Loading Reader ...")
    # reader = easyocr.Reader(['id'], gpu=True)
    #
    # while True:
    #     imagePath = input("Enter Image Path : ")
    #     image = cv2.imread(imagePath)
    #     lpr = LicensePlateRecognition(reader, image)
    #     lpr.run()
