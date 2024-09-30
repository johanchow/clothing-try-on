from flask import Blueprint

ai_picture = Blueprint('ai_picture', __name__)

@ai_picture.route('/')
def show():
  print('111')
  pass
