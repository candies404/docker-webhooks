import requests
import logging
import time

logger = logging.getLogger(__name__)


class RenderService:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = logger

    def get_services(self, api_key):
        self.logger.info("正在获取服务列表")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        response = requests.get(f"{self.base_url}/services", headers=headers)
        if response.status_code == 200:
            services = response.json()
            logger.info(f"获取到 {len(services)} 个服务")
            self.log_service_names(services)
            return services
        else:
            logger.error(f"获取服务列表失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None

    def log_service_names(self, services):
        for service in services:
            name = service.get('service', {}).get('name')
            service_id = service.get('service', {}).get('id')
            logger.info(f"服务名称: {name}, ID: {service_id}")

    def trigger_deploy(self, service_id, api_key):
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

    def check_deploy_status(self, service_id, deploy_id, api_key, max_retries=10, interval=60):
        """
        检查部署状态，直到部署成功或失败，或达到最大重试次数。
        """
        url = f"{self.base_url}/services/{service_id}/deploys/{deploy_id}"
        headers = {"Authorization": f"Bearer {api_key}"}

        retries = 0
        while retries < max_retries:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"无法获取部署状态: {response.status_code}")
                return False

            deploy_info = response.json()
            status = deploy_info.get("status")

            if status == "live":
                return True
            elif status in ["failed", "canceled"]:
                return False

            time.sleep(interval)  # 等待指定的间隔时间后重试
            retries += 1

        logger.error("检查部署状态超时")
        return False
