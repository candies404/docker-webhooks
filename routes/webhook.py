from datetime import datetime, timedelta
from flask import request, current_app
import logging
from typing import TYPE_CHECKING
from utils.response import json_response
from utils.lock_utils import (
    file_lock,
    file_unlock,
    get_deploy_lock,
    get_last_deploy_time,
    update_deploy_time
)
from config.constants import DEPLOY_INTERVAL

if TYPE_CHECKING:
    from services.project_service import ProjectService
    from services.render_service import RenderService
    from app import FlaskApp  # 导入自定义的 Flask 应用类

    current_app: FlaskApp  # 类型提示

logger = logging.getLogger(__name__)


def get_project_service() -> 'ProjectService':
    """获取项目服务实例"""
    return current_app.project_service  # IDE 现在能识别这个属性


def get_render_service() -> 'RenderService':
    """获取渲染服务实例"""
    return current_app.render_service  # IDE 现在能识别这个属性


def webhook():
    """Webhook 路由处理"""
    logger.info("收到 webhook 请求")

    # 验证请求格式
    if not request.is_json:
        logger.error("无效的 Content-Type，需要 application/json")
        return json_response({'error': '无效的 Content-Type，需要 application/json'}, 400)

    # 验证令牌
    token = request.args.get('token')
    if not token:
        return json_response({'error': '缺少认证令牌'}, 401)
    if token != current_app.config['SECRET_TOKEN']:
        return json_response({'error': '无效的令牌'}, 403)

    # 验证项目
    project = request.args.get('project')
    project_service = get_project_service()
    if not project_service.is_valid_project(project):
        logger.error(f"无效的项目名称: {project}")
        return json_response({'error': '无效的项目名称'}, 400)

    # 验证负载
    payload = request.json
    if not payload or 'push_data' not in payload:
        logger.error("无效的负载")
        return json_response({'error': '无效的负载'}, 400)

    # 获取文件锁
    lock_file = get_deploy_lock(project)
    lock_acquired = False
    try:
        # 尝试获取文件锁
        if not file_lock(lock_file):
            logger.warning(f"项目 {project} 正在部署中，获取锁失败")
            lock_file.close()
            return json_response({
                'error': '部署正在进行中',
                'details': f'检测到项目 {project} 正在进行部署，请等待当前部署完成后再试',
                'status': 'deploying'
            }, 429)

        lock_acquired = True
        logger.info(f"项目 {project} 成功获取锁, 准备部署")

        # 检查部署时间间隔
        last_deploy_time = get_last_deploy_time(project)
        if last_deploy_time:
            time_since_last_deploy = datetime.now() - last_deploy_time
            if time_since_last_deploy < timedelta(seconds=DEPLOY_INTERVAL):
                remaining_seconds = DEPLOY_INTERVAL - time_since_last_deploy.seconds
                logger.warning(
                    f"项目 {project} 在 {DEPLOY_INTERVAL} 秒内已经触发过部署，"
                    f"还需等待 {remaining_seconds} 秒"
                )
                return json_response({
                    'error': '部署请求过于频繁',
                    'details': f'系统限制项目 {project} 每 {DEPLOY_INTERVAL} 秒只能部署一次',
                    'retry_after': f"{remaining_seconds}秒",
                    'status': 'rate_limited'
                }, 429)

        # 更新部署时间
        update_deploy_time(project)

        # 执行部署
        project_config = project_service.get_project_config(project)
        api_key = project_config['api_key']
        if not api_key:
            logger.error(f"项目 {project} 缺少 API 密钥")
            return json_response({
                'error': '配置错误',
                'details': '项目缺少 API 密钥配置',
                'status': 'error'
            }, 500)

        render_service = get_render_service()
        response, error, status_code = render_service.handle_webhook(project, api_key)
        if error:
            logger.error(f"处理 webhook 时出错: {error}")
            return json_response({'error': error, 'project': project}, status_code)

        logger.info(f"成功处理 webhook: {project}")
        return json_response(response, status_code)

    except Exception as e:
        logger.exception(f'处理 webhook 时出错: 项目 {project}')
        return json_response({
            'error': '处理 webhook 时出错',
            'details': str(e),
            'status': 'error'
        }, 500)
    finally:
        if lock_acquired:
            file_unlock(lock_file)
            logger.info(f"释放锁，时间：{datetime.now().isoformat()}")
        lock_file.close()
