from io import BytesIO
from flask import Blueprint, jsonify, request, send_file
from concurrent.futures import ThreadPoolExecutor
import json
import cv2
import numpy as np
from helper.mysql import execute_sql
from helper.request import request_idm_vton
from helper.image import imread_image_from_url, imread_from_file, copy_polygon_area
from helper.util import generate_uuid
from helper.trie_human import trie_human
from PyPatchMatch import patch_match
from helper.logger import logger

try_on = Blueprint('try_on', __name__)

# 最大并发线程数，超出的请求将会自动排队等待
executor = ThreadPoolExecutor(max_workers=10)

@try_on.post('/generate')
def generate():
  logger.info('receive call /generate')
  data = request.get_json(force = True)
  real_clothing_id = data['real_clothing_id']
  clothing_category = data['clothing_category']
  if 'person_id' in data:
    human_photo_id = data['person_id']
    human_photo_sql = f"select * from human_photo where id = '{human_photo_id}'"
  elif 'real_clothing_id' in data:
    gender, age, bg, style = [data.get(k) for k in ['gender', 'age', 'bg', 'style']]
    human_photo_sql = 'select * from human_photo where 1 = 1'
    if gender:
      human_photo_sql += f" AND gender = '{gender}'"
    if age:
      human_photo_sql += f" and age = '{age}'"
    if bg:
      human_photo_sql += f" and bg = '{bg}'"
    if style:
      human_photo_sql += f" and style = '${style}'"
    human_photo_sql += f" ORDER BY RAND() LIMIT 1"
  else:
    return jsonify({'code': 400, 'message': '没有提供real_clothing_id 或 person_id'}), 200

  logger.info(f'human_photo_sql: {human_photo_sql}')
  try_on_id = generate_uuid(10)
  with execute_sql() as cursor:
    logger.info(f'real_clothing_id: {real_clothing_id}')
    cursor.execute("Select * from real_clothing where id = %s", (real_clothing_id,))
    real_clothing = cursor.fetchone()
    real_clothing_url = real_clothing['image_url']
    cursor.execute(human_photo_sql)
    human_photo = cursor.fetchone()
    human_photo_url, human_photo_id = human_photo['url'], human_photo['id']
    cursor.execute(
      "INSERT INTO try_on_generation (id, real_clothing_id, user_id, human_photo_id, status) VALUES (%s, %s, %s, %s, %s)",
      (try_on_id, real_clothing_id, data['user_id'], human_photo_id, 'processing')
    )
  # 启动异步任务
  executor.submit(generate_try_on, try_on_id, human_photo_url, real_clothing_url, clothing_category)
  print('finish call /generate: ', real_clothing_id)
  return jsonify({'try_on_id': try_on_id}), 200

@try_on.post('/list-history')
def listHistory():
  data = request.get_json(force = True)
  print('receive call /list-history')
  user_id = data['user_id']
  if (user_id is None):
    jsonify({'code': 400, 'message': '没有用户id信息'})
    return
  with execute_sql() as cursor:
    cursor.execute("Select * from try_on_generation where user_id = %s order by create_time desc", (user_id,))
    try_on_list = cursor.fetchall()
    return jsonify({"try_on_list": try_on_list}), 200

@try_on.post('/erase-rectangle')
def erase_polygon():
  print('receive call /erase-rectangle')
  img = imread_from_file(request.files['image'])
  cv2.imwrite('input_image.png', img)
  # 获取前端传递的多边形坐标
  polygon_coordinates = json.loads(request.form.get('polygon_coordinates'))
  polygon = np.array(
    [[int(point[0]), int(point[1])] for point in polygon_coordinates],
    np.int32
  )
  polygon = polygon.reshape((-1, 1, 2))
  # 创建掩码
  mask = np.zeros(img.shape[:2], dtype=np.uint8)

  # 填充多边形区域
  cv2.fillPoly(mask, [polygon], 255)

  # 清除多边形区域，保留背景(PatchMatch算法在清除大面积区域要优于cv2.inpaint)
  result = patch_match.inpaint(img, mask, patch_size=3)

  # 将处理后的图像编码为 jpeg
  _, buffer = cv2.imencode('.jpg', result)
  io_buf = BytesIO(buffer)

  return send_file(io_buf, mimetype='image/jpeg')

@try_on.post('/copy-to-generation-from-source')
def copy_source_to_generation_image():
  print('receive call /copy-to-generation-from-source')
  generation_image = imread_from_file(request.files['generation_image'])
  source_image = imread_image_from_url(request.form.get('source_image_url'))
  source_coordinates = json.loads(request.form.get('source_coordinates'))
  source_bounding_box = json.loads(request.form.get('source_bounding_box'))
  generation_coordinates = json.loads(request.form.get('generation_coordinates'))
  generation_bounding_box = json.loads(request.form.get('generation_bounding_box'))
  print('start copy')
  result = copy_polygon_area(
    source_image,
    np.array(source_coordinates),
    source_bounding_box,
    generation_image,
    np.array(generation_coordinates),
    generation_bounding_box,
  )
  print('finish copy')

  # 将处理后的图像编码为 jpeg
  _, buffer = cv2.imencode('.jpg', result)
  io_buf = BytesIO(buffer)
  cv2.imwrite('result.jpg', result)
  return send_file(io_buf, mimetype='image/jpeg')


@try_on.get('/detail')
def generate_detail():
  print('receive call /generate/detail')
  generation_id = request.args.get('id')
  with execute_sql() as cursor:
    cursor.execute('''
      select try_on_generation.*, real_clothing.image_url
      from try_on_generation
      left join real_clothing on try_on_generation.real_clothing_id = real_clothing.id
      where try_on_generation.id = %s
      ''', (generation_id,)
    )
    generation_row = cursor.fetchone()
    image_url, rest = generation_row['image_url'], {k: v for k, v in generation_row.items() if k != 'image_url'}
    generation = {
      **rest,
      'real_clothing': { 'id': generation_row['real_clothing_id'], 'image_url': image_url }
    }
  return jsonify(generation), 200

def generate_try_on(try_on_id, human_url, clothing_url, clothing_category):
  logger.info(f'线程开始生成图片: {try_on_id}')
  generation_url = request_idm_vton(human_url, clothing_url, clothing_category)
  with execute_sql() as cursor:
    if (generation_url):
      cursor.execute("update try_on_generation set status = %s, generation_image_url = %s where id = %s", ('finished', generation_url, try_on_id))
    else:
      cursor.execute("update try_on_generation set status = %s where id = %s", ('failed', try_on_id))
  logger.info(f'线程完成生成try_on图片: {try_on_id}')
