# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 
"""

from datacenter import create_app
app = create_app()


if __name__ == "__main__":

    app.run(host='127.0.0.1', port=8000, debug=True, threaded=False)
