import io
from flask import Blueprint, jsonify, request
from helper.mysql import execute_sql
from helper.resource import upload_resource_to_cos, transform_to_bytes
from helper.logger import logger
from helper.image_recognition import detect_human_count

person = Blueprint('person', __name__)

@person.post('/upload')
def show():
  user_id = request.form.get('user_id')
  logger.info(f'收到person upload请求: user_id={user_id}')
  file = request.files['person_image']
  file_bytes = transform_to_bytes(file)
  # 检查文件是否有文件名
  if file.filename == '':
    return jsonify({"error": "请选择图片上传"}), 400
  human_count = detect_human_count(file_bytes)
  logger.info(f'person upload请求里user_id={user_id}上传图片有{human_count}个人')
  # 上传到cos
  logger.info(f'start upload image to cos: filename={file.filename}')
  id, url = upload_resource_to_cos(file_bytes, file.filename)
  logger.info(f'start write to db: id={id}, url={url}')
  # 保存到数据库
  with execute_sql() as cursor:
    cursor.execute("SELECT * FROM human_photo WHERE id = %s", (id,))
    human = cursor.fetchone()
    if (human is None):
      cursor.execute("INSERT INTO human_photo (id, user_id, url) VALUES (%s, %s, %s)", (id, user_id, url))
  logger.info('完成upload请求')
  if human_count > 1:
    return jsonify({"code": 5000, "message": "图片里超过1个人", "resource_id": id}), 200
  elif human_count < 1:
    return jsonify({"code": 5000, "message": "图片里没有找到人", "resource_id": id}), 200
  else:
    return jsonify({"resource_id": id}), 200
