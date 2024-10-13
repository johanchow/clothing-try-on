from flask import Blueprint, jsonify, request, send_file
import json
import cv2
import numpy as np
from helper.mysql import execute_sql
from helper.request import request_idm_vton
from helper.image import imread_image_from_url, imread_from_file, copy_polygon_area
from helper.util import generate_uuid
from io import BytesIO
import threading
from PyPatchMatch import patch_match

try_on = Blueprint('try_on', __name__)

selection_picture_dict = {
  'male': {
    'child': {
      'urban': [
      ],
      'scenery': [
      ],
      'cartoon': [
      ]
    },
    'junior': {
      'urban': [
        'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-young-street-1.jpg'
      ],
      'scenery': [
        'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-young-scenary-1.png'
      ],
      'pure': [
        'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-yound-pure-1.jpg'
      ]
    },
    'senior': {
      'urban': [
      ],
      'scenery': [
      ],
      'cartoon': [
      ]
    }
  },
  'female': {
    'child': {
      'urban': [
      ],
      'scenery': [
      ],
      'cartoon': [
      ]
    },
    'junior': {
      'urban': [
        'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-young-street-1.jpg'
      ],
      'scenery': [
        'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-young-scenary-1.png'
      ],
      'pure': [
        'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-yound-pure-1.jpg'
      ]
    },
    'senior': {
      'urban': [
      ],
      'scenery': [
      ],
      'cartoon': [
      ]
    }
  }
  # 'male-child': 'a Asian boy',
  # 'female-child': 'a Asian cute girl',
  # 'male-junior': 'a Asian handsome man',
  # 'female-junior': 'a Asian beautiful smiling lady, long hair',
  # 'male-senior': 'a Asian old healthy man',
  # 'female-senior': 'a Asian old healthy woman',
  # 'full-body': 'full body',
  # 'upper-body': 'upper body',
  # 'lower-body': 'lower body',
  # 'urban': 'urban',
  # 'scenery': 'scenery',
  # 'cartoon': 'cartoon'
}


@try_on.post('/generate')
def generate():
  print('receive call /generate')
  data = request.get_json(force = True)
  gender, age, view, style = data['gender'], data['age'], data['view'], data['style']
  text_prompt = gender
  text_prompt += ' - ' + age
  text_prompt += ' - ' + view
  text_prompt += ' - ' + style
  human_url, = selection_picture_dict[gender][age][style]

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
  task_thread = threading.Thread(target=generate_try_on, args=(try_on_id, human_url, real_clothing_url))
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

def generate_try_on(try_on_id, human_url, clothing_url):
  print('thread run generate try_on image: ', try_on_id)
  generation_url = request_idm_vton(human_url, clothing_url)
  with execute_sql() as cursor:
    if (generation_url):
      cursor.execute("update try_on_generation set status = %s, generation_image_url = %s where id = %s", ('finished', generation_url, try_on_id))
    else:
      cursor.execute("update try_on_generation set status = %s where id = %s", ('failed', try_on_id))
