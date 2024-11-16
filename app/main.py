# from flask import Flask
# from flask_cors import CORS
from dotenv import load_dotenv
from blueprint.person import person
from blueprint.try_on import try_on
from blueprint.real_clothing import real_clothing
from blueprint.weixin_srv import weixin_srv
from blueprint.generation import generation
from blueprint.web_static import web_static
from app import app
import middleware.utc_8

load_dotenv()
# app = Flask(__name__)
# CORS(app)
app.register_blueprint(try_on, url_prefix='/try-on')
app.register_blueprint(person, url_prefix='/person')
app.register_blueprint(real_clothing, url_prefix='/real-clothing')
app.register_blueprint(weixin_srv, url_prefix='/weixin-srv')
app.register_blueprint(generation, url_prefix='/generation')
app.register_blueprint(web_static, url_prefix='/web-static')
