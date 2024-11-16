from datetime import datetime, timedelta, timezone
from app import app
from email.utils import parsedate_to_datetime
import json

# 定义 UTC+8 时区
UTC_PLUS_8 = timezone(timedelta(hours=8))

# 递归转换 datetime 到 UTC+8
def convert(obj):
  if isinstance(obj, str):  # 假设 datetime 是 ISO 格式字符串
    try:
      # 1. 尝试解析为 ISO 格式时间
      dt = datetime.fromisoformat(obj)
    except ValueError:
      try:
        # 2. 尝试解析 HTTP 日期格式
        dt = parsedate_to_datetime(obj)
      except (TypeError, ValueError):
        return obj  # 如果解析失败，返回原始值
    # 设置时区为 UTC+8，但保留原时间值不变
    return dt.replace(tzinfo=UTC_PLUS_8).isoformat()
  elif isinstance(obj, dict):  # 如果是字典，递归处理
      return {key: convert(value) for key, value in obj.items()}
  elif isinstance(obj, list):  # 如果是列表，递归处理
      return [convert(item) for item in obj]
  else:
      return obj  # 其他类型直接返回


@app.after_request
def convert_datetime(response):
  if response.is_json:  # 检查响应是否是 JSON 格式
    data = json.loads(response.get_data(as_text=True))  # 解析 JSON 数据
    converted_data = convert(data)  # 转换嵌套结构中的 datetime
    response.set_data(json.dumps(converted_data))  # 将转换后的数据重新设置到响应中
  return response
