import os
from io import BytesIO
import numpy as np
import tensorflow as tf
import logging
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
from helper.resource import get_resource_from_cos

# 本地开发使用，启动tensorflow时候默认下载会要求ssl
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 加载预训练的 EfficientNetB0 模型
model_path = './model/efficientnetb0.h5'
if os.getenv("SERVER_ENV"):
  model_path = './app/model/efficientnetb0.h5'
model = EfficientNetB0(weights=model_path)

def classify_image(img_bytes):
  '''
  利用预训练的 EfficientNetB0 模型对图片(BytesIO流)进行分类
  '''
  # 加载图片并将其调整为模型需要的输入尺寸
  img = image.load_img(img_bytes, target_size=(224, 224))  # EfficientNetB0 的输入尺寸为 224x224
  img_array = image.img_to_array(img)  # 转换为 numpy 数组
  img_array = np.expand_dims(img_array, axis=0)  # 增加 batch 维度
  img_array = preprocess_input(img_array)  # 预处理为模型需要的格式

  # 使用模型进行预测
  predictions = model.predict(img_array)

  # 将预测结果解码为可读标签
  decoded_predictions = decode_predictions(predictions, top=5)[0]

  return decoded_predictions

clothing_labels = ['dress', 'pants', 'skirt', 'coat', 'jacket']
def is_image_clothing(img_file):
  '''
  判断图片(File流)是否是衣服
  '''
  # 将上传的文件对象转换为 BytesIO 流
  img_bytes = BytesIO(img_file.read())
  logging.debug('start to classify image')
  predictions = classify_image(img_bytes)
  most_likely1_label, most_likely1_score = predictions[0][1], predictions[0][2]
  most_likely2_label, most_likely2_score = predictions[1][1], predictions[1][2]
  logging.info(f'image recognition result: {most_likely1_label}={most_likely1_score}; {most_likely2_label}={most_likely2_score}')
  if most_likely1_label not in clothing_labels:
     return False
  total_score = most_likely1_score
  if most_likely2_label in clothing_labels:
      total_score += most_likely2_score
  if total_score > 0.5:
     return True
  return False

def init_cnn_model():
  '''
  初始化模型，加载预训练模型
  '''
  global cnn_model
  print('start to init cnn model')
  # 加载预训练的 EfficientNetB0 模型
  local_model_path = './efficientnetb0.h5'
  with open(local_model_path, 'wb') as f:
    f.write(get_resource_from_cos('libs/efficientnetb0.h5', 'binary'))
  cnn_model = EfficientNetB0(weights=local_model_path)
  print('finish to init cnn model')
