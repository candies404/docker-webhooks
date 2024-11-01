import logging
import sys
from flask import Flask, request, render_template, current_app, json, make_response
import os
from datetime import datetime, timedelta
from config import load_config
from services.deploy_service import handle_webhook
from services.render_service import RenderService
from services.project_service import ProjectService


# 配置日志
def configure_logging():
    # 使用更具体的logger名称，而不是root
    logger = logging.getLogger('docker-hooks')
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# 在应用初始化时调用
logger = configure_logging()

app = Flask(__name__)

# 设置 JSON 编码为 UTF-8
app.config['JSON_AS_ASCII'] = False
# 这个设置决定了 JSON 响应是否应该被格式化（美化打印）
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# 加载配置
try:
    config = load_config()
    app.config.update(config)
except ValueError as e:
    logger.error(f"配置加载失败: {str(e)}")
    sys.exit(1)

# 添加部署状态跟踪
last_deploy_time = {}


# JSON响应处理函数
def json_response(data, status_code=200):
    return make_response(
        json.dumps(data, ensure_ascii=False, indent=2),
        status_code,
        {'Content-Type': 'application/json; charset=utf-8'}
    )


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)

# app.logger = logger

# 初始化服务
render_service = RenderService(app.config['BASE_URL'])
project_service = ProjectService(app.config['PROJECT_CONFIG'])


@app.route('/')
def home():
    current_app.logger.info("访问了首页")
    return render_template('index.html')


@app.route('/test', methods=['GET'])
def test():
    current_app.logger.info("收到测试请求")

    valid_projects = [
        project_name
        for project_name, config in app.config['PROJECT_CONFIG'].items()
        if config.get('api_key')
    ]

    data = {
        'message': '这是一个测试响应',
        'timestamp': datetime.now().isoformat(),
        'app_config': {
            'BASE_URL': app.config['BASE_URL'],
            'PROJECT_COUNT': len(valid_projects),
            'PROJECTS': valid_projects
        }
    }

    return json_response(data)


@app.route('/webhook', methods=['POST'])
def webhook():
    current_app.logger.info("收到 webhook 请求")
    if not request.is_json:
        current_app.logger.error("无效的 Content-Type，需要 application/json")
        return json_response({'error': '无效的 Content-Type，需要 application/json'}, 400)

    # 确保请求中包含 token
    token = request.args.get('token')
    if not token:
        return json_response({'error': '缺少认证令牌'}, 401)

    # 使用安全的比较方法
    if token != app.config['SECRET_TOKEN']:
        return json_response({'error': '无效的令牌'}, 403)

    project = request.args.get('project')
    if not project_service.is_valid_project(project):
        current_app.logger.error(f"无效的项目名称: {project}")
        return json_response({'error': '无效的项目名称'}, 400)

    payload = request.json
    if not payload or 'push_data' not in payload:
        current_app.logger.error("无效的负载")
        return json_response({'error': '无效的负载'}, 400)

    # 检查上次部署时间
    now = datetime.now()
    if project in last_deploy_time:
        time_since_last_deploy = now - last_deploy_time[project]
        if time_since_last_deploy < timedelta(minutes=1):
            # 计算还需要等待的秒数
            remaining_seconds = 60 - time_since_last_deploy.seconds
            current_app.logger.warning(f"项目 {project} 在1分钟内已经触发过部署，还需等待 {remaining_seconds} 秒")
            return json_response({
                'error': '部署请求过于频繁，请稍后再试',
                'project': project,
                'retry_after': f"{remaining_seconds}秒"
            }, 429)

    # 更新最后部署时间
    last_deploy_time[project] = now

    try:
        project_config = project_service.get_project_config(project)
        api_key = project_config['api_key']

        response, error, status_code = handle_webhook(render_service, project, api_key)
        if error:
            current_app.logger.error(f"处理 webhook 时出错: {error}")
            return json_response({'error': error, 'project': project}, status_code)

        current_app.logger.info(f"成功处理 webhook: {project}")
        return json_response(response, status_code)

    except Exception as e:
        current_app.logger.exception(f'处理 webhook 时出错: 项目 {project}')
        return json_response({
            'error': '处理 webhook 时出错',
            'project': project,
            'details': str(e)
        }, 500)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.logger.info(f"应用正在直接启动，监听端口 {port}")
    app.run(host='0.0.0.0', port=port)
