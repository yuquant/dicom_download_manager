# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 
"""
from threading import Thread
from dcmtks.back_process import back_server
from datacenter import create_app
from dcmtks.log import get_logger


app = create_app(config_name='development')

if __name__ == "__main__":
    logger = get_logger(__name__, log_path=None, debug=True)
    logger.info('datacenter starting')
    app.config['back_task'] = Thread(target=back_server)
    app.config['back_task'].setDaemon(True)
    app.config['back_task'].start()
    # debug=False才能保证后台程序正常运行
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
