from flask import Blueprint, jsonify, request, send_file
import cv2
import numpy as np
from helper.mysql import execute_sql
from helper.request import request_fooocus_try_on
from helper.image import imread_image_from_url, copy_polygon_area
from helper.util import generate_uuid
from io import BytesIO
import threading

try_on = Blueprint('try_on', __name__)

keyword_to_prompt = {
  'male-child': 'a Asian boy',
  'female-child': 'a Asian cute girl',
  'male-junior': 'a Asian handsome man',
  'female-junior': 'a Asian beautiful smiling lady, long hair',
  'male-senior': 'a Asian old healthy man',
  'female-senior': 'a Asian old healthy woman',
  'full-body': 'full body',
  'upper-body': 'upper body',
  'lower-body': 'lower body',
  'urban': 'urban',
  'scenery': 'scenery',
  'cartoon': 'cartoon'
}


@try_on.post('/generate')
def generate():
  print('receive call /generate')
  data = request.get_json(force = True)
  text_prompt = ''
  text_prompt += keyword_to_prompt[data['gender'] + '-' + data['age']]
  if (data['view']):
    text_prompt += ', ' + keyword_to_prompt[data['view']]
  if (data['style']):
    text_prompt += ', ' + keyword_to_prompt[data['style']]

  real_clothing_id = data['real_clothing_id']
  try_on_id = generate_uuid(10)
  with execute_sql() as cursor:
    print('real_clothing_id: ', real_clothing_id)
    cursor.execute("Select * from real_clothing where id = %s", (real_clothing_id,))
    real_clothing = cursor.fetchone()
    real_clothing_url = real_clothing['image_url']
    cursor.execute(
      "INSERT INTO try_on_generation (id, real_clothing_id, user_id, text_prompt, status) VALUES (%s, %s, %s, %s, %s)",
      (try_on_id, real_clothing_id, data['user_id'], text_prompt, 'processing')
    )
  # 启动异步任务
  task_thread = threading.Thread(target=generate_try_on, args=(try_on_id, text_prompt, real_clothing_url))
  task_thread.start()
  print('finish call /generate: ', real_clothing_id)
  return jsonify({'try_on_id': try_on_id}), 200

@try_on.post('/list-history')
def listHistory():
  data = request.get_json(force = True)
  print(data)
  user_id = data['user_id']
  if (user_id is None):
    jsonify({'code': 400, 'message': '没有用户id信息'})
    return
  with execute_sql() as cursor:
    cursor.execute("Select * from try_on_generation where user_id = %s order by create_time desc", (user_id,))
    try_on_list = cursor.fetchall()
    return jsonify({"try_on_list": try_on_list}), 200

def generate_try_on(try_on_id, text_prompt, clothing_url):
  print('thread run generate try_on image: ', try_on_id)
  generation_url = request_fooocus_try_on(text_prompt, clothing_url)
  with execute_sql() as cursor:
    if (generation_url):
      cursor.execute("update try_on_generation set status = %s, generation_image_url = %s where id = %s", ('finished', generation_url, try_on_id))
    else:
      cursor.execute("update try_on_generation set status = %s where id = %s", ('failed', try_on_id))

@try_on.post('/erase-rectangle')
def erase_polygon():
  print('receive call /erase-rectangle')
  # 获取前端传递的多边形坐标
  data = request.get_json(force = True)
  print('data: ', data)
  img = imread_image_from_url(data['generation_image_url'])
  polygon = np.array(
    [[int(point[0]), int(point[1])] for point in data['polygon_coordinates']],
    np.int32
  )
  polygon = polygon.reshape((-1, 1, 2))
  # 创建掩码
  mask = np.zeros(img.shape[:2], dtype=np.uint8)

  # 填充多边形区域
  cv2.fillPoly(mask, [polygon], 255)

  # 清除多边形区域，保留背景
  result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

  # 将处理后的图像编码为 jpeg
  _, buffer = cv2.imencode('.jpg', result)
  io_buf = BytesIO(buffer)

  return send_file(io_buf, mimetype='image/jpeg')

@try_on.post('/copy-to-generation-from-source')
def update_generation_image():
  print('receive call /erase-rectangle')
  # 获取前端传递的多边形坐标
  data = request.get_json(force = True)
  print('data: ', data)
  source_image = imread_image_from_url(data['source_image_url'])
  generation_image = imread_image_from_url(data['generation_image_url'])
  print('start copy')
  result = copy_polygon_area(source_image, data['source_coordinates'], generation_image, data['generation_coordinates'])
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
