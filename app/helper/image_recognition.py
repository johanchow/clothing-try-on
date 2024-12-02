import os
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
from ultralytics import YOLO

# 本地开发使用，启动tensorflow时候默认下载会要求ssl
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 加载预训练的 EfficientNetB0 模型
model_path = './model/efficientnetb0.h5'
if os.getenv("SERVER_ENV") == 'dev':
  model_path = './app/model/efficientnetb0.h5'
classification_model = EfficientNetB0(weights=model_path)

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
  predictions = classification_model.predict(img_array)

  # 将预测结果解码为可读标签
  decoded_predictions = decode_predictions(predictions, top=5)[0]

  return decoded_predictions

upper_clothing_labels = [
  'shirt', 'coat', 'sweater', 'jacket', 'wool', 'cardigan', 'jersey', 'vest'
]
lower_clothing_labels = ['pants', 'trousers', 'skirt', 'jean']
dress_clothing_labels = ['pajama', 'overskirt' ,'gown', 'dress']

def detect_clothing_category(img_bytes):
  '''
  判断图片(File流)是否是衣服
  '''
  predictions = classify_image(img_bytes)
  img_bytes.seek(0)
  most_likely1_label, most_likely1_score = predictions[0][1], predictions[0][2]
  most_likely2_label, most_likely2_score = predictions[1][1], predictions[1][2]
  print(f'image recognition result: {most_likely1_label}={most_likely1_score}; {most_likely2_label}={most_likely2_score}')
  if any([label in most_likely1_label for label in upper_clothing_labels]):
    label1_clothing_category = 'upper_body'
  elif any([label in most_likely1_label for label in lower_clothing_labels]):
    label1_clothing_category = 'lower_body'
  elif any([label in most_likely1_label for label in dress_clothing_labels]):
    label1_clothing_category = 'dresses'
  else:
    label1_clothing_category = None
  if not label1_clothing_category:
     return None
  total_score = most_likely1_score

  if any([label in most_likely2_label for label in upper_clothing_labels]):
    label2_clothing_category = 'upper_body'
  elif any([label in most_likely2_label for label in lower_clothing_labels]):
    label2_clothing_category = 'lower_body'
  elif any([label in most_likely2_label for label in dress_clothing_labels]):
    label2_clothing_category = 'dresses'
  else:
    label2_clothing_category = None

  if label2_clothing_category:
      total_score += most_likely2_score
  if total_score > 0.5:
     return label1_clothing_category
  return None


# 加载预训练模型
yolo_model_path = './model/yolov8n.pt'
if os.getenv("SERVER_ENV") == 'dev':
  yolo_model_path = './app/model/yolov8n.pt'
yolo_model = YOLO(yolo_model_path)
def detect_human_count(img_bytes):
  image = Image.open(img_bytes)
  image_np = np.array(image)
  results = yolo_model(image_np)
  # 获取检测到的对象类别
  people = [det for det in results[0].boxes if det.cls == 0]  # 类别0通常是'person'
  img_bytes.seek(0)
  return len(people)
