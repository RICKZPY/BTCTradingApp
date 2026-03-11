#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - 新闻跟踪器
News tracker component for weighted sentiment straddle trading system

该组件负责：
1. 维护新闻历史数据库（SQLite）
2. 识别新增的高分新闻（importance_score >= 7）
3. 防止重复处理同一新闻
"""

import sqlite3
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

from weighted_sentiment_models import WeightedNews


# 配置日志
logger = logging.getLogger(__name__)


class NewsTracker:
    """新闻跟踪器类
    
    使用 SQLite 数据库跟踪已处理的新闻，识别新增的高分新闻。
    数据库设计轻量级，适合资源受限环境。
    """
    
    def __init__(self, db_path: str = "data/weighted_news_history.db"):
        """初始化新闻跟踪器
        
        Args:
            db_path: SQLite 数据库文件路径，默认为 data/weighted_news_history.db
        """
        self.db_path = db_path
        self._ensure_data_directory()
        self._init_database()
        logger.info(f"NewsTracker 初始化完成，数据库路径: {self.db_path}")
    
    def _ensure_data_directory(self) -> None:
        """确保数据目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self) -> None:
        """初始化数据库表和索引
        
        创建新闻历史表，包含以下字段：
        - news_id: 新闻唯一标识符（主键）
        - timestamp: 新闻时间戳
        - importance_score: 新闻重要性评分
        - processed_at: 处理时间戳
        
        在 news_id 和 timestamp 字段上创建索引以优化查询性能
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建新闻历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_history (
                    news_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    importance_score INTEGER NOT NULL,
                    processed_at TEXT NOT NULL
                )
            """)
            
            # 创建索引以优化查询性能
            # 索引 news_id（主键自动索引）
            # 索引 timestamp 用于时间范围查询
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_timestamp 
                ON news_history(timestamp)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("数据库表和索引创建成功")
            
        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def identify_new_news(self, news_list: List[WeightedNews]) -> List[WeightedNews]:
        """识别新增的高分新闻
        
        筛选条件：
        1. 新闻未被处理过（news_id 不在数据库中）
        2. 重要性评分 >= 7
        
        Args:
            news_list: 新闻列表
        
        Returns:
            符合条件的新闻列表（未处理 AND 评分 >= 7）
        
        Preconditions:
            - news_list 是有效的 WeightedNews 对象列表
            - 数据库连接已建立
        
        Postconditions:
            - 返回列表仅包含未处理过的新闻
            - 返回列表中所有新闻的 importance_score >= 7
            - 不修改输入参数
            - 数据库状态不变（仅读取）
        """
        if not news_list:
            logger.info("新闻列表为空，无需筛选")
            return []
        
        filtered_news = []
        
        try:
            # 在异步环境中运行同步数据库操作
            loop = asyncio.get_event_loop()
            
            for news in news_list:
                # 检查新闻是否已处理
                is_processed = await loop.run_in_executor(
                    None, 
                    self._is_news_processed_sync, 
                    news.news_id
                )
                
                # 检查新闻是否满足评分阈值
                is_high_score = news.importance_score >= 7
                
                # 只保留未处理且高分的新闻
                if not is_processed and is_high_score:
                    filtered_news.append(news)
                    logger.debug(
                        f"识别到新的高分新闻: {news.news_id}, "
                        f"评分: {news.importance_score}"
                    )
            
            logger.info(
                f"从 {len(news_list)} 条新闻中识别出 {len(filtered_news)} 条新的高分新闻"
            )
            
            return filtered_news
            
        except Exception as e:
            logger.error(f"识别新闻时发生错误: {e}")
            # 发生错误时返回空列表，避免中断服务
            return []
    
    def _is_news_processed_sync(self, news_id: str) -> bool:
        """检查新闻是否已处理（同步版本）
        
        Args:
            news_id: 新闻唯一标识符
        
        Returns:
            True 如果新闻已处理，False 否则
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT 1 FROM news_history WHERE news_id = ? LIMIT 1",
                (news_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except sqlite3.Error as e:
            logger.error(f"查询新闻处理状态失败: {e}")
            # 发生错误时假设未处理，避免丢失新闻
            return False
    
    async def is_news_processed(self, news_id: str) -> bool:
        """检查新闻是否已处理（异步版本）
        
        Args:
            news_id: 新闻唯一标识符
        
        Returns:
            True 如果新闻已处理，False 否则
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._is_news_processed_sync, 
            news_id
        )
    
    async def update_history(self, news_list: List[WeightedNews]) -> None:
        """更新新闻历史记录
        
        将新闻的 news_id、timestamp 和 importance_score 保存到数据库。
        使用事务确保数据一致性。
        
        Args:
            news_list: 要保存的新闻列表
        
        Preconditions:
            - news_list 是有效的 WeightedNews 对象列表
            - 数据库连接已建立
        
        Postconditions:
            - 所有新闻的 news_id 和 timestamp 已保存到数据库
            - 数据库事务已提交
            - 不抛出未捕获的异常（错误被记录但不中断服务）
        """
        if not news_list:
            logger.info("新闻列表为空，无需更新历史")
            return
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                self._update_history_sync, 
                news_list
            )
            
            logger.info(f"成功更新 {len(news_list)} 条新闻的历史记录")
            
        except Exception as e:
            logger.error(f"更新新闻历史时发生错误: {e}")
            # 不抛出异常，避免中断服务
    
    def _update_history_sync(self, news_list: List[WeightedNews]) -> None:
        """更新新闻历史记录（同步版本）
        
        Args:
            news_list: 要保存的新闻列表
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 使用事务确保数据一致性
            processed_at = datetime.now().isoformat()
            
            for news in news_list:
                # 使用 INSERT OR IGNORE 避免重复插入
                cursor.execute("""
                    INSERT OR IGNORE INTO news_history 
                    (news_id, timestamp, importance_score, processed_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    news.news_id,
                    news.timestamp.isoformat(),
                    news.importance_score,
                    processed_at
                ))
            
            conn.commit()
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库更新失败: {e}")
            raise
            
        finally:
            if conn:
                conn.close()
    
    def get_history_count(self) -> int:
        """获取历史记录总数
        
        Returns:
            数据库中的新闻记录总数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM news_history")
            count = cursor.fetchone()[0]
            
            conn.close()
            
            return count
            
        except sqlite3.Error as e:
            logger.error(f"查询历史记录数量失败: {e}")
            return 0
    
    def clear_history(self) -> None:
        """清空历史记录（仅用于测试）
        
        警告：此操作会删除所有历史数据，仅应在测试环境中使用
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM news_history")
            conn.commit()
            conn.close()
            
            logger.warning("历史记录已清空")
            
        except sqlite3.Error as e:
            logger.error(f"清空历史记录失败: {e}")
            raise


# 示例使用
async def main():
    """示例：使用 NewsTracker"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建跟踪器
    tracker = NewsTracker()
    
    # 创建测试新闻
    news_list = [
        WeightedNews(
            news_id="news_001",
            content="Major BTC announcement",
            sentiment="positive",
            importance_score=9,
            timestamp=datetime.now()
        ),
        WeightedNews(
            news_id="news_002",
            content="Minor update",
            sentiment="neutral",
            importance_score=5,
            timestamp=datetime.now()
        ),
        WeightedNews(
            news_id="news_003",
            content="Important market change",
            sentiment="negative",
            importance_score=8,
            timestamp=datetime.now()
        )
    ]
    
    # 识别新的高分新闻
    new_high_score = await tracker.identify_new_news(news_list)
    print(f"\n识别到 {len(new_high_score)} 条新的高分新闻:")
    for news in new_high_score:
        print(f"  - {news.news_id}: 评分 {news.importance_score}")
    
    # 更新历史
    await tracker.update_history(news_list)
    
    # 再次检查（应该没有新新闻）
    new_high_score = await tracker.identify_new_news(news_list)
    print(f"\n再次检查，识别到 {len(new_high_score)} 条新的高分新闻")
    
    # 显示历史记录数量
    count = tracker.get_history_count()
    print(f"\n历史记录总数: {count}")


if __name__ == "__main__":
    asyncio.run(main())
