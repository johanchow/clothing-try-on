## 安装环境
1. 先清空当前虚拟环境；再创建虚拟环境，然后安装依赖包
```shell
rm -rf venv/
python -m venv venv
pip install -r requirements.txt
```
2. 查看已安装包的版本
```shell
pip list | grep numpy
```

## 本地开发
1. 设置环境变量，便于flask找到入口文件
```shell
export FLASK_APP=app/main.py
```

## 编译
```shell
# 进入到项目根目录
cp ../.env . # 复制.env文件到当前目录
docker build -t clothing-try-on .
```


## 启动运行
```shell
docker stop clothing-try-on-container # 停止容器
docker rm clothing-try-on-container # 删除旧容器
docker run -d -p 8080:80 --name clothing-try-on-container --env-file .env clothing-try-on
```

## 登录到容器里
```shell
docker exec -it clothing-try-on-container /bin/bash
```

