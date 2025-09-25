# 配置管理
import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置类"""

    # Twitter账号配置
    twitter_username: str = Field(..., env="TWITTER_USERNAME", description="Twitter用户名")
    twitter_email: str = Field(..., env="TWITTER_EMAIL", description="Twitter邮箱")
    twitter_password: str = Field(..., env="TWITTER_PASSWORD", description="Twitter密码")

    # 服务配置
    host: str = Field("0.0.0.0", env="HOST", description="服务主机地址")
    port: int = Field(8000, env="PORT", description="服务端口")

    # 数据库配置
    database_url: str = Field("sqlite+aiosqlite:///data/app.db", env="DATABASE_URL", description="数据库URL")

    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL", description="日志级别")

    # 重试配置
    max_retry_attempts: int = Field(3, env="MAX_RETRY_ATTEMPTS", description="最大重试次数")
    retry_delay: int = Field(2, env="RETRY_DELAY", description="重试延迟(秒)")

    # 文件路径
    cookies_file: str = Field("data/cookies.json", description="Cookie文件路径")
    log_file: str = Field("data/app.log", description="日志文件路径")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def validate_config(self) -> bool:
        """验证配置完整性"""
        required_fields = [
            self.twitter_username,
            self.twitter_email,
            self.twitter_password
        ]

        missing_fields = []
        for field in required_fields:
            if not field:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"缺少必要配置: {missing_fields}")

        return True


# 全局配置实例
settings = Settings()