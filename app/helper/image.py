import cv2
import numpy as np
import requests
from scipy.spatial import Delaunay

def imread_image_from_url(url):
  '''从远程URL读取图片
  '''
  # 通过 requests 获取远程图片数据
  response = requests.get(url)
  # 将数据转换为 numpy 数组
  img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
  # 使用 OpenCV 解码为图片
  img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
  return img


def get_polygon_mask(image_shape, polygon_points):
    """
    Create a mask for a polygon region.
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(polygon_points, dtype=np.int32)], 255)
    return mask

def extract_object_using_canny(src_image, src_mask):
    """
    Extract the object from the source image using Canny edge detection.
    """
    # Apply the mask to the source image
    masked_image = cv2.bitwise_and(src_image, src_image, mask=src_mask)

    # Convert to grayscale
    gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)

    # Apply Canny edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        raise ValueError("No object found in the specified source region.")

    # Assume the largest contour is the object
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(contour)

    object_image = src_image[y:y+h, x:x+w]
    object_mask = np.zeros_like(gray)
    cv2.drawContours(object_mask, [contour], -1, 255, thickness=cv2.FILLED)
    object_mask = object_mask[y:y+h, x:x+w]
    cv2.imwrite('object.png', object_image)

    return object_image, object_mask

def place_object(dst_image, dst_polygon, object_image, object_mask):
    """
    Place the object image onto the destination image, centered in the destination polygon.
    """
    dst_polygon_int = np.array(dst_polygon, dtype=np.int32)
    x, y, w, h = cv2.boundingRect(np.array(dst_polygon_int))
    center_x, center_y = x + w // 2, y + h // 2
    obj_h, obj_w = object_image.shape[:2]

    top_left_x = max(center_x - obj_w // 2, 0)
    top_left_y = max(center_y - obj_h // 2, 0)
    bottom_right_x = min(top_left_x + obj_w, dst_image.shape[1])
    bottom_right_y = min(top_left_y + obj_h, dst_image.shape[0])

    # Create a region of interest
    roi = dst_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    roi_mask = object_mask[:bottom_right_y-top_left_y, :bottom_right_x-top_left_x]

    # Blend the object image into the destination image using the mask
    roi[roi_mask > 0] = object_image[roi_mask > 0]
    dst_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x] = roi
    return dst_image

def resize_image(image, scale_width_factor, scale_height_factor):
  # 计算新尺寸
  new_width = int(image.shape[1] * scale_width_factor)
  new_height = int(image.shape[0] * scale_height_factor)
  # 缩放图像和掩码
  resized_image = cv2.resize(image, (new_width, new_height))
  return resized_image

def copy_polygon_area(src_img, src_points, dst_img, dst_points):
  src_mask = get_polygon_mask(src_img.shape, src_points)
  object_image, object_mask = extract_object_using_canny(src_img, src_mask)
  # 原图和目标图尺寸不一样，物体放置前根据图片比例做缩放
  width_ratio = dst_img.shape[1] / src_img.shape[1]
  height_ratio = dst_img.shape[0] / src_img.shape[0]
  resized_object_image = resize_image(object_image, 0.5, 0.5)
  resized_object_mask = resize_image(object_mask, 0.5, 0.5)
  output_image = place_object(dst_img, dst_points, resized_object_image, resized_object_mask)
  return output_image
