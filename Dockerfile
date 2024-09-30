FROM tiangolo/uwsgi-nginx-flask:python3.8

COPY . /app

# 其他部分
RUN pip install -r requirements.txt

