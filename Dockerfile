# 基础镜像
FROM tiangolo/uwsgi-nginx-flask:python3.12

# 替换为腾讯云的 Debian 镜像源
RUN echo "deb http://mirrors.tencentyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://mirrors.tencentyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.tencentyun.com/debian-security/ bookworm-security main contrib non-free-firmware" >> /etc/apt/sources.list

# 设置 pip 源为清华的镜像源
RUN mkdir -p /root/.config/pip && \
    echo "[global]" >> /root/.config/pip/pip.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> /root/.config/pip/pip.conf && \
    echo "trusted-host = pypi.tuna.tsinghua.edu.cn" >> /root/.config/pip/pip.conf

# 安装系统依赖和 OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
RUN apt-get install -y libopencv-dev

RUN apt-get install -y vim

# 设置 PKG_CONFIG_PATH
ENV PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig:$PKG_CONFIG_PATH

COPY ./app /app
COPY ./requirements.txt /app
COPY ./uwsgi.ini /app

# 切换到 /app/PyPatchMatch 目录
WORKDIR /app/PyPatchMatch
# 执行 make 命令
RUN make
# 切换回原始的 /app 目录（如果需要继续其他操作）
WORKDIR /app

# 设置多个环境变量
ENV SERVER_ENV=prod \
    TZ=Asia/Shanghai

# uswgi的日志输入文件
RUN touch /var/log/uwsgi.log

# 其他部分
pip cache purge
RUN pip install -r requirements.txt

