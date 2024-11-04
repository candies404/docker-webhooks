import os
import re

from config import BASE_API_URL


def load_config():
    # 验证 SECRET_TOKEN
    secret_token = os.environ.get('SECRET_TOKEN')
    if not secret_token:
        raise ValueError("环境变量 SECRET_TOKEN 未设置")
    if len(str(secret_token)) < 8:
        raise ValueError("SECRET_TOKEN 长度必须大于等于8位")

    # 正则表达式：验证项目标识格式（字母、数字、下划线、连字符）
    project_id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    # 正则表达式：验证环境变量格式（PROJECT__项目标识__配置键）
    env_var_pattern = re.compile(r'^PROJECT__[a-zA-Z0-9_-]+__(SERVICE_NAME|API_KEY)$', re.IGNORECASE)

    # 存储所有项目的配置信息
    projects_config = {}

    # 遍历环境变量，查找项目配置
    for env_key, env_value in os.environ.items():
        # 检查是否匹配项目配置格式（如：PROJECT__test__API_KEY）
        if env_var_pattern.match(env_key):
            # 拆分环境变量名（如：["PROJECT", "test", "API_KEY"]）
            parts = env_key.split('__')
            # 统一项目标识为小写（如：TEST -> test）
            project_id = parts[1].lower()
            # 统一配置项键名为小写（如：API_KEY -> api_key）
            config_key = parts[2].lower()

            # 验证项目标识是否包含非法字符
            if not project_id_pattern.match(project_id):
                raise ValueError(f"项目标识 '{project_id}' 格式无效，只能包含字母、数字、下划线和连字符")

            # 初始化项目配置字典
            if project_id not in projects_config:
                projects_config[project_id] = {}
            # 保存配置值（保持原始大小写）
            projects_config[project_id][config_key] = env_value

    # 确保至少存在一个项目配置
    if not projects_config:
        raise ValueError("未找到任何项目配置，请设置 PROJECT__*__* 环境变量")

    # 验证每个项目的必需配置项
    for project_id, config in projects_config.items():
        if 'api_key' not in config:
            raise ValueError(f"项目 '{project_id}' 缺少必需的 API_KEY 配置")
        if 'service_name' not in config:
            raise ValueError(f"项目 '{project_id}' 缺少必需的 SERVICE_NAME 配置")

    # 返回完整配置
    return {
        'SECRET_TOKEN': secret_token,
        'BASE_URL': BASE_API_URL,
        'PROJECT_CONFIG': projects_config
    }
