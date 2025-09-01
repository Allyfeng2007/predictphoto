FROM python:3.9-slim

WORKDIR /app

# 先复制依赖文件，利用Docker缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 再复制代码
COPY app.py .
COPY yolov8n.pt .

EXPOSE 80

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
