import os
from io import BytesIO
import numpy as np
import tensorflow as tf
from helper.logger import logger
from tensorflow import keras
from tensorflow.keras.preprocessing import image

# 本地开发使用，启动tensorflow时候默认下载会要求ssl
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 加载预训练的Fashion Mnist CNN模型
model_path = './app/model/fashion_mnist_model.h5'
if os.getenv("SERVER_ENV") == 'prod':
  model_path = './model/mnist_fashion.h5'
model = keras.models.load_model(model_path)

def classify_image(img_bytes):
  '''
  利用fashion mnist数据预训练的CNN模型对图片(BytesIO流)进行分类
  '''
  # 加载图片并将其调整为模型需要的输入尺寸
  img = image.load_img(img_bytes, target_size=(28, 28), color_mode='grayscale')  # EfficientNetB0 的输入尺寸为 224x224
  img_array = image.img_to_array(img)  # 转换为 numpy 数组
  img_array = np.expand_dims(img_array, axis=0)  # 增加 batch 维度
  img_array = img_array / 255.0

  # 使用模型进行预测，并取出前 2 个预测结果
  scores = model.predict(img_array).tolist()[0]
  print(scores)
  top_2_indices = np.argsort(scores)[-2:]
  [top_1_index, top_2_index] = top_2_indices[::-1]

  return [(clothing_labels[top_1_index], scores[top_1_index]), (clothing_labels[top_2_index], scores[1])]

clothing_labels = [
  'T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
  'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot'
]
def is_image_clothing(img_file):
  '''
  判断图片(File流)是否是衣服
  '''
  # 将上传的文件对象转换为 BytesIO 流
  img_bytes = BytesIO(img_file.read())
  logger.debug('start to classify image')
  predictions = classify_image(img_bytes)
  most_likely1_label, most_likely1_score = predictions[0][0], predictions[0][1]
  most_likely2_label, most_likely2_score = predictions[1][0], predictions[1][1]
  logger.info(f'image recognition result: {most_likely1_label}={most_likely1_score}; {most_likely2_label}={most_likely2_score}')
  total_score = most_likely1_score + most_likely2_score
  if total_score > 0.2:
     return True
  return False
