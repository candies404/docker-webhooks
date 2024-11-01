# 项目介绍
本项目利用docker webhooks 对render项目进行更新部署。项目使用 Flask 框架构建，并集成了多种通知服务。

## 主要功能
- **部署通知**：通过 `deploy_service.py` 发送部署成功或失败的通知。
- **Webhook 处理**：通过 `app.py` 接收和处理 webhook 请求。
- **通知服务**：通过 `notify.py` 提供多种通知方式，如 Bark、钉钉、飞书等。
- **项目服务**：通过 `project_service.py` 管理项目配置。
- **render服务**：通过 `render_service.py` 与外部 API 交互。

## 环境变量说明
| 变量名 | 说明 | 是否必填 | 示例 |
|-------|------|---------|------|
| SECRET_TOKEN | Webhook 安全令牌 | 是 | 至少8位字符 |
| ONE_HUB_API_KEY | One Hub 项目的 API 密钥 | 否 | render api key |
| UPTIME_KUMA_API_KEY | Uptime Kuma 项目的 API 密钥 | 否 | render api key |
| NAV_API_KEY | Nav 项目的 API 密钥 | 否 | render api key |
| DD_BOT_SECRET | 钉钉机器人加签密钥 | 否 | SEC... |
| DD_BOT_TOKEN | 钉钉机器人令牌 | 否 | accesstoken值... |
| TZ | 时区设置 | 否 | Asia/Shanghai |

## 推荐Docker部署

1. 构建镜像：
```bash
docker build -t docker-webhooks .
```

2. 运行容器：
```bash
docker run -d \
  --name docker-webhooks \
  -p 5000:5000 \
  -e SECRET_TOKEN=your_secret_token \
  -e ONE_HUB_API_KEY=your_one_hub_api_key \
  -e UPTIME_KUMA_API_KEY=your_uptime_kuma_api_key \
  -e NAV_API_KEY=your_nav_api_key \
  -e DD_BOT_SECRET=your_DD_BOT_SECRET \
  -e DD_BOT_TOKEN=your_DD_BOT_TOKEN \
  -e TZ=Asia/Shanghai \
  docker-webhooks
```

> **注意**：请确保将上述命令中的环境变量替换为实际的值。

## 手动部署

1. 克隆项目到本地：
```bash
git clone https://github.com/candies404/docker-webhooks.git
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量：
```bash
# Linux/Mac
export SECRET_TOKEN=your_secret_token
export ONE_HUB_API_KEY=your_one_hub_api_key
export UPTIME_KUMA_API_KEY=your_uptime_kuma_api_key
export NAV_API_KEY=your_nav_api_key
export DD_BOT_SECRET=your_DD_BOT_SECRET
export DD_BOT_TOKEN=your_DD_BOT_TOKEN
export TZ=Asia/Shanghai

# Windows
set SECRET_TOKEN=your_secret_token
set ONE_HUB_API_KEY=your_one_hub_api_key
set UPTIME_KUMA_API_KEY=your_uptime_kuma_api_key
set NAV_API_KEY=your_nav_api_key
set DD_BOT_SECRET=your_DD_BOT_SECRET
set DD_BOT_TOKEN=your_DD_BOT_TOKEN
set TZ=Asia/Shanghai
```

## 运行

在项目根目录下运行以下命令启动 Flask 应用：
```bash
python app.py
```
应用将运行在 `http://0.0.0.0:5000`。

## API 端点

### GET /
返回项目主页。

### GET /test
测试接口，返回当前配置信息。

**响应示例：**
```json
{
    "message": "这是一个测试响应",
    "timestamp": "2024-01-01T12:00:00",
    "app_config": {
        "BASE_URL": "https://api.render.com/v1",
        "PROJECT_COUNT": 2,
        "PROJECTS": ["one-hub", "nav"]
    }
}
```

### POST /webhook
处理来自 Docker Hub 的 webhook 请求，触发 Render 平台的项目部署。

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| project | string | 是 | 项目标识，如：'nav', 'one-hub' |
| token | string | 是 | 安全令牌，需与 SECRET_TOKEN 环境变量匹配 |

**请求示例：**
```bash
curl -X POST "http://your-domain/webhook?project=nav&token=your-secret-token" \
     -H "Content-Type: application/json" \
     -d '{"push_data": {"tag": "latest"}}'
```

**响应状态码：**

| 状态码 | 说明 |
|-------|------|
| 200 | 请求成功，部署已触发 |
| 400 | 请求无效（Content-Type 错误或负载格式错误） |
| 401 | 未提供认证令牌 |
| 403 | 认证令牌无效 |
| 429 | 请求过于频繁，需等待一分钟后重试 |
| 500 | 服务器内部错误 |

**成功响应示例：**
```json
{
    "status": "success",
    "message": "部署已触发",
    "project": "nav"
}
```

**错误响应示例：**
```json
{
    "error": "无效的 Content-Type，需要 application/json",
    "project": "nav"
}
```
或
```json
{
    "error": "部署请求过于频繁，请稍后再试",
    "project": "nav",
    "retry_after": "30秒"
}
```

## 配置说明
配置文件位于 `config.py`，主要通过环境变量进行配置。SECRET_TOKEN 为必填项且长度必须大于等于8位。

## 如何添加新项目
1. 在 `config.py` 的 `PROJECT_CONFIG` 中添加新项目配置：
```python
'PROJECT_CONFIG': {
    'new-project': {  # 项目标识
        'service_name': 'New Project',  # 项目名称
        'api_key': os.environ.get('NEW_PROJECT_API_KEY')  # API密钥环境变量
    }
}
```

2. 设置对应的环境变量 `NEW_PROJECT_API_KEY`

## 注意事项
- SECRET_TOKEN 必须设置且长度大于等于8位
- API 密钥需要从 Render 平台获取
- 建议使用 HTTPS 来保护 webhook 端点
