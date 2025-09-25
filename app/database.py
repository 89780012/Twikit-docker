# 异步数据库管理
import aiosqlite
import asyncio
import os
from datetime import datetime
from typing import Optional, List
from .models import TweetLog


class DatabaseManager:
    """异步SQLite数据库管理器"""

    def __init__(self, database_path: str = "data/app.db"):
        self.database_path = database_path
        self._connection = None

    async def init_database(self):
        """初始化数据库表结构"""
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tweet_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def log_tweet(self, text: str, tweet_id: Optional[str] = None,
                       status: str = "pending", error_message: Optional[str] = None) -> int:
        """记录推文日志"""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute("""
                INSERT INTO tweet_logs (tweet_id, text, status, error_message)
                VALUES (?, ?, ?, ?)
            """, (tweet_id, text, status, error_message))

            await db.commit()
            return cursor.lastrowid

    async def update_tweet_log(self, log_id: int, tweet_id: Optional[str] = None,
                              status: Optional[str] = None, retry_count: Optional[int] = None,
                              error_message: Optional[str] = None):
        """更新推文日志"""
        updates = []
        params = []

        if tweet_id is not None:
            updates.append("tweet_id = ?")
            params.append(tweet_id)

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if retry_count is not None:
            updates.append("retry_count = ?")
            params.append(retry_count)

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(log_id)

        if updates:
            query = f"UPDATE tweet_logs SET {', '.join(updates)} WHERE id = ?"
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(query, params)
                await db.commit()

    async def get_recent_logs(self, limit: int = 100) -> List[dict]:
        """获取最近的日志记录"""
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM tweet_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def save_config(self, key: str, value: str):
        """保存配置项"""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO app_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))

            await db.commit()

    async def get_config(self, key: str) -> Optional[str]:
        """获取配置项"""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute("""
                SELECT value FROM app_config WHERE key = ?
            """, (key,))

            row = await cursor.fetchone()
            return row[0] if row else None


# 全局数据库实例
db_manager = DatabaseManager()