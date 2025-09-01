# ===== 第一阶段：构建依赖 =====
FROM python:3.9-slim as builder

WORKDIR /app

# 复制依赖列表（利用Docker缓存层）
COPY requirements.txt .

# 安装依赖（使用国内镜像源）
RUN pip install --user --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && find /root/.local -type d -name '__pycache__' -exec rm -rf {} +

# ===== 第二阶段：生产镜像 =====
FROM python:3.9-slim

WORKDIR /app

# 从builder阶段复制已安装的Python依赖
COPY --from=builder /root/.local /root/.local

# 复制必要文件（模型+代码）
COPY app.py .
COPY yolov8n.pt .

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=2

# 暴露端口
EXPOSE 80

# 启动命令（使用gunicorn）
CMD ["gunicorn", "-w", "${GUNICORN_WORKERS}", "-b", "0.0.0.0:80", "app:app"]
