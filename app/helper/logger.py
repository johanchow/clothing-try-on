import logging

# 自定义日志格式
log_format = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format, filename='x.log', filemode='a')

# 创建一个StreamHandler来输出到标准输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # 设置控制台输出的最低级别

# 为控制台处理器设置相同的格式
console_handler.setFormatter(logging.Formatter(log_format))

# 获取当前的logger，并添加控制台处理器
logger = logging.getLogger()
logger.addHandler(console_handler)
