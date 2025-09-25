# API端点测试
import pytest
import asyncio
import json
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def test_client():
    """测试客户端"""
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_root_endpoint(test_client):
    """测试根端点"""
    response = await test_client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "Twikit HTTP Service"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_endpoint(test_client):
    """测试健康检查端点"""
    response = await test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "twitter_status" in data


@pytest.mark.asyncio
async def test_tweet_endpoint_validation(test_client):
    """测试推文端点参数验证"""
    # 测试空文本
    response = await test_client.post(
        "/api/tweet",
        json={"text": ""}
    )
    assert response.status_code == 422  # 参数验证失败

    # 测试过长文本
    response = await test_client.post(
        "/api/tweet",
        json={"text": "a" * 300}  # 超过280字符
    )
    assert response.status_code == 422

    # 测试正常文本
    response = await test_client.post(
        "/api/tweet",
        json={"text": "测试推文"}
    )
    # 注意: 这里可能会失败，因为需要真实的Twitter凭据


@pytest.mark.asyncio
async def test_logs_endpoint(test_client):
    """测试日志端点"""
    response = await test_client.get("/api/logs")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "logs" in data["data"]


if __name__ == "__main__":
    pytest.main([__file__])