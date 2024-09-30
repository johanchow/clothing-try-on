import os
import requests
from flask import Blueprint, request, jsonify

weixin_srv = Blueprint('weixin', __name__)

@weixin_srv.post('/get-openid')
def get_openid():
  data = request.get_json(force = True)
  url = "https://api.weixin.qq.com/sns/jscode2session"
  url += "?appid=" + os.getenv("WEIXIN_APPID")
  url += "&secret=" + os.getenv("WEIXIN_SECRET")
  url += "&js_code=" + data['code']
  url += "&grant_type=authorization_code"
  url += "&connect_redirect=1"

  # 发送get请求到url
  response = requests.get(url)
  # 返回json格式的数据
  return jsonify(response.json()), 200
