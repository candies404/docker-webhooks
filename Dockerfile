# 使用官方的 Python 3.9 作为基础镜像
FROM python:3.9-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件并安装依赖
COPY requirements.txt .

# 安装 Flask 和其他依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码到容器中
COPY . .

# 设置默认端口为 5000
ENV PORT=5000

# 暴露应用运行的端口
EXPOSE $PORT

# 使用 Gunicorn 启动 Flask 应用 ,-c 指定一个配置文件 ,app:app:指定 Flask 应用实例，格式为 模块名:实例名
CMD ["gunicorn", "-c", "config/gunicorn_config.py", "app:app"]
