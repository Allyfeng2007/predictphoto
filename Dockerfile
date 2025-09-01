# 更小的基础镜像
FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 仅装 OpenCV 运行时需要的基础库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先通过 CPU 源安装 PyTorch & torchvision（避免 CUDA 巨包）
# 这一步一定要和下面的 requirements 分开
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.3.1 torchvision==0.18.1

# 其它依赖仍可走官方或国内镜像（需要的话可改为清华镜像）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码和模型
COPY app.py .
COPY yolov8n.pt .

EXPOSE 80

# 使用 gunicorn 监听 80（符合云托管要求）
# gthread 可以更好地处理短请求；按需调整 workers/threads
CMD ["gunicorn", "-b", "0.0.0.0:80", "-w", "2", "-k", "gthread", "--threads", "4", "--timeout", "120", "app:app"]
