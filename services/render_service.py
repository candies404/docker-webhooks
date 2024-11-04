import logging
import threading
import time
from datetime import datetime, timezone
from multiprocessing import Process, log_to_stderr  # 添加 log_to_stderr 导入
from typing import Tuple, Optional, Dict, Any

import requests

from config.constants import (
    MAX_DEPLOY_RETRIES,
    DEPLOY_CHECK_INTERVAL,
    PREFER_CUSTOM_DOMAIN
)
from utils.notify import send

logger = logging.getLogger(__name__)


# 服务状态常量
class ServiceStatus:
    SUSPENDED = 'suspended'
    NOT_SUSPENDED = 'not_suspended'


# 部署状态常量
class DeployStatus:
    LIVE = 'live'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    DEACTIVATED = 'deactivated'


class RenderService:
    """Render 服务的操作封装类"""

    def __init__(self, base_url):
        """
        初始化 RenderService

        Args:
            base_url: Render API 的基础 URL
        """
        self.base_url = base_url
        # 直接使用 docker-hooks logger 而不是创建新的
        self.logger = logging.getLogger('docker-hooks')

    def get_services(self, api_key: str, suspended: Optional[str] = None):
        """
        获取 Render 服务列表

        Args:
            api_key: Render API 密钥
            suspended: 可选，筛选服务状态
                - "suspended": 只返回已暂停的服务
                - "not_suspended": 只返回未暂停的服务
                - None: 返回所有服务

        Returns:
            list: 成功时返回服务列表
            None: 失败时返回 None
        """
        self.logger.info("正在获取服务列表")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

        # 构建查询参数
        params = {}
        if suspended is not None:
            params['suspended'] = suspended

        response = requests.get(
            f"{self.base_url}/services",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            services = response.json()
            self.logger.info(f"获取到 {len(services)} 个服务")
            self._log_service_names(services)
            return services
        else:
            logger.error(f"获取服务列表失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None

    def get_custom_domains(self, service_id: str, api_key: str) -> list[str]:
        """
        获取服务的自定义域名列表

        Args:
            service_id: 服务ID
            api_key: API密钥

        Returns:
            list[str]: 已验证的自定义域名列表，每个域名都包含 https:// 前缀
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(
                f"{self.base_url}/services/{service_id}/custom-domains",
                headers=headers
            )

            if response.status_code == 200:
                domains_data = response.json()
                # 提取已验证的域名并添加 https:// 前缀
                domains = [
                    f"https://{item['customDomain']['name']}"
                    for item in domains_data
                    if isinstance(item, dict)
                       and 'customDomain' in item
                       and item['customDomain'].get('verificationStatus') == 'verified'
                       and item['customDomain'].get('name')
                ]
                self.logger.info(f"获取到 {len(domains)} 个已验证的自定义域名")
                return domains
            else:
                logger.error(f"获取自定义域名失败: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return []
        except Exception as e:
            logger.error(f"获取自定义域名时出错: {str(e)}")
            return []

    def get_service_urls(self, service_id: str, api_key: str) -> Optional[Dict[str, Any]]:
        """
        获取服务的 URL 信息，包括默认域名和自定义域名

        Args:
            service_id: 服务ID
            api_key: API密钥

        Returns:
            Optional[Dict[str, Any]]: 包含默认域名和自定义域名的字典；失败时返回 None
            格式: {
                'default_url': 'https://xxx.onrender.com',
                'custom_domains': ['https://domain1.com', 'https://domain2.com']
            }
        """
        # 获取服务列表
        services = self.get_services(api_key)
        if not services:
            return None

        # 查找指定的服务
        service_info = None
        for service in services:
            service_data = service.get('service')
            if isinstance(service_data, dict) and service_data.get('id') == service_id:
                service_info = service_data
                break

        if not service_info:
            logger.error(f"未找到服务: {service_id}")
            return None

        # 获取并返回 URL 信息
        return {
            'default_url': service_info.get('serviceDetails', {}).get('url'),
            'custom_domains': self.get_custom_domains(service_id, api_key)
        }

    def _log_service_names(self, services):
        """
        记录服务名称和 ID（私有方法）

        Args:
            services: 服务列表
        """
        for service in services:
            name = service.get('service', {}).get('name')
            service_id = service.get('service', {}).get('id')
            self.logger.info(f"服务名称: {name}, ID: {service_id}")

    def trigger_deploy(self, service_id, api_key):
        """
        触发 Render 服务的部署

        Args:
            service_id: 要部署的服务 ID
            api_key: Render API 密钥

        Returns:
            dict: 成功时返回部署信息
            None: 失败时返回 None
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        response = requests.post(f"{self.base_url}/services/{service_id}/deploys", headers=headers)
        if response.status_code == 201:
            return response.json()
        else:
            logger.error(f"触发部署失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None

    def check_deploy_status(
            self,
            service_id: str,
            deploy_id: str,
            api_key: str,
            max_retries: int = MAX_DEPLOY_RETRIES,
            interval: int = DEPLOY_CHECK_INTERVAL
    ) -> Tuple[bool, str, str]:
        """
        检查部署状态，直到部署成功或失败，或达到最大重试次数

        Args:
            service_id: Render 服务的唯一标识符
            deploy_id: 部署操作的唯一标识符
            api_key: Render API 密钥
            max_retries: 最大重试次数，默认从配置获取
            interval: 重试间隔（秒），默认从配置获取

        Returns:
            Tuple[bool, str, str]:
                - bool: 部署是否成功
                - str: 部署完成时间（UTC格式），失败时为空字符串
                - str: 部署状态
        """
        url = f"{self.base_url}/services/{service_id}/deploys/{deploy_id}"
        headers = {"Authorization": f"Bearer {api_key}"}

        retries = 0
        last_status = None

        self.logger.info(f"开始检查部署状态: deploy_id={deploy_id}")
        self.logger.info(f"最大重试次数: {max_retries}, 检查间隔: {interval}秒")

        while retries < max_retries:
            try:
                self.logger.info(f"第 {retries + 1}/{max_retries} 次检查部署状态")
                response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    logger.error(f"获取部署状态失败: HTTP {response.status_code}")
                    logger.error(f"响应内容: {response.text}")
                    return False, "", "failed"

                deploy_info = response.json()
                current_status = deploy_info.get("status", "unknown")

                # 记录详细的部署信息
                self.logger.info(f"部署信息: {deploy_info}")

                # 记录当前状态，即使没有变化
                self.logger.info(f"当前部署状态: {current_status}")

                # 记录状态变化
                if current_status != last_status:
                    self.logger.info(f"部署状态从 {last_status} 变更为 {current_status}")
                    last_status = current_status

                finish_time = deploy_info.get("finishedAt", "")

                if current_status == DeployStatus.LIVE:
                    self.logger.info(f"部署成功完成！总耗时: {retries * interval} 秒")
                    self.logger.info(f"完成时间: {finish_time}")
                    return True, finish_time, current_status

                elif current_status in [DeployStatus.FAILED, DeployStatus.CANCELLED, DeployStatus.DEACTIVATED]:
                    logger.error(f"部署失败！状态: {current_status}")
                    logger.error(f"总耗时: {retries * interval} 秒")
                    logger.error(f"完成时间: {finish_time}")
                    # 记录更多失败细节
                    if 'errorMessage' in deploy_info:
                        logger.error(f"错误信息: {deploy_info['errorMessage']}")
                    return False, finish_time, current_status

                retries += 1
                if retries < max_retries:
                    self.logger.info(f"等待 {interval} 秒后进行下一次检查...")
                    time.sleep(interval)

            except Exception as e:
                logger.error(f"检查部署状态时发生错误: {str(e)}")
                return False, "", "failed"

        logger.error(f"检查部署状态超时，已达到最大重试次数 {max_retries}")
        logger.error(f"最后的部署状态: {last_status}")
        return False, "", last_status or "failed"

    def send_deploy_notification(
            self,  # 添加 self 参数
            project: str,
            service_name: str,
            deploy_id: Optional[str] = None,
            urls: Optional[Dict[str, Any]] = None,
            finish_time: Optional[str] = None,
            status: str = None
    ) -> None:
        """
        发送部署通知

        Args:
            project: 项目名称
            service_name: 服务名称
            deploy_id: 部署ID（可选）
            urls: URL信息，格式同 get_service_urls 的返回值
            finish_time: 部署完成时间，格式为 ISO 8601
            status: 部署状态（live、failed、cancelled）

        Note:
            - URL 显示格式由 PREFER_CUSTOM_DOMAIN 环境变量控制
              - true: 仅显示自定义域名（如果有）
              - false: 同时显示默认域名和自定义域名
            - 时间显示包括部署完成时间（UTC转本地）和通知发送时间（本地）
            - 多个自定义域名使用 | 符号分隔显示
        """
        # 构建基本通知内容
        title = "Render 部署通知"
        # 根据状态添加图标
        status_icon = "✅" if status == "live" else "❌"

        content = (
            f"--- \n\n"
            f"**项目名**: {project}\n\n"
            f"**服务名**: {service_name}\n\n"
            f"**部署状态**: {status_icon} {status}\n\n"
        )

        # 添加部署ID（如果有）
        if deploy_id:
            content += f"**部署ID**: {deploy_id}\n\n"

        # 添加域名信息（如果有）
        if urls:
            custom_domains = urls.get('custom_domains', [])
            default_url = urls.get('default_url')

            if PREFER_CUSTOM_DOMAIN and custom_domains:
                # 仅显示自定义域名，使用 | 分隔多个域名
                content += f"**自定义域名**: {' | '.join(custom_domains)}\n\n"
            else:
                # 显示所有域名
                if default_url:
                    content += f"**默认域名**: {default_url}\n\n"
                if custom_domains:
                    content += f"**自定义域名**: {' | '.join(custom_domains)}\n\n"

        # 添加时间信息
        if finish_time:
            try:
                # 将 UTC 时间转换为本地时间
                utc_time = datetime.strptime(finish_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                local_time = utc_time.replace(tzinfo=timezone.utc).astimezone()
                content += f"**部署完成时间**: {local_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            except ValueError:
                self.logger.warning(f"无法解析部署完成时间: {finish_time}")

        # 添加通知发送时间
        content += f"**通知时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # 发送通知
        send(title, content)

    def check_deploy_and_notify(
            self,
            project: str,
            service_name: str,
            service_id: str,
            deploy_id: str,
            api_key: str
    ) -> None:
        """
        检查部署状态并发送通知的后台任务

        此方法会执行以下操作：
        1. 定期检查部署状态直到完成
        2. 获取服务的域名信息（包括默认域名和自定义域名）
        3. 发送包含部署结果、域名信息和时间信息的通知

        Args:
            project: 项目名称，用于日志和通知显示
            service_name: 服务名称，用于日志和通知显示
            service_id: Render 服务的唯一标识符
            deploy_id: 部署操作的唯一标识符
            api_key: Render API 密钥

        Note:
            - 此方法通常在单独的线程中运行
            - 部署状态检查会根据 MAX_DEPLOY_RETRIES 和 DEPLOY_CHECK_INTERVAL 配置进行重试
            - 域名显示格式由 PREFER_CUSTOM_DOMAIN 环境变量控制
            - 如果部署失败，通知中将不包含域名信息
            - 时间信息包括部署完成时间和通知发送时间
            - 部署状态
        """
        thread_name = threading.current_thread().name
        self.logger.info(f"[{thread_name}] 开始检查部署状态: 项目名 {project}, 服务名称 {service_name}")

        deploy_success, finish_time, status = self.check_deploy_status(service_id, deploy_id, api_key)

        # 获取服务 URL 信息
        urls = None
        if deploy_success:
            urls = self.get_service_urls(service_id, api_key)
            self.logger.info(f"[{thread_name}] 部署成功: 项目名 {project}, 服务名称 {service_name}")
        else:
            self.logger.error(f"[{thread_name}] 部署{status}: 项目名 {project}, 服务名称 {service_name}")

        # 发送带有 URL 和完成时间的通知
        self.send_deploy_notification(
            project=project,
            service_name=service_name,
            deploy_id=deploy_id,
            urls=urls,
            finish_time=finish_time,
            status=status
        )

        self.logger.info(f"[{thread_name}] 部署状态检查和通知发送完成: 项目名 {project}, 服务名称 {service_name}")

    def handle_webhook(self, project, api_key):
        """
        处理 webhook 请求，触发部署并启动状态监控
        """
        self.logger.info(f"处理 webhook: 项目名 {project}")

        # 获取未暂停的服务
        services = self.get_services(api_key, suspended=ServiceStatus.NOT_SUSPENDED)
        if not services:
            # 如果没有找到未暂停的服务，检查是否有已暂停的服务
            suspended_services = self.get_services(api_key, suspended=ServiceStatus.SUSPENDED)
            if suspended_services:
                service = suspended_services[0]
                service_data = service.get('service', {})
                service_name = service_data.get('name', 'unknown')
                suspenders = service_data.get('suspenders', [])

                # 根据暂停者类型返回相应的错误信息
                suspend_reason = "服务已被 Render 管理员暂停" if "admin" in suspenders else "服务已被用户手动暂停"

                return None, {
                    "error": f"触发部署失败: 项目名 {project}, 服务名称 {service_name}",
                    "details": suspend_reason
                }, 500
            else:
                return None, {
                    "error": f"触发部署失败: 项目名 {project}",
                    "details": "未找到相关服务，请检查 API 密钥是否正确"
                }, 500

        # 部署第一个服务
        service = services[0]
        service_id = service.get('service', {}).get('id')
        service_name = service.get('service', {}).get('name')

        if not service_id:
            logger.error(f"无法获取服务ID: 项目名 {project}, 服务名称 {service_name}")
            return None, {
                "error": f"触发部署失败: 项目名 {project}, 服务名称 {service_name}",
                "details": "无法获取服务ID"
            }, 500

        self.logger.info(f"准备部署服务: 项目名 {project}, 服务名称 {service_name}")

        deploy_result = self.trigger_deploy(service_id, api_key)
        if deploy_result:
            deploy_id = deploy_result.get('id')
            self.logger.info(f"新的部署已触发: 项目名 {project}, 服务名称 {service_name}")

            # 启用多进程日志
            log_to_stderr()

            # 使用进程
            process = Process(
                target=self.check_deploy_and_notify,
                name=f"Process-{project}",
                args=(project, service_name, service_id, deploy_id, api_key)
            )
            process.start()
            self.logger.info(f"后台检查部署状态的进程已启动: 项目名: {project}, 服务名称 {service_name}")

            return {
                'message': '部署已触发',
                'project': project,
                'service_name': service_name,
                'service_id': service_id,
                'status': 'pending'
            }, None, 200
        else:
            return None, {
                "error": f"触发部署失败: 项目名 {project}, 服务名称 {service_name}",
                "details": "API 调用失败，请检查服务状态"
            }, 500
