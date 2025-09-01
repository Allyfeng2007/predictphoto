FROM python:3.9-slim

WORKDIR /app

# 复制文件
COPY requirements.txt .
COPY app.py .
COPY linreg.model .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露端口（微信云托管默认使用80端口）
EXPOSE 80

# 启动应用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
