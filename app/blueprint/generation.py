from flask import Blueprint, jsonify, request, send_file
import cv2
import numpy as np
from io import BytesIO
from helper.resource import upload_resource_to_cos
from helper.mysql import execute_sql
from helper.image import imread_image_from_url, copy_polygon_area
from PyPatchMatch import patch_match

generation = Blueprint('generation', __name__)

@generation.post('/update')
def update():
  image = request.files['updated_image']
  user_id = request.form.get('user_id')
  generation_id = request.form.get('id')
  cos_id, generation_clothing_image_url = upload_resource_to_cos(image, user_id+'__'+image.filename)
  with execute_sql() as cursor:
    cursor.execute(
      "Update try_on_generation set generation_image_url = %s Where id = %s",
      (generation_clothing_image_url, generation_id)
    )
  return jsonify({"id": generation_id, "generation_image_url": generation_clothing_image_url}), 200

@generation.post('/erase-polygon')
def erase_polygon():
  data = request.get_json(force = True)
  img = imread_image_from_url(data['generation_image_url'])
  cv2.imwrite('input_image.png', img)
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
  result = patch_match.inpaint(img, mask, patch_size=3)
  # result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

  # 将处理后的图像编码为 jpeg
  _, buffer = cv2.imencode('.jpg', result)
  io_buf = BytesIO(buffer)

  return send_file(io_buf, mimetype='image/jpeg')

@generation.post('/copy-to-generation-from-source')
def copy_source_to_generation_image():
  print('receive call /copy-to-generation-from-source')
  # 获取前端传递的多边形坐标
  data = request.get_json(force = True)
  print('data: ', data)
  source_image = imread_image_from_url(data['source_image_url'])
  generation_image = imread_image_from_url(data['generation_image_url'])
  print('start copy')
  result = copy_polygon_area(
    source_image,
    np.array(data['source_coordinates']),
    data['source_bounding_box'],
    generation_image,
    np.array(data['generation_coordinates']),
    data['generation_bounding_box'],
  )
  print('finish copy')

  # 将处理后的图像编码为 jpeg
  _, buffer = cv2.imencode('.jpg', result)
  io_buf = BytesIO(buffer)
  cv2.imwrite('result.jpg', result)
  return send_file(io_buf, mimetype='image/jpeg')
