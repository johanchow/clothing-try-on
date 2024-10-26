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
