# 使用Pydantic定义请求和响应数据模型
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class TweetRequest(BaseModel):
    """推文发布请求模型"""
    text: str = Field(..., min_length=1, max_length=280, description="推文文本内容")
    media: Optional[List[str]] = Field(None, description="媒体文件列表(base64编码)")
    reply_to: Optional[str] = Field(None, description="回复的推文ID")


class TweetResponse(BaseModel):
    """推文发布响应模型"""
    success: bool = Field(..., description="操作是否成功")
    tweet_id: Optional[str] = Field(None, description="发布的推文ID")
    message: str = Field(..., description="响应消息")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="操作失败")
    error_code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[str] = Field(None, description="详细错误信息")


class TweetLog(BaseModel):
    """推文日志模型"""
    id: Optional[int] = Field(None, description="日志ID")
    tweet_id: Optional[str] = Field(None, description="推文ID")
    text: str = Field(..., description="推文内容")
    status: str = Field(..., description="状态: success, failed, retrying")
    retry_count: int = Field(0, description="重试次数")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field("healthy", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    twitter_status: str = Field(..., description="Twitter连接状态")