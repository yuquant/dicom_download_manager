# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def get_logger(logger_name=None, log_path=None, debug=False):
    if logger_name:
        log_name = logger_name
    else:
        log_name = __name__
    logger = logging.getLogger(log_name)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not os.path.exists('/data/log'):
        os.makedirs('/data/log')
    if log_path:
        path = log_path
    else:
        path = os.path.join('/data/log', 'logger.log')
    fh = RotatingFileHandler(path, encoding='UTF-8', maxBytes=1024*1024, backupCount=100)
    logger.addHandler(fh)

    return logger


def set_logger():
    FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    DATEFMT = '%a, %d %b %Y %H:%M:%S'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=DATEFMT)

    # rotateHandler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=100)
    # rotateHandler.setLevel(logging.DEBUG)
    # rotateHandler.setFormatter(logging.Formatter(FORMAT, DATEFMT))
    # logging.getLogger('').addHandler(rotateHandler)


if __name__ == "__main__":
    set_logger()
    logger = get_logger(__name__, log_path=None, debug=True)
    logger.info('datacenter starting')