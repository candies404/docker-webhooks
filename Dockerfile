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

# 设置默认端口为 5000
ENV PORT=5000

# 暴露应用运行的端口
EXPOSE $PORT


# 使用 Gunicorn 启动 Flask 应用
# --w 4: 使用 4 个工作进程，适合 2 核心的服务器
# --b 0.0.0.0:5000: 绑定到所有 IP 地址的 5000 端口
# --log-level info：设置日志级别为 info
# --access-logfile - 和 --error-logfile -：将访问日志和错误日志都输出到标准输出
# -app:app: 第一个 'app' 是 Python 文件名（不带 .py），第二个 'app' 是 Flask 应用实例名称
CMD gunicorn --workers 4 \
             --bind 0.0.0.0:$PORT \
             --log-level info \
             --access-logfile - \
             --error-logfile - \
             app:app
