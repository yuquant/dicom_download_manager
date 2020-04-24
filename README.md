# 影像数据管理工具

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
flask forge
```

## docker 运行
构建docker
```angular2html
cd center
docker build -t webenv:2.01 .
```
运行
```
cd ..
docker run -v /home/public/liuweipeng/datacenter2/center/:/app -v /home/pictures/WinShare/DcmData/:/app/downloads -v /etc/localtime:/etc/localtime:ro -p 8080:8000 -p 10002:10002 -i -t webenv:2.01 python run.py
```


## License

This project is licensed under the MIT License (see the
[LICENSE](LICENSE) file for details).
