import logging
import re
from logging.handlers import TimedRotatingFileHandler

from broker.broker import Broker
from helper.generalHelper import create_log_dir_if_does_not_exists
from misc.value import DEFAULT_APP_NAME

logger = logging.getLogger(DEFAULT_APP_NAME)


def setup_log():
    log_format = "%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s"
    log_level = logging.DEBUG
    handler = TimedRotatingFileHandler("log/{}.log".format(DEFAULT_APP_NAME), when="midnight", interval=1)
    handler.setLevel(log_level)
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    handler.suffix = "%Y%m%d"
    handler.extMatch = re.compile(r"^\d{8}$")
    logger.setLevel(log_level)
    logger.addHandler(handler)


if __name__ == "__main__":
    create_log_dir_if_does_not_exists('log')
    setup_log()
    broker = Broker(logger)
    broker.consume()
