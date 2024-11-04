# 项目介绍

本项目利用docker webhooks 对render项目进行更新部署。项目使用 Flask 框架构建，并集成了多种通知服务。

## 主要功能

1. 项目配置管理：通过 services/project_service.py 管理多项目配置，支持动态配置项目和API密钥。

2. Webhook 处理：通过 routes/webhook.py 接收和处理 Docker Hub 的 webhook 请求，支持请求验证和频率限制。

3. Render 服务集成：通过 services/render_service.py 与 Render 平台 API 交互，处理服务部署和状态检查。

4. 通知服务：通过 notify.py 提供丰富的通知渠道支持：

    - 支持 Bark、钉钉、飞书、Telegram 等多种通知方式

    - 支持邮件通知

    - 支持自定义 Webhook

    - 使用时请根据需求选择通知服务并配置相应环境变量

5. 部署流程管理：

    - 防并发部署的文件锁机制

    - 部署频率限制

    - 异步部署状态检查

    - 自定义域名支持

    - 部署结果通知

6. 统一错误处理：通过 utils/response.py 提供标准化的 JSON 响应格式，支持中文输出。

7. 完善的日志系统：分离应用日志和访问日志，提供详细的操作记录。

## 环境变量说明

| 变量名                | 说明                           | 是否必填 | 示例             |
| --------------------- | ------------------------------ | -------- | ---------------- |
| SECRET_TOKEN          | Webhook 安全令牌               | 是       | 至少8位字符      |
| ONE_HUB_API_KEY       | One Hub 项目的 API 密钥        | 否       | render api key   |
| UPTIME_KUMA_API_KEY   | Uptime Kuma 项目的 API 密钥    | 否       | render api key   |
| NAV_API_KEY           | Nav 项目的 API 密钥            | 否       | render api key   |
| DD_BOT_SECRET         | 钉钉机器人加签密钥             | 否       | SEC...           |
| DD_BOT_TOKEN          | 钉钉机器人令牌                 | 否       | accesstoken值... |
| TZ                    | 时区设置                       | 否       | Asia/Shanghai    |
| DEPLOY_INTERVAL       | 两次同一项目部署间隔时间(秒)   | 否       | 60（默认值）     |
| MAX_DEPLOY_RETRIES    | 部署状态查询重试次数           | 否       | 5（默认值）      |
| DEPLOY_CHECK_INTERVAL | 部署状态检查间隔(秒)           | 否       | 60（默认值）     |
| PREFER_CUSTOM_DOMAIN  | 域名显示配置默认显示自定义域名 | 否       | false            |

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

| 参数    | 类型   | 必填 | 说明                                     |
| ------- | ------ | ---- | ---------------------------------------- |
| project | string | 是   | 项目标识，如：'nav', 'one-hub'           |
| token   | string | 是   | 安全令牌，需与 SECRET_TOKEN 环境变量匹配 |

**请求示例：**

```bash
curl -X POST "http://your-domain/webhook?project=nav&token=your-secret-token" \
     -H "Content-Type: application/json" \
     -d '{"push_data": {"tag": "latest"}}'
```

**响应状态码：**

| 状态码 | 说明                                        |
| ------ | ------------------------------------------- |
| 200    | 请求成功，部署已触发                        |
| 400    | 请求无效（Content-Type 错误或负载格式错误） |
| 401    | 未提供认证令牌                              |
| 403    | 认证令牌无效                                |
| 429    | 请求过于频繁，需等待一分钟后重试            |
| 500    | 服务器内部错误                              |

**成功响应示例：**

```json
{
  "message": "部署已触发",
  "project": "one-hub",
  "service_id": "srv-csjjbgjtq21c73ddm2n0",
  "service_name": "one-hub",
  "status": "pending"
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
  "details": "系统限制项目 one-hub 每 60 秒只能部署一次",
  "error": "部署请求过于频繁",
  "retry_after": "53秒",
  "status": "rate_limited"
}
```

## 配置说明

配置文件位于 `config/settings.py`，主要通过环境变量进行配置。SECRET_TOKEN 为必填项且长度必须大于等于8位。

## 如何添加新项目

1. 在 `config/settings.py` 的 `PROJECT_CONFIG` 中添加新项目配置：

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
