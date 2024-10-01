FROM tiangolo/uwsgi-nginx-flask:python3.12

# 安装系统依赖和 OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0

COPY ./app /app

# 其他部分
RUN pip install -r requirements.txt

