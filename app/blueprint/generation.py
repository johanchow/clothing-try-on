from flask import Blueprint, jsonify, request, send_file
from helper.resource import upload_resource_to_cos
from helper.mysql import execute_sql

generation = Blueprint('generation', __name__)

@generation.post('/update')
def update():
  image = request.files['updated_image']
  user_id = request.form.get('user_id')
  generation_id = request.form.get('id')
  cos_id, generation_clothing_image_url = upload_resource_to_cos(image, user_id+'__'+image.filename)
  with execute_sql() as cursor:
    cursor.execute(
      "Update try_on_generation set generation_image_url = %s Where id = %s",
      (generation_clothing_image_url, generation_id)
    )
  return jsonify({"id": generation_id, "generation_image_url": generation_clothing_image_url}), 200
