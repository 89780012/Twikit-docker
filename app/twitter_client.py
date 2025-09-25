# Twitter客户端异步封装
import asyncio
import base64
import logging
import os
from typing import Optional, List, Dict, Any
from twikit import Client
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from .database import db_manager


logger = logging.getLogger(__name__)


class TwitterClientError(Exception):
    """Twitter客户端异常"""
    pass


class TwitterService:
    """Twitter服务封装类"""

    def __init__(self, username: str, email: str, password: str, cookies_file: str = "data/cookies.json"):
        self.username = username
        self.email = email
        self.password = password
        self.cookies_file = cookies_file
        self.client = Client('zh-CN')  # 支持中文界面
        self._authenticated = False

    async def authenticate(self) -> bool:
        """认证登录Twitter账号"""
        try:
            # 尝试加载已保存的cookies
            if os.path.exists(self.cookies_file):
                logger.info("尝试加载已保存的cookies")
                self.client.load_cookies(self.cookies_file)

                # 验证cookies是否有效
                try:
                    # 简单的API调用验证会话
                    await self._test_authentication()
                    self._authenticated = True
                    logger.info("使用已保存cookies认证成功")
                    return True
                except Exception as e:
                    logger.warning(f"保存的cookies无效: {e}")

            # cookies无效或不存在，执行完整登录
            logger.info("开始执行Twitter账号登录")
            await self.client.login(
                auth_info_1=self.username,
                auth_info_2=self.email,
                password=self.password
            )

            # 保存cookies到文件
            os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
            self.client.save_cookies(self.cookies_file)

            self._authenticated = True
            logger.info("Twitter账号认证成功，cookies已保存")
            return True

        except Exception as e:
            logger.error(f"Twitter认证失败: {e}")
            raise TwitterClientError(f"认证失败: {str(e)}")

    async def _test_authentication(self):
        """测试认证状态"""
        # 通过获取账号信息验证认证状态
        user = await self.client.get_user_by_screen_name(self.username)
        if not user:
            raise TwitterClientError("认证测试失败")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def create_tweet(self, text: str, media_data: Optional[List[str]] = None,
                          reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        发布推文

        Args:
            text: 推文文本
            media_data: 媒体数据列表(base64编码)
            reply_to: 回复的推文ID

        Returns:
            包含tweet_id等信息的字典
        """
        if not self._authenticated:
            await self.authenticate()

        try:
            # 处理媒体上传
            media_ids = []
            if media_data:
                media_ids = await self._upload_media(media_data)

            # 发布推文
            logger.info(f"发布推文: {text[:50]}...")

            if reply_to:
                # 回复推文
                tweet = await self.client.create_tweet(
                    text=text,
                    media_ids=media_ids if media_ids else None,
                    reply_to=reply_to
                )
            else:
                # 普通推文
                tweet = await self.client.create_tweet(
                    text=text,
                    media_ids=media_ids if media_ids else None
                )

            result = {
                "tweet_id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "user_id": tweet.user.id,
                "user_name": tweet.user.name
            }

            logger.info(f"推文发布成功: {tweet.id}")
            return result

        except Exception as e:
            error_msg = f"发布推文失败: {str(e)}"
            logger.error(error_msg)

            # 如果是认证相关错误，重置认证状态
            if any(keyword in str(e).lower() for keyword in ['auth', 'login', 'unauthorized', 'forbidden']):
                self._authenticated = False
                logger.warning("检测到认证错误，已重置认证状态")

            raise TwitterClientError(error_msg)

    async def _upload_media(self, media_data_list: List[str]) -> List[str]:
        """
        上传媒体文件

        Args:
            media_data_list: base64编码的媒体数据列表

        Returns:
            媒体ID列表
        """
        media_ids = []

        for i, media_data in enumerate(media_data_list):
            try:
                # 解析base64数据
                if media_data.startswith('data:'):
                    # 格式: data:image/jpeg;base64,/9j/4AAQ...
                    header, data = media_data.split(',', 1)
                    mime_type = header.split(';')[0].split(':')[1]
                else:
                    data = media_data
                    mime_type = "image/jpeg"  # 默认类型

                # 解码base64
                media_bytes = base64.b64decode(data)

                # 保存临时文件
                temp_filename = f"temp_media_{i}.jpg"
                with open(temp_filename, 'wb') as f:
                    f.write(media_bytes)

                # 上传到Twitter
                media_id = await self.client.upload_media(temp_filename)
                media_ids.append(media_id)

                # 删除临时文件
                os.unlink(temp_filename)

                logger.info(f"媒体上传成功: {media_id}")

            except Exception as e:
                logger.error(f"媒体上传失败 ({i}): {e}")
                # 清理可能的临时文件
                if os.path.exists(f"temp_media_{i}.jpg"):
                    os.unlink(f"temp_media_{i}.jpg")
                raise TwitterClientError(f"媒体上传失败: {str(e)}")

        return media_ids

    async def get_tweet_info(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """获取推文信息"""
        if not self._authenticated:
            await self.authenticate()

        try:
            tweet = await self.client.get_tweet_by_id(tweet_id)
            return {
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "user_name": tweet.user.name,
                "like_count": getattr(tweet, 'favorite_count', 0),
                "retweet_count": getattr(tweet, 'retweet_count', 0)
            }
        except Exception as e:
            logger.error(f"获取推文信息失败: {e}")
            return None

    async def health_check(self) -> Dict[str, str]:
        """健康检查"""
        try:
            if not self._authenticated:
                await self.authenticate()

            # 简单的API调用测试
            await self._test_authentication()
            return {"status": "connected", "message": "Twitter API连接正常"}
        except Exception as e:
            return {"status": "disconnected", "message": f"Twitter API连接异常: {str(e)}"}


# 全局Twitter服务实例（延迟初始化）
twitter_service: Optional[TwitterService] = None


def get_twitter_service() -> TwitterService:
    """获取Twitter服务实例"""
    if twitter_service is None:
        raise RuntimeError("Twitter服务未初始化")
    return twitter_service