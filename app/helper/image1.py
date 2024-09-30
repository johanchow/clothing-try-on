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

    # 二值化处理
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    # 查找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 如果没有找到任何轮廓，则返回None
    if len(contours) == 0:
        return None, None

    # 找到面积最大的轮廓
    largest_contour = max(contours, key=cv2.contourArea)

    # 计算该轮廓的最小边界矩形
    x, y, w, h = cv2.boundingRect(largest_contour)

    # 创建 output_image 和 mask，大小为boundingRect的 w 和 h
    output_image = np.zeros((h, w, 4), dtype=np.uint8)  # RGBA格式
    mask = np.zeros((h, w), dtype=np.uint8)

    # 将轮廓偏移到新的坐标系中 (基于 boundingRect 的位置)
    contour_offset = largest_contour - [x, y]

    # 创建一个局部的掩码 (mask) 并填充轮廓
    cv2.drawContours(mask, [contour_offset], -1, 255, thickness=cv2.FILLED)

    # 将原图像中的轮廓区域复制到output_image
    src_rgba_image_ = cv2.merge((src_image, np.full((src_image.shape[0], src_image.shape[1]), 255, dtype=np.uint8)))
    output_image[mask == 255] = src_rgba_image_[y:y+h, x:x+w][mask == 255]

    # 设置轮廓区域为不透明
    output_image[:, :, 3][mask == 255] = 255  # 设置 alpha 通道

    cv2.imwrite('object.png', output_image)

    return output_image, mask

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

def copy_polygon_area(src_img, src_points, dst_img, dst_points):
  src_mask = get_polygon_mask(src_img.shape, src_points)
  object_rgba_image, object_rgba_mask = extract_object_using_canny(src_img, src_mask)
  output_image = place_object(dst_img, dst_points, object_rgba_image, object_rgba_mask)
  return output_image








def interpolate_points(points, target_num):
    """插值或减少顶点，使多边形的顶点数量达到目标数量"""
    points = np.array(points, dtype=np.float32)
    interpolated_points = []
    num_points = len(points)

    if num_points == target_num:
        return points

    if num_points < target_num:
        # 插值: 当顶点数量不足时，插入新的点
        for i in range(num_points):
            interpolated_points.append(points[i])
            next_idx = (i + 1) % num_points
            if len(interpolated_points) < target_num:
                mid_point = (points[i] + points[next_idx]) / 2.0
                interpolated_points.append(mid_point)
    else:
        # 简化: 当顶点数量过多时，移除点
        step = num_points / target_num
        idx = 0
        for i in range(target_num):
            interpolated_points.append(points[int(idx)])
            idx += step

    return np.array(interpolated_points, dtype=np.float32)

def delaunay_triangulation(points):
    """对多边形顶点进行 Delaunay 三角剖分"""
    delaunay = Delaunay(points)
    return delaunay.simplices

def warp_triangle(src_img, dst_img, t_src, t_dst):
    """将源图像中的三角形仿射变换到目标图像中的对应区域"""
    # 计算仿射变换矩阵
    t_src = np.array(t_src, dtype=np.float32)
    t_dst = np.array(t_dst, dtype=np.float32)

    warp_matrix = cv2.getAffineTransform(t_src, t_dst)

    # 计算目标区域的边界框
    x, y, w, h = cv2.boundingRect(t_dst)

    # 提取目标图像中的对应区域
    dst_cropped = dst_img[y:y+h, x:x+w]

    # 计算仿射变换后的目标区域
    warp_dst = cv2.warpAffine(src_img, warp_matrix, (w, h), dst_cropped, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

    # 创建三角形掩码
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = t_dst - np.array([x, y])
    cv2.fillConvexPoly(mask, np.int32(pts), 255)

    # 使用掩码将仿射变换后的区域复制到目标图像中
    warp_dst = warp_dst * (mask[..., np.newaxis] / 255.0)
    dst_img[y:y+h, x:x+w] = dst_img[y:y+h, x:x+w] * (1 - mask[..., np.newaxis] / 255.0) + warp_dst

def copy_polygon_area2(src_img, src_points, dst_img, dst_points):
    """从源图中拷贝一个区域映射到目标图中"""
    # 确保 src_points 和 dst_points 的数量相同
    if len(src_points) != len(dst_points):
        max_len = max(len(src_points), len(dst_points))
        src_points = interpolate_points(src_points, max_len)
        dst_points = interpolate_points(dst_points, max_len)

    # Delaunay 三角剖分
    tri_indices = delaunay_triangulation(dst_points)

    # 对每个三角形进行仿射变换
    for tri in tri_indices:
        t_src = [src_points[tri[0]], src_points[tri[1]], src_points[tri[2]]]
        t_dst = [dst_points[tri[0]], dst_points[tri[1]], dst_points[tri[2]]]
        warp_triangle(src_img, dst_img, t_src, t_dst)

    return dst_img
