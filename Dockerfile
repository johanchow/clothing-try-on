FROM tiangolo/uwsgi-nginx-flask:python3.12

COPY ./app /app

# 其他部分
RUN pip install -r requirements.txt

