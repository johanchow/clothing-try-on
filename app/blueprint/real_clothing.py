from flask import Blueprint, jsonify, request
from helper.resource import upload_resource_to_cos, copy_resource_to_cos, transform_to_bytes
from helper.logger import logger
from helper.mysql import execute_sql
from helper.image_recognition import is_image_clothing

real_clothing = Blueprint('real_clothing', __name__)

@real_clothing.post('/upload')
def upload():
  user_id = request.form.get('user_id')
  logger.info(f'收到clothing upload请求, user_id={user_id}')
  file = request.files['clothing_image']
  file_bytes = transform_to_bytes(file)
  confirmed = request.form.get('confirmed')
  # 检查文件是否有文件名
  if file.filename == '':
    return jsonify({"message": "请选择图片上传"}), 400
  # if not confirmed and not is_image_clothing(file):
  #   return jsonify({"code": 200, "message": "图片应该不是衣服"}), 200
  # 上传到cos
  logger.info(f'start upload image to cos: {file.filename}')
  id, url = upload_resource_to_cos(file_bytes, file.filename)
  if id is None:
    return jsonify({"message": "上传失败"}), 200
  logger.info(f'start write to db, id={id}, url={url}')
  # 保存到数据库
  with execute_sql() as cursor:
    cursor.execute("SELECT * FROM real_clothing WHERE id = %s", (id,))
    clothing = cursor.fetchone()
    if (clothing is None):
      cursor.execute("INSERT INTO real_clothing (id, user_id, image_url) VALUES (%s, %s, %s)", (id, user_id, url))
    else:
      cursor.execute("UPDATE real_clothing SET user_id = %s, image_url = %s WHERE id = %s", (user_id, url, id))
  logger.info(f'完成clothing upload请求: id={id}')
  return jsonify({'resource_id': id}), 200

@real_clothing.post('/copy')
def copy():
  data = request.get_json(force = True)
  id, url = copy_resource_to_cos(data['url'])
  return jsonify({"url": url}), 200
