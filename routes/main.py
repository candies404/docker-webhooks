from datetime import datetime
from flask import render_template, current_app
from utils.response import json_response
import logging

logger = logging.getLogger(__name__)


def home():
    """首页路由"""
    logger.info("访问了首页")
    return render_template('index.html')


def test():
    """测试路由"""
    logger.info("收到测试请求")
    valid_projects = [
        project_name
        for project_name, config in current_app.config['PROJECT_CONFIG'].items()
        if config.get('api_key')
    ]
    data = {
        'message': '这是一个测试响应',
        'timestamp': datetime.now().isoformat(),
        'app_config': {
            'BASE_URL': current_app.config['BASE_URL'],
            'PROJECT_COUNT': len(valid_projects),
            'PROJECTS': valid_projects
        }
    }
    return json_response(data)
