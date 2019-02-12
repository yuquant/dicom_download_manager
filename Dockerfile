# webenv:2.01 datacenter的环境
# ubuntu/aienv:1.01 此docker已经在我本地构建好,包含dcmtk以及python3
FROM ubuntu/aienv:1.01
MAINTAINER Jason "yuyoujiutian@gmail.com"

ADD requirements.txt /app
# 安装 requirements.txt 中指定的任何所需软件包，vim无须安装，将需要修改的文件放在外部
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 使端口 80 可供此容器外的环境使用,8000为aiservice服务端的接收报告请求的端口号，10000为pacs接收dicom图像的端口号
EXPOSE 80
EXPOSE 8000
EXPOSE 10001