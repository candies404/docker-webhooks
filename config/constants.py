# 日志相关配置
import os

LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_PORT = 5000

# API相关配置
BASE_API_URL = "https://api.render.com/v1"

# 部署相关配置
DEPLOY_INTERVAL = int(os.getenv('DEPLOY_INTERVAL', '60'))  # 部署间隔时间(秒)
MAX_DEPLOY_RETRIES = int(os.getenv('MAX_DEPLOY_RETRIES', '5'))  # 最大部署重试次数
DEPLOY_CHECK_INTERVAL = int(os.getenv('DEPLOY_CHECK_INTERVAL', '60'))  # 部署状态检查间隔(秒)
# 域名显示配置
PREFER_CUSTOM_DOMAIN = os.getenv('PREFER_CUSTOM_DOMAIN', 'true').lower() == 'true'
