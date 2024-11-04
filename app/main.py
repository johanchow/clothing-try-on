from flask import Flask
from flask_cors import CORS
import logging
from dotenv import load_dotenv
from blueprint.ai_picture import ai_picture
from blueprint.try_on import try_on
from blueprint.real_clothing import real_clothing
from blueprint.weixin_srv import weixin_srv
from blueprint.generation import generation
from blueprint.web_static import web_static

# 自定义日志格式
log_format = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format, filename='x.log', filemode='a')

load_dotenv()
app = Flask(__name__)
CORS(app)
app.register_blueprint(try_on, url_prefix='/try-on')
app.register_blueprint(ai_picture, url_prefix='/ai-picture')
app.register_blueprint(real_clothing, url_prefix='/real-clothing')
app.register_blueprint(weixin_srv, url_prefix='/weixin-srv')
app.register_blueprint(generation, url_prefix='/generation')
app.register_blueprint(web_static, url_prefix='/web-static')
