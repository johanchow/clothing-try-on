from flask import Blueprint, Response
from helper.resource import get_resource_from_cos

static = Blueprint('static', __name__)

@static.get('/diy-image')
def getDiyImageHtml():
  html_content = get_resource_from_cos('diy-image/index.html')
  return Response(html_content, mimetype='text/html')
