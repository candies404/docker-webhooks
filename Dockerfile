# 使用官方的 Python 3.9 作为基础镜像
FROM python:3.9-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件并安装依赖
COPY requirements.txt .

# 安装 Flask 和其他依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码到容器中
COPY . .

# 暴露应用运行的端口
EXPOSE 5000

# 启动 Flask 应用
CMD ["python", "app.py"]
