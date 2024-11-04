import multiprocessing
import os
from config.constants import DEFAULT_PORT  # 从 constants.py 导入默认端口配置

# 获取环境变量或使用默认值
port = os.getenv("PORT", DEFAULT_PORT)
max_workers = int(os.getenv("MAX_WORKERS", "8"))  # 默认最大 8 个 workers

# 计算 workers 数量
cpu_count = multiprocessing.cpu_count()
worker_count = min(cpu_count * 2 + 1, max_workers)

# Gunicorn 配置
bind = f"0.0.0.0:{port}"  # 绑定地址和端口，0.0.0.0表示监听所有网络接口
workers = worker_count  # worker进程数
loglevel = "info"  # 日志级别
accesslog = "-"  # 访问日志输出到标准输出(-)
errorlog = "-"  # 错误日志输出到标准输出(-)
capture_output = True  # 捕获应用的标准输出和错误输出

# 访问日志格式
# %(t)s - 时间戳
# %(h)s - 远程地址
# %(l)s - '-'
# %(u)s - 用户名
# %(r)s - 请求行
# %(s)s - 状态码
# %(b)s - 响应长度
# %(f)s - referer
# %(a)s - user-agent
access_log_format = '[%(t)s] %(h)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 使用 Gunicorn 的标准日志类
logger_class = "gunicorn.glogging.Logger"
