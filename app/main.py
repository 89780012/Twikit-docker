# FastAPI主应用
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import TweetRequest, TweetResponse, ErrorResponse, HealthResponse
from .twitter_client import TwitterService, TwitterClientError, get_twitter_service, twitter_service
from .database import db_manager
from .utils import setup_logging, format_error_response, format_success_response

# 设置日志
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Twikit HTTP Service",
    description="基于twikit库的Twitter发布服务API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    try:
        logger.info("正在启动Twikit HTTP服务...")

        # 验证配置
        settings.validate_config()
        logger.info("配置验证通过")

        # 初始化数据库
        await db_manager.init_database()
        logger.info("数据库初始化完成")

        # 初始化Twitter服务
        global twitter_service
        twitter_service = TwitterService(
            username=settings.twitter_username,
            email=settings.twitter_email,
            password=settings.twitter_password,
            cookies_file=settings.cookies_file
        )

        # 预热Twitter连接
        try:
            await twitter_service.authenticate()
            logger.info("Twitter服务预热成功")
        except Exception as e:
            logger.warning(f"Twitter服务预热失败，将在首次请求时重试: {e}")

        logger.info("Twikit HTTP服务启动完成")

    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("正在关闭Twikit HTTP服务...")


@app.exception_handler(TwitterClientError)
async def twitter_error_handler(request, exc: TwitterClientError):
    """Twitter客户端异常处理"""
    logger.error(f"Twitter操作异常: {exc}")
    return JSONResponse(
        status_code=400,
        content=format_error_response(
            error_code="TWITTER_ERROR",
            message="Twitter操作失败",
            details=str(exc)
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=format_error_response(
            error_code="INTERNAL_ERROR",
            message="内部服务器错误",
            details=str(exc)
        )
    )


@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "service": "Twikit HTTP Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    try:
        # 检查Twitter服务状态
        twitter_status = await get_twitter_service().health_check()

        return HealthResponse(
            status="healthy",
            twitter_status=twitter_status["status"]
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            twitter_status="error"
        )


async def process_tweet_async(tweet_data: TweetRequest, log_id: int):
    """异步处理推文发布"""
    try:
        # 获取Twitter服务
        service = get_twitter_service()

        # 发布推文
        result = await service.create_tweet(
            text=tweet_data.text,
            media_data=tweet_data.media,
            reply_to=tweet_data.reply_to
        )

        # 更新日志
        await db_manager.update_tweet_log(
            log_id=log_id,
            tweet_id=result["tweet_id"],
            status="success"
        )

        logger.info(f"推文发布成功: {result['tweet_id']}")
        return result

    except Exception as e:
        logger.error(f"推文发布失败: {e}")

        # 更新日志
        await db_manager.update_tweet_log(
            log_id=log_id,
            status="failed",
            error_message=str(e)
        )
        raise


@app.post("/api/tweet", response_model=TweetResponse)
async def create_tweet(tweet_data: TweetRequest, background_tasks: BackgroundTasks):
    """
    发布推文API端点

    - **text**: 推文文本内容 (必填, 1-280字符)
    - **media**: 媒体文件列表，base64编码 (可选)
    - **reply_to**: 回复的推文ID (可选)

    返回:
    - **success**: 操作是否成功
    - **tweet_id**: 发布的推文ID
    - **message**: 响应消息
    - **created_at**: 创建时间
    """
    try:
        logger.info(f"收到推文发布请求: {tweet_data.text[:50]}...")

        # 记录请求日志
        log_id = await db_manager.log_tweet(
            text=tweet_data.text,
            status="processing"
        )

        # 异步处理推文发布
        try:
            result = await process_tweet_async(tweet_data, log_id)

            return TweetResponse(
                success=True,
                tweet_id=result["tweet_id"],
                message="推文发布成功",
                created_at=result.get("created_at")
            )

        except TwitterClientError as e:
            # Twitter相关错误
            await db_manager.update_tweet_log(
                log_id=log_id,
                status="failed",
                error_message=str(e)
            )

            raise HTTPException(
                status_code=400,
                detail=format_error_response(
                    error_code="TWITTER_ERROR",
                    message="推文发布失败",
                    details=str(e)
                )
            )

        except Exception as e:
            # 其他错误
            await db_manager.update_tweet_log(
                log_id=log_id,
                status="failed",
                error_message=str(e)
            )

            raise HTTPException(
                status_code=500,
                detail=format_error_response(
                    error_code="INTERNAL_ERROR",
                    message="服务器内部错误",
                    details=str(e)
                )
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"推文API处理异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=format_error_response(
                error_code="UNEXPECTED_ERROR",
                message="意外错误",
                details=str(e)
            )
        )


@app.get("/api/logs", response_model=dict)
async def get_logs(limit: int = 50):
    """获取最近的操作日志"""
    try:
        logs = await db_manager.get_recent_logs(limit=limit)
        return format_success_response(
            data={"logs": logs, "total": len(logs)},
            message="日志获取成功"
        )
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=format_error_response(
                error_code="DATABASE_ERROR",
                message="日志获取失败",
                details=str(e)
            )
        )


# 运行服务的函数 (用于独立运行)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )