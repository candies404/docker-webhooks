# 项目介绍
本项目利用docker webhooks 对render项目进行更新部署。项目使用 Flask 框架构建，并集成了多种通知服务。


## 主要功能

- **部署通知**：通过 `deploy_service.py` 发送部署成功或失败的通知。
- **Webhook 处理**：通过 `app.py` 接收和处理 webhook 请求。
- **通知服务**：通过 `notify.py` 提供多种通知方式，如 Bark、钉钉、飞书等。
- **项目服务**：通过 `project_service.py` 管理项目配置。
- **render服务**：通过 `render_service.py` 与外部 API 交互。

## Docker部署

`docker build -t you_image_name .`

```
docker run -d --name your_container_name \
   -p 5000:5000 \
   -e SECRET_TOKEN=your_secret_token \
   -e ONE_HUB_API_KEY=your_one_hub_api_key \
   -e UPTIME_KUMA_API_KEY=your_uptime_kuma_api_key \
   -e NAV_API_KEY=your_nav_api_key \
   -e DD_BOT_SECRET=your_DD_BOT_SECRET \
   -e DD_BOT_TOKEN=your_DD_BOT_TOKEN \
   -e TZ=Asia/Shanghai \
   your_image_name
````


## 手动部署

1. 克隆项目到本地：

```git clone https://github.com/candies404/Docker-webhooks.git```

2. 安装依赖：

```pip install -r requirements.txt```

3. 设置环境变量：

   ```bash
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

```python
python app.py
```

应用将运行在 `http://0.0.0.0:5000`。

## **API 端点**

- **GET /**: 返回主页。
- **GET /test**: 返回测试响应。
- **POST /webhook**: 处理 webhook 请求。

## **配置**

配置文件 [config.py](./config.py) ，可以通过环境变量进行配置。

## 如何添加新项目
要在 `config.py` 文件中添加一个新的项目，请按照以下步骤操作：
1. 打开 `config.py` 文件。
2. 找到 `PROJECT_CONFIG` 字典。
3. 在 `PROJECT_CONFIG` 字典中添加一个新的键值对，表示新的项目。以下是一个示例：
```python
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
               },
               'new-project': {  # 添加新的项目
                   'service_name': 'New Project',
                   'api_key': os.environ.get('NEW_PROJECT_API_KEY')  # 确保环境变量已设置
               }
           }
       }
```
4. 环境变量设置`NEW_PROJECT_API_KEY`对应值


