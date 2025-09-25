# 工具函数
import logging
import sys
from datetime import datetime


def setup_logging(log_level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/app.log', encoding='utf-8')
        ]
    )


def format_error_response(error_code: str, message: str, details: str = None) -> dict:
    """格式化错误响应"""
    return {
        "success": False,
        "error_code": error_code,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }


def format_success_response(data: dict, message: str = "操作成功") -> dict:
    """格式化成功响应"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }