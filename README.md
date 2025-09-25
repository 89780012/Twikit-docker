# Twikit HTTP Service

基于twikit库的Twitter发布服务，为n8n工作流提供HTTP API。

## 功能特性

- 🚀 **FastAPI异步框架** - 高性能，自动生成API文档
- 📝 **多功能推文** - 支持文本、媒体、回复推文
- 🔄 **智能重试机制** - 3次异常重试，自动错误恢复
- 💾 **数据持久化** - SQLite存储Cookie和操作日志
- 🐳 **Docker容器化** - 一键部署，环境隔离
- 🔧 **n8n集成友好** - JSON API，无需认证，开箱即用
- 📊 **健康检查** - 实时监控服务和Twitter连接状态
- 📝 **完整日志** - 详细的操作记录和错误追踪

## 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，配置Twitter账号信息
vim .env
```

**必需配置项**：
```env
TWITTER_USERNAME=your_twitter_username
TWITTER_EMAIL=your_email@example.com
TWITTER_PASSWORD=your_password
```

### 2. Docker部署

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

### 3. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
# 浏览器访问: http://localhost:8000/docs
```

## API接口

### 发布推文

**端点**: `POST /api/tweet`

**请求示例**:
```json
{
  "text": "Hello from n8n! 🚀",
  "media": ["data:image/jpeg;base64,/9j/4AAQ..."],
  "reply_to": "1234567890123456789"
}
```

**响应示例**:
```json
{
  "success": true,
  "tweet_id": "1789012345678901234",
  "message": "推文发布成功",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 健康检查

**端点**: `GET /health`

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "twitter_status": "connected"
}
```

### 操作日志

**端点**: `GET /api/logs?limit=50`

**响应示例**:
```json
{
  "success": true,
  "message": "日志获取成功",
  "data": {
    "logs": [...],
    "total": 10
  }
}
```

## n8n集成指南

### 1. HTTP Request节点配置

- **方法**: POST
- **URL**: `http://localhost:8000/api/tweet`
- **Headers**: `Content-Type: application/json`

### 2. 请求体配置

**纯文本推文**:
```json
{
  "text": "{{$json.message}}"
}
```

**带媒体推文**:
```json
{
  "text": "{{$json.message}}",
  "media": ["{{$json.image_base64}}"]
}
```

**回复推文**:
```json
{
  "text": "{{$json.reply_text}}",
  "reply_to": "{{$json.original_tweet_id}}"
}
```

### 3. 错误处理

n8n可以通过响应中的`success`字段判断操作是否成功：

```javascript
// n8n表达式
{{$json.success === true}}
```

### 4. n8n工作流示例

```json
{
  "name": "Twitter发布工作流",
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8000/api/tweet",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "{\n  \"text\": \"{{$json.content}}\"\n}"
      }
    }
  ]
}
```

## 部署配置

### Docker Compose配置

```yaml
version: '3.8'
services:
  twikit-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TWITTER_USERNAME=${TWITTER_USERNAME}
      - TWITTER_EMAIL=${TWITTER_EMAIL}
      - TWITTER_PASSWORD=${TWITTER_PASSWORD}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `TWITTER_USERNAME` | ✅ | - | Twitter用户名 |
| `TWITTER_EMAIL` | ✅ | - | Twitter注册邮箱 |
| `TWITTER_PASSWORD` | ✅ | - | Twitter密码 |
| `PORT` | ❌ | 8000 | 服务端口 |
| `LOG_LEVEL` | ❌ | INFO | 日志级别 |
| `MAX_RETRY_ATTEMPTS` | ❌ | 3 | 最大重试次数 |

## 项目结构

```
twikit-http-service/
├── app/                      # 应用代码
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── models.py            # 数据模型
│   ├── twitter_client.py    # Twitter客户端封装
│   ├── database.py          # 数据库管理
│   └── utils.py             # 工具函数
├── data/                    # 数据目录（持久化）
│   ├── cookies.json         # Twitter会话Cookie
│   ├── app.db              # SQLite数据库
│   └── app.log             # 应用日志
├── tests/                   # 测试代码
│   ├── test_api.py
│   └── test_twitter.py
├── Dockerfile              # Docker镜像构建
├── docker-compose.yml      # Docker编排配置
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量模板
├── .dockerignore          # Docker忽略文件
└── README.md              # 项目文档
```

## 故障排除

### 1. Twitter认证失败

**问题**: 服务启动后无法连接Twitter

**解决方案**:
- 确认Twitter账号密码正确
- 检查Twitter账号是否开启双因素认证（暂不支持）
- 查看日志：`docker-compose logs`

### 2. 推文发布失败

**问题**: API返回Twitter相关错误

**解决方案**:
- 检查推文长度（不超过280字符）
- 验证媒体格式和大小
- 查看错误详情：`GET /api/logs`

### 3. 服务无法启动

**问题**: Docker容器启动失败

**解决方案**:
- 检查`.env`文件配置
- 确保8000端口未被占用
- 运行：`bash verify_deployment.sh`

### 4. n8n连接超时

**问题**: n8n无法访问服务

**解决方案**:
- 检查网络连通性
- 确认端口映射：`docker-compose ps`
- 防火墙设置检查

## 技术栈

- **FastAPI** - 现代Python Web框架，高性能异步API
- **twikit** - Twitter操作库，无需API Key
- **SQLite + aiosqlite** - 轻量级异步数据库
- **Docker** - 容器化部署
- **Pydantic** - 数据验证和序列化
- **tenacity** - 重试机制库
- **uvicorn** - ASGI服务器

## 开发和贡献

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
python -m app.main

# 运行测试
pytest tests/
```

### 代码规范

- 使用Python 3.11+
- 遵循PEP 8代码规范
- 添加类型注解
- 编写单元测试

## 许可证

MIT License

## 更新日志

### v1.0.0 (2024-01-15)

- ✨ 初始版本发布
- 🚀 FastAPI基础框架
- 📝 推文发布功能
- 🔄 异常重试机制
- 🐳 Docker容器化支持
- 📖 完整文档和n8n集成指南