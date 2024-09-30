from flask import Blueprint, jsonify, request
from helper.resource import upload_resource_to_cos, copy_resource_to_cos
from helper.mysql import execute_sql

real_clothing = Blueprint('real_clothing', __name__)

@real_clothing.post('/upload')
def upload():
  print('收到upload请求')
  file = request.files['clothing_image']
  print('file: ', file)
  user_id = request.form.get('user_id')
  print('user_id: ', user_id)
  # 检查文件是否有文件名
  if file.filename == '':
    return jsonify({"error": "请选择图片上传"}), 400
  print(user_id)
  # 上传到cos
  id, url = upload_resource_to_cos(file, file.filename)
  print(id)
  print(url)
  # 保存到数据库
  with execute_sql() as cursor:
    cursor.execute("SELECT * FROM real_clothing WHERE id = %s", (id,))
    clothing = cursor.fetchone()
    if (clothing is None):
      cursor.execute("INSERT INTO real_clothing (id, user_id, image_url) VALUES (%s, %s, %s)", (id, user_id, url))
  return jsonify({'resource_id': id}), 200

@real_clothing.post('/copy')
def copy():
  data = request.get_json(force = True)
  id, url = copy_resource_to_cos(data['url'])
  return jsonify({"url": url}), 200
