# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 
"""
from threading import Thread
from dcmtks.back_process import back_server
from datacenter import create_app
#
#
app = create_app()
# from app import app
# app.app_context().push()

if __name__ == "__main__":
    app.config['back_task'] = Thread(target=back_server)
    app.config['back_task'].setDaemon(True)
    app.config['back_task'].start()
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
    # app.run(host='127.0.0.1', port=8000, debug=False, threaded=False)
