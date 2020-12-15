import asyncio
import logging
import re
from logging.handlers import TimedRotatingFileHandler

from src.broker.broker import Broker
from src.helper.generalHelper import create_log_dir_if_does_not_exists
from src.misc.value import DEFAULT_APP_NAME

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


create_log_dir_if_does_not_exists('log')
setup_log()
broker = Broker(logger)


async def background_task():
    await asyncio.sleep(1)
    broker.consume()


async def main():
    while True:
        await background_task()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
