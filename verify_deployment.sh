#!/bin/bash

# 部署验证脚本

echo "🚀 开始验证 Twikit HTTP Service 部署..."

# 检查必要文件
echo "📁 检查项目文件..."
required_files=(
    "requirements.txt"
    "Dockerfile"
    "docker-compose.yml"
    ".env.example"
    "app/main.py"
    "app/config.py"
    "app/models.py"
    "app/twitter_client.py"
    "app/database.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    else
        echo "✅ $file 存在"
    fi
done

# 检查.env文件
if [[ ! -f ".env" ]]; then
    echo "⚠️  警告: .env 文件不存在，请复制 .env.example 并配置"
    echo "   cp .env.example .env"
    echo "   然后编辑 .env 文件填入您的 Twitter 账号信息"
fi

# 检查数据目录
echo "📂 创建数据目录..."
mkdir -p data logs

# 检查Docker环境
echo "🐳 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 未安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 构建镜像 (可选 - 仅验证)
echo "🔨 验证 Docker 镜像构建..."
if docker build -t twikit-service-test . --quiet; then
    echo "✅ Docker 镜像构建成功"
    docker rmi twikit-service-test 2>/dev/null
else
    echo "❌ Docker 镜像构建失败"
    exit 1
fi

# 验证Python语法
echo "🐍 验证 Python 代码语法..."
python_files=(
    "app/main.py"
    "app/config.py"
    "app/models.py"
    "app/twitter_client.py"
    "app/database.py"
)

for file in "${python_files[@]}"; do
    if python -m py_compile "$file"; then
        echo "✅ $file 语法正确"
    else
        echo "❌ $file 语法错误"
        exit 1
    fi
done

# 显示部署说明
echo ""
echo "🎉 验证完成！项目已准备就绪"
echo ""
echo "📋 部署步骤:"
echo "1. 配置环境变量:"
echo "   cp .env.example .env"
echo "   编辑 .env 文件填入 Twitter 账号信息"
echo ""
echo "2. 启动服务:"
echo "   docker-compose up -d"
echo ""
echo "3. 检查服务状态:"
echo "   docker-compose logs -f"
echo ""
echo "4. 访问API文档:"
echo "   http://localhost:8000/docs"
echo ""
echo "5. 测试健康检查:"
echo "   curl http://localhost:8000/health"
echo ""
echo "🔗 n8n 集成示例:"
echo "POST http://localhost:8000/api/tweet"
echo "Content-Type: application/json"
echo '{"text": "Hello from n8n! 🚀"}'
echo ""
echo "✨ 部署验证完成！"