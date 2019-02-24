# 影像数据管理工具
dicom数据队列下载工具,账号注册,下载任务提交到审批
*医学影像科研数据管理更便捷*
以下提供了三种部署方式
## 用pipenv构建

```
$ git clone https://github.com/greyli/albumy.git
$ cd albumy
$ pipenv install --dev --pypi-mirror https://mirrors.aliyun.com/pypi/simple
$ pipenv shell
$ flask forge
$ flask run
* Running on http://127.0.0.1:5000/
```
测试账户:
* 用户名: `liuweipeng`
* 密码: `123456`

## windows用户安装

```
pip install -r requirements.txt
set FLASK_APP=datacenter
flask initdb
flask init
```

## docker 运行
构建docker
```angular2html
cd center
docker build -t webenv:2.01 .
```
运行,挂载目录必须是完整路径
```
cd ..
docker run -v ~/center:/app -p 8000:8000 -p 10001:10001 -i -t webenv:2.01 python run.py
```


## License

This project is licensed under the MIT License (see the
[LICENSE](LICENSE) file for details).
