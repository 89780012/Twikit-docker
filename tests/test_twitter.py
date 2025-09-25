# Twitter客户端测试
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

from app.twitter_client import TwitterService, TwitterClientError


@pytest.fixture
def twitter_service():
    """创建测试用的Twitter服务实例"""
    return TwitterService(
        username="test_user",
        email="test@example.com",
        password="test_password",
        cookies_file="test_cookies.json"
    )


@pytest.mark.asyncio
async def test_authentication_success(twitter_service):
    """测试认证成功"""
    with patch.object(twitter_service.client, 'login', new_callable=AsyncMock) as mock_login, \
         patch.object(twitter_service.client, 'save_cookies') as mock_save, \
         patch.object(twitter_service, '_test_authentication', new_callable=AsyncMock) as mock_test:

        result = await twitter_service.authenticate()

        assert result is True
        assert twitter_service._authenticated is True
        mock_login.assert_called_once()
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_authentication_failure(twitter_service):
    """测试认证失败"""
    with patch.object(twitter_service.client, 'login', new_callable=AsyncMock, side_effect=Exception("Login failed")):
        with pytest.raises(TwitterClientError):
            await twitter_service.authenticate()


@pytest.mark.asyncio
async def test_create_tweet_success(twitter_service):
    """测试推文发布成功"""
    mock_tweet = MagicMock()
    mock_tweet.id = "123456789"
    mock_tweet.text = "测试推文"
    mock_tweet.created_at = "2024-01-15T10:30:00Z"
    mock_tweet.user.id = "user123"
    mock_tweet.user.name = "Test User"

    with patch.object(twitter_service, 'authenticate', new_callable=AsyncMock) as mock_auth, \
         patch.object(twitter_service.client, 'create_tweet', new_callable=AsyncMock, return_value=mock_tweet) as mock_create:

        twitter_service._authenticated = True
        result = await twitter_service.create_tweet("测试推文")

        assert result["tweet_id"] == "123456789"
        assert result["text"] == "测试推文"
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_tweet_with_media(twitter_service):
    """测试带媒体的推文发布"""
    mock_tweet = MagicMock()
    mock_tweet.id = "123456789"
    mock_tweet.text = "测试推文"
    mock_tweet.created_at = "2024-01-15T10:30:00Z"
    mock_tweet.user.id = "user123"
    mock_tweet.user.name = "Test User"

    # Mock base64 媒体数据
    media_data = ["data:image/jpeg;base64,/9j/4AAQSkZJRg=="]

    with patch.object(twitter_service, 'authenticate', new_callable=AsyncMock), \
         patch.object(twitter_service, '_upload_media', new_callable=AsyncMock, return_value=["media123"]) as mock_upload, \
         patch.object(twitter_service.client, 'create_tweet', new_callable=AsyncMock, return_value=mock_tweet) as mock_create:

        twitter_service._authenticated = True
        result = await twitter_service.create_tweet("测试推文", media_data=media_data)

        assert result["tweet_id"] == "123456789"
        mock_upload.assert_called_once()
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_health_check(twitter_service):
    """测试健康检查"""
    with patch.object(twitter_service, 'authenticate', new_callable=AsyncMock), \
         patch.object(twitter_service, '_test_authentication', new_callable=AsyncMock):

        twitter_service._authenticated = True
        result = await twitter_service.health_check()

        assert result["status"] == "connected"
        assert "Twitter API连接正常" in result["message"]


def test_media_upload_base64_parsing():
    """测试base64媒体数据解析"""
    # 这是一个简单的单元测试，不需要实际的Twitter连接
    import base64

    # 测试数据
    test_data = b"test image data"
    encoded_data = base64.b64encode(test_data).decode()
    full_data = f"data:image/jpeg;base64,{encoded_data}"

    # 解析
    if full_data.startswith('data:'):
        header, data = full_data.split(',', 1)
        mime_type = header.split(';')[0].split(':')[1]
        decoded_data = base64.b64decode(data)

        assert mime_type == "image/jpeg"
        assert decoded_data == test_data


if __name__ == "__main__":
    pytest.main([__file__])