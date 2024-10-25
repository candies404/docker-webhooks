import os


def load_config():
    return {
        'SECRET_TOKEN': os.environ.get('SECRET_TOKEN'),
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
