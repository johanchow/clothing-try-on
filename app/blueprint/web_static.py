from flask import Blueprint, Response
from helper.resource import get_resource_from_cos

web_static = Blueprint('web-static', __name__)

@web_static.get('/diy-image')
def getDiyImageHtml():
  html_content = get_resource_from_cos('diy-image/index.html')
  return Response(html_content, mimetype='text/html')
