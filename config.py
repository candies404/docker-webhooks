import os


def load_config():
    secret_token = os.environ.get('SECRET_TOKEN')

    # 验证 SECRET_TOKEN
    if not secret_token:
        raise ValueError("环境变量 SECRET_TOKEN 未设置")
    if len(str(secret_token)) < 8:
        raise ValueError("SECRET_TOKEN 长度必须大于等于8位")

    return {
        'SECRET_TOKEN': secret_token,
        'BASE_URL': "https://api.render.com/v1",
        'PROJECT_CONFIG': {
            'one-hub': {
                'service_name': 'One Hub',
                'api_key': os.environ.get('ONE_HUB_API_KEY')
            },
            'uptime-kuma': {
                'service_name': 'Uptime Kuma',
                'api_key': os.environ.get('UPTIME_KUMA_API_KEY')
            },
            'nav': {
                'service_name': 'Nav',
                'api_key': os.environ.get('NAV_API_KEY')
            }
        }
    }
