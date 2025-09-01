from flask import Flask, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO
import base64
import threading
from queue import Queue

# 初始化 Flask 应用
app = Flask(__name__)

# 加载 YOLOv8 模型（确保 yolov8n.pt 文件存在）
model = YOLO('./yolov8n.pt')

# 语音播报队列（保留结构但实际由小程序端处理）
speech_q = Queue()
stop_event = threading.Event()


def tts_worker():
    """保留语音线程结构（实际不启用）"""
    while not stop_event.is_set():
        text = speech_q.get()
        if text is None:
            break
        speech_q.task_done()


tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()


def generate_alert_text(detections):
    """根据检测结果生成提示文本"""
    alert_texts = []
    for cls_name, (x1, y1, x2, y2) in detections:
        if cls_name == 'traffic light':
            # 交通灯颜色识别逻辑
            roi = np.random.randint(0, 255, (y2 - y1, x2 - x1, 3), dtype=np.uint8)  # 模拟ROI
            if roi.size == 0:
                continue
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            mask_red = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255)) | cv2.inRange(hsv, (160, 100, 100),
                                                                                     (180, 255, 255))
            mask_green = cv2.inRange(hsv, (50, 100, 100), (90, 255, 255))
            if cv2.countNonZero(mask_red) > 50:
                color = '红灯'
            elif cv2.countNonZero(mask_green) > 50:
                color = '绿灯'
            else:
                color = '黄灯'
            alert_texts.append(f"前方{color}")
        else:
            # 障碍物位置判断
            center_x = (x1 + x2) / 2
            pos = "左侧" if center_x < 0.3 else ("右侧" if center_x > 0.7 else "前方")
            cname_zh = {
                'person': '行人', 'bicycle': '自行车', 'car': '汽车',
                'motorbike': '摩托车', 'bus': '公交车', 'truck': '卡车'
            }.get(cls_name, "障碍物")
            alert_texts.append(f"{pos}有{cname_zh}")

    return "，".join(list(set(alert_texts))) + "。" if alert_texts else "未检测到目标"


@app.route('/predict', methods=['POST'])
def predict():
    """接收小程序上传的图片并返回识别结果"""
    try:
        # 获取Base64图片数据
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'error': '未提供图片数据'}), 400

        # Base64解码 -> OpenCV格式
        header, data = image_data.split(',', 1)
        img_bytes = base64.b64decode(data)
        img_np = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # YOLOv8 目标检测
        results = model(img, verbose=False)[0]
        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = results.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detections.append((cls_name, (x1, y1, x2, y2)))

        # 生成语音提示文本
        alert_text = generate_alert_text(detections)
        return jsonify({
            'result': alert_text,
            'detections': detections  # 可选：返回检测框坐标供小程序绘制
        })

    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'service': 'yolo-detection'})


if __name__ == '__main__':
    # 启动服务（生产环境用Gunicorn）
    app.run(host='0.0.0.0', port=80, debug=False)