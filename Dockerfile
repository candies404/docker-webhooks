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

# 使用 Gunicorn 启动 Flask 应用
# --workers 4                          : 启动4个工作进程，建议设置为 CPU 核心数的 2-4 倍
# --bind 0.0.0.0:$PORT                : 绑定到所有网络接口的指定端口
# --log-level info                    : 设置日志级别为 info
# --access-logfile -                  : 将访问日志输出到标准输出(-)
# --error-logfile -                   : 将错误日志输出到标准输出(-)
# --capture-output                    : 捕获应用程序的标准输出和错误输出
# --access-logformat                  : 自定义访问日志格式
#   %(t)s  - 时间戳
#   %(h)s  - 远程地址
#   %(l)s  - '-'
#   %(u)s  - 用户名
#   %(r)s  - 请求行
#   %(s)s  - 状态码
#   %(b)s  - 响应长度
#   %(f)s  - 请求头中的 referer
#   %(a)s  - 请求头中的 user-agent
# --logger-class                      : 使用 Gunicorn 的标准日志类
# app:app                             : 指定 Flask 应用实例，格式为 模块名:实例名
CMD ["gunicorn", \
     "--workers", "4", \
     "--bind", "0.0.0.0:5000", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "--access-logformat", "[%(t)s] %(h)s %(l)s %(u)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"", \
     "--logger-class", "gunicorn.glogging.Logger", \
     "app:app"]
