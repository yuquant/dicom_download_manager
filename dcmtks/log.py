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
    default_log_path = '/app/log'
    log_fmt = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', '%Y%m%d %H:%M:%S')

    if logger_name:
        log_name = logger_name
    else:
        log_name = __name__
    logger = logging.getLogger(log_name)
    ch = logging.StreamHandler()
    ch.setFormatter(log_fmt)

    logger.addHandler(ch)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not os.path.exists(default_log_path):
        os.makedirs(default_log_path)
    if log_path:
        path = log_path
    else:
        path = os.path.join(default_log_path, 'ai-logger.log')
    fh = RotatingFileHandler(path, encoding='UTF-8', maxBytes=1024*1024, backupCount=100)
    fh.setFormatter(log_fmt)
    logger.addHandler(fh)

    return logger


if __name__ == "__main__":
    logger = get_logger(__name__, log_path=None, debug=True)
    logger.info('test starting')