import logging
import os
import sys
from typing import TYPE_CHECKING

from flask import Flask

from config import (
    DEFAULT_PORT,
    load_config
)
from routes import home, test, webhook
from services import RenderService, ProjectService

if TYPE_CHECKING:
    from services.project_service import ProjectService
    from services.render_service import RenderService

# 定义全局 logger
logger: logging.Logger = None


class FlaskApp(Flask):
    project_service: 'ProjectService'
    render_service: 'RenderService'


def configure_logging() -> logging.Logger:
    """配置日志系统并返回应用日志器"""
    # 配置根日志器
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)

    # 使用 Gunicorn 默认的日志格式
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s [%(process)d] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z'
    )
    console_handler.setFormatter(formatter)

    # 配置应用日志器
    app_logger = logging.getLogger('docker-hooks')
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(console_handler)
    app_logger.propagate = False

    # 配置其他日志器
    loggers = [
        logging.getLogger('werkzeug'),
        logging.getLogger('gunicorn.error'),
        logging.getLogger('gunicorn.access')
    ]

    for logger_instance in loggers:
        logger_instance.handlers = []
        logger_instance.addHandler(console_handler)
        logger_instance.setLevel(logging.INFO)
        logger_instance.propagate = False

    return app_logger


def create_app() -> FlaskApp:
    """创建并配置 Flask 应用"""
    global logger

    # 创建应用实例
    app = FlaskApp(__name__)

    # 配置日志
    logger = configure_logging()

    # 配置应用
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

    try:
        config = load_config()
        app.config.update(config)
    except ValueError as e:
        logger.error(f"配置加载失败: {str(e)}")
        sys.exit(1)

    # 初始化服务
    app.render_service = RenderService(app.config['BASE_URL'])
    app.project_service = ProjectService(app.config['PROJECT_CONFIG'])

    # 注册路由
    app.add_url_rule('/', 'home', home)
    app.add_url_rule('/test', 'test', test)
    app.add_url_rule('/webhook', 'webhook', webhook, methods=['POST'])

    return app


# 创建应用实例
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    logger.info(f"应用正在直接启动，监听端口 {port}")
    app.run(host='0.0.0.0', port=port)
