"""Local adapter for the optional CIX YOLOv11n-pose NPU model.

The OpenCV and CIX runtime imports are intentionally delayed so a Mac preview,
or a board without this optional model, can still run the rest of WearMind.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

SKELETON = ((5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12),
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16))
DEFAULT_MODEL = Path('/home/cix/wearmind-npu/yolov11n-pose.cix')


def model_path() -> Path:
    return Path(os.environ.get('WEARMIND_NPU_POSE_MODEL', str(DEFAULT_MODEL))).expanduser()


def status() -> dict:
    path = model_path()
    return {'configured': path.is_file(),
            'model': path.name if path.is_file() else '未检测到 YOLOv11n-Pose .cix',
            'provider': 'CIX NPU / NOE Engine' if path.is_file() else '未就绪',
            'cloud_disabled': True}


def _letterbox(image, cv2, np, size=640):
    height, width = image.shape[:2]
    scale = min(size / width, size / height)
    resized = cv2.resize(image, (round(width * scale), round(height * scale)))
    left, top = (size - resized.shape[1]) // 2, (size - resized.shape[0]) // 2
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    canvas[top:top + resized.shape[0], left:left + resized.shape[1]] = resized
    tensor = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    return np.ascontiguousarray(tensor), scale, left, top


def _iou(one, many, np):
    left, top = np.maximum(one[0], many[:, 0]), np.maximum(one[1], many[:, 1])
    right, bottom = np.minimum(one[2], many[:, 2]), np.minimum(one[3], many[:, 3])
    overlap = np.maximum(0, right-left) * np.maximum(0, bottom-top)
    return overlap / np.maximum((one[2]-one[0])*(one[3]-one[1]) + (many[:, 2]-many[:, 0])*(many[:, 3]-many[:, 1])-overlap, 1e-6)


def _nms(boxes, scores, np):
    order, kept = scores.argsort()[::-1], []
    while len(order):
        current = int(order[0]); kept.append(current)
        if len(order) == 1: break
        order = order[1:][_iou(boxes[current], boxes[order[1:]], np) <= .55]
    return kept


def _tips(people):
    if not people:
        return ['没有稳定检测到完整人物。请换成光线更均匀、人物更清楚的全身或半身照片。', '这不是穿搭好坏判断；它只帮助检查人物是否在画面里清楚可见。']
    if people > 1:
        return ['画面里检测到多个人，分享前建议裁剪或确认主角，避免构图分散。', '让主角离画面边缘留一点空间，衣服轮廓会更完整。']
    return ['已检测到一位主体人物和姿势关键点，人物轮廓可用于检查全身构图。', '拍穿搭记录时，尽量保留头顶、衣摆和鞋子附近的少量空间，方便看清整体比例。', '这项分析只做人物与姿势定位，不推断身材、情绪或健康状态。']


def _composition(box, points, width, height):
    """Use visible pose landmarks to assess photo coverage, not clothing or body shape."""
    if box is None or points is None:
        return {'coverage':'未检测到主体','head_clear':False,'feet_clear':False,
                'tips':['请换一张人物更清晰的照片；无法判断穿搭是否完整入画。']}
    def visible(index):
        x, y, confidence = points[index]
        return bool(confidence >= .35 and 0 <= x < width and 0 <= y < height)
    head = any(visible(i) for i in range(5))
    feet = visible(15) and visible(16)
    hips = visible(11) and visible(12)
    coverage = '全身关键点可见' if head and hips and feet else ('上半身可见' if head and hips else '人物关键点不完整')
    tips = []
    if not head: tips.append('头部关键点不清晰或未入画；如果要展示全套穿搭，可以调整拍摄距离与角度。')
    if not feet: tips.append('脚踝关键点不清晰，可能被遮挡或未入画；若想展示鞋履，请确认脚部完整可见。')
    if box[0] <= width*.02 or box[2] >= width*.98:
        tips.append('人物靠近画面侧边；适当留白更容易看清衣物轮廓。')
    if not tips: tips.append('主要人物的头部、髋部和脚踝关键点均可见，可作为整套穿搭记录。')
    return {'coverage':coverage,'head_clear':head,'feet_clear':feet,'tips':tips}


def analyze(image_path: Path, output_path: Path) -> dict:
    if not status()['configured']:
        raise ValueError('本机 NPU 姿势模型尚未就绪；不会改用云端分析')
    try:
        import cv2
        import numpy as np
        from NOE_Engine import EngineInfer
    except ImportError as error:
        raise ValueError('开发板缺少本机姿势分析组件：' + str(error)) from error
    image = cv2.imread(str(image_path))
    if image is None: raise ValueError('无法读取这张图片')
    tensor, scale, left, top = _letterbox(image, cv2, np)
    engine = None
    try:
        engine = EngineInfer(str(model_path()))
        started = time.perf_counter()
        raw = np.asarray(engine.forward([tensor])[0]).reshape(56, 8400).T
        elapsed = round((time.perf_counter() - started) * 1000)
    finally:
        if engine is not None: engine.clean()
    raw = raw[raw[:, 4] >= .45]
    people = 0
    main_box = main_points = None
    if len(raw):
        boxes = raw[:, :4].copy(); boxes[:, 0] -= boxes[:, 2]/2; boxes[:, 1] -= boxes[:, 3]/2; boxes[:, 2] += boxes[:, 0]; boxes[:, 3] += boxes[:, 1]
        for index in _nms(boxes, raw[:, 4], np)[:3]:
            people += 1
            x1, y1, x2, y2 = boxes[index]
            x1, y1, x2, y2 = (x1-left)/scale, (y1-top)/scale, (x2-left)/scale, (y2-top)/scale
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (32, 210, 122), 2)
            keypoints = raw[index, 5:].reshape(17, 3).copy(); keypoints[:, 0] = (keypoints[:, 0]-left)/scale; keypoints[:, 1] = (keypoints[:, 1]-top)/scale
            if people == 1:
                main_box, main_points = (x1,y1,x2,y2), keypoints
            for x, y, confidence in keypoints:
                if confidence >= .35: cv2.circle(image, (int(x), int(y)), 3, (45, 184, 255), -1)
            for a, b in SKELETON:
                if keypoints[a, 2] >= .35 and keypoints[b, 2] >= .35: cv2.line(image, tuple(keypoints[a, :2].astype(int)), tuple(keypoints[b, :2].astype(int)), (255, 168, 54), 2)
    else:
        cv2.putText(image, 'No person detected', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, .8, (40, 40, 220), 2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), image): raise ValueError('无法保存本机分析结果')
    composition = _composition(main_box, main_points, image.shape[1], image.shape[0])
    return {'people': people, 'elapsed_ms': elapsed, 'tips': _tips(people) + composition['tips'],
            'composition':{key:value for key,value in composition.items() if key != 'tips'},
            'provider': 'CIX NPU / YOLOv11n-Pose'}
