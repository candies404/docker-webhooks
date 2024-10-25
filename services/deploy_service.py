import logging
import threading
from datetime import datetime

from notify import send

logger = logging.getLogger(__name__)


def send_deploy_notification(project, service_name, success, deploy_id):
    """
    发送部署通知
    """
    status = "成功" if success else "失败"
    title = f"Render 部署通知"
    content = (
        f"### 项目: {project}\n\n"
        f"**服务**: {service_name}\n\n"
        f"**部署状态**: {status}\n\n"
        f"**部署ID**: {deploy_id}\n\n"
        f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    send(title, content)


def check_deploy_and_notify(render_service, project, service_name, service_id, deploy_id, api_key):
    """
    检查部署状态并发送通知的后台任务
    """
    thread_name = threading.current_thread().name
    logger.info(f"[{thread_name}] 开始检查部署状态: 项目 {project}, 服务 {service_name}")
    deploy_success = render_service.check_deploy_status(service_id, deploy_id, api_key)

    if deploy_success:
        logger.info(f"[{thread_name}] 部署成功: 项目 {project}, 服务 {service_name}")
    else:
        logger.error(f"[{thread_name}] 部署失败: 项目 {project}, 服务 {service_name}")

    send_deploy_notification(project, service_name, deploy_success, deploy_id)
    logger.info(f"[{thread_name}] 部署状态检查和通知发送完成: 项目 {project}, 服务 {service_name}")


def handle_webhook(render_service, project, api_key):
    """
    处理 webhook 请求的业务逻辑
    """
    logger.info(f"处理 webhook: 项目 {project}")
    services = render_service.get_services(api_key)
    if not services:
        logger.error(f"无法获取服务列表或列表为空: 项目 {project}")
        return None, '无法获取服务列表或列表为空', 500

    # 部署第一个服务
    service = services[0]
    service_id = service.get('service', {}).get('id')
    service_name = service.get('service', {}).get('name')

    if not service_id:
        logger.error(f"无法获取服务ID: 项目 {project}, 服务 {service_name}")
        return None, '无法获取服务ID', 500

    logger.info(f"准备部署服务: 项目 {project}, 服务 {service_name}")

    deploy_result = render_service.trigger_deploy(service_id, api_key)
    if deploy_result:
        deploy_id = deploy_result.get('id')
        logger.info(f"新的部署已触发: 项目 {project}, 服务名称 {service_name}")

        # 在后台线程中检查部署状态并发送通知
        thread_name = f"Thread-{project}"
        thread = threading.Thread(target=check_deploy_and_notify,
                                  name=thread_name,
                                  args=(render_service, project, service_name, service_id, deploy_id, api_key))
        thread.start()
        logger.info(f"后台检查部署状态的线程已启动: 项目 {project}, 服务名称 {service_name}")

        return {
            'message': '部署已触发',
            'project': project,
            'service_name': service_name,
            'service_id': service_id,
            'status': 'pending'
        }, None, 200
    else:
        logger.error(f"触发部署失败: 项目 {project}, 服务 {service_name}")
        send_deploy_notification(project, service_name, False)
        return None, '触发部署失败', 500
