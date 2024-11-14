import io
import os
import requests
import mimetypes
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from helper.logger import logger
from helper.util import hash_string

secret_id = os.getenv('COS_SECRET_ID')
secret_key = os.getenv('COS_SECRET_KEY')
region = os.getenv('COS_REGION')  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
                           # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
token = None               # 如果使用永久密钥不需要填入 token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见 https://cloud.tencent.com/document/product/436/14048
scheme = 'https'           # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
bucket = os.getenv('COS_BUCKET')

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
client = CosS3Client(config)

def upload_resource_to_cos(resource_file, key):
  """upload file to cos
  :param resource_file(string): file content
  :param key(string): cos key
  """
  response = client.put_object(
    Bucket=bucket,
    Body=resource_file,
    Key=key,
    StorageClass='STANDARD',
    EnableMD5=False
  )
  logger.info('upload resource file to cos successfully: ', response)
  url = 'http://' + bucket + '.cos.' + region + '.myqcloud.com/' + key
  return response['ETag'].strip('"'), url

def copy_resource_to_cos(resource_url):
  """copy resource from url and upload to cos
  :param resource_url(string): resource file url
  """
  response = requests.get(resource_url, stream=True)
  response.raise_for_status()  # check if success
  # file_size = int(response.headers.get('Content-Length', 0))
  content_type = response.headers['content-type']
  extension = mimetypes.guess_extension(content_type)
  key = hash_string(resource_url)
  return upload_resource_to_cos(response.content, key+extension)

def get_resource_from_cos(path_key, type = 'text'):
  """get resource from cos
  :param path_key(string): path
  :param type(string): text or binary
  """
  response = client.get_object(
    Bucket=bucket,
    Key=path_key
  )
  # 获取文件内容
  if type == 'binary':
    content = response['Body'].get_raw_stream().read()
  else:
    content = response['Body'].read().decode('utf-8')
  return content

def transform_to_bytes(file):
  # 如果 file 不是 BytesIO 类型，则将其转换为 BytesIO
  if not isinstance(file, io.BytesIO):
      # 读取 file 的内容并将其写入到 BytesIO 中
      file_content = file.read()
      # 创建一个新的 BytesIO 对象，并将内容写入
      file_bytes = io.BytesIO(file_content)
      # 重置流位置到开头
      file_bytes.seek(0)
  else:
      # 如果 file 是 BytesIO，确保指针位置在开头
      file_bytes = file
      file_bytes.seek(0)

  return file_bytes
