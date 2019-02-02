# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
python manager.py db init
python manager.py db migrate
python manager.py db upgrade

set FLASK_APP=datacenter
flask initdict
flask initaedict
"""
from flask_script import Manager
from run import app
from flask_migrate import Migrate, MigrateCommand
from datacenter import db

# init  初始化一个迁移环境
# migrate 生成迁移文件
# upgrade 将迁移文件映射到表中
# 模型 -> 迁移文件 -> 表

manager = Manager(app)

# 1. 要使用flask_migrate, 必须绑定app和db
migrate = Migrate(app, db)

# 2. 把MigrateCommand命令添加到manager中
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
