# 基础镜像
FROM tiangolo/uwsgi-nginx-flask:python3.12

# 安装系统依赖和 OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
RUN apt-get install -y libopencv-dev

# 设置 PKG_CONFIG_PATH
ENV PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig:$PKG_CONFIG_PATH

COPY ./app /app

# 切换到 /app/PyPatchMatch 目录
WORKDIR /app/PyPatchMatch
# 执行 make 命令
RUN make
# 切换回原始的 /app 目录（如果需要继续其他操作）
WORKDIR /app

# 其他部分
RUN pip install -r requirements.txt

