#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - Cron Job 脚本
Lightweight cron job for weighted sentiment straddle trading

这是一个轻量级脚本，设计用于通过 cron 定期执行（每小时一次）。
适合资源受限的测试环境。

使用方法：
    python weighted_sentiment_cron.py

Cron 配置示例：
    0 * * * * cd /path/to/BTCOptionsTrading/backend && python weighted_sentiment_cron.py >> logs/weighted_sentiment_cron.log 2>&1
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from weighted_sentiment_api_client import NewsAPIClient
from weighted_sentiment_news_tracker import NewsTracker
from weighted_sentiment_models import WeightedNews, StraddleTradeResult


# 配置日志
def setup_logging():
    """配置日志系统"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "weighted_sentiment.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


logger = setup_logging()


class SimplifiedStraddleExecutor:
    """简化版跨式期权执行器
    
    注意：这是一个简化实现，用于演示工作流程。
    实际交易功能需要完整的 Deribit 集成。
    """
    
    def __init__(self):
        """初始化执行器"""
        self.api_key = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_KEY')
        self.api_secret = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            logger.warning(
                "未配置 Deribit 凭证。请设置环境变量：\n"
                "  WEIGHTED_SENTIMENT_DERIBIT_API_KEY\n"
                "  WEIGHTED_SENTIMENT_DERIBIT_API_SECRET"
            )
    
    async def execute_straddle(self, news: WeightedNews) -> StraddleTradeResult:
        """执行跨式期权交易（简化版）
        
        Args:
            news: 触发交易的新闻
        
        Returns:
            交易结果
        """
        logger.info(f"模拟执行跨式交易，触发新闻: {news.news_id}")
        
        # 简化实现：记录交易意图但不实际执行
        # 在生产环境中，这里应该调用 Deribit API
        
        if not self.api_key or not self.api_secret:
            return StraddleTradeResult(
                success=False,
                news_id=news.news_id,
                trade_time=datetime.now(),
                spot_price=0.0,
                call_option=None,
                put_option=None,
                total_cost=0.0,
                error_message="未配置 Deribit 凭证"
            )
        
        # 模拟成功的交易
        logger.info(
            f"[模拟] 为新闻 {news.news_id} 执行跨式交易\n"
            f"  内容: {news.content[:60]}...\n"
            f"  情绪: {news.sentiment}\n"
            f"  评分: {news.importance_score}/10"
        )
        
        return StraddleTradeResult(
            success=False,
            news_id=news.news_id,
            trade_time=datetime.now(),
            spot_price=0.0,
            call_option=None,
            put_option=None,
            total_cost=0.0,
            error_message="简化实现 - 未实际执行交易"
        )


class SimplifiedTradeLogger:
    """简化版交易日志记录器
    
    将交易记录写入日志文件，而不是数据库。
    适合资源受限环境。
    """
    
    def __init__(self):
        """初始化日志记录器"""
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.trade_log_file = self.log_dir / "weighted_sentiment_trades.log"
    
    async def log_trade(self, news: WeightedNews, result: StraddleTradeResult):
        """记录交易
        
        Args:
            news: 触发交易的新闻
            result: 交易结果
        """
        log_entry = (
            f"\n{'='*80}\n"
            f"交易时间: {result.trade_time.isoformat()}\n"
            f"新闻 ID: {news.news_id}\n"
            f"新闻内容: {news.content}\n"
            f"情绪: {news.sentiment}\n"
            f"重要性评分: {news.importance_score}/10\n"
            f"交易成功: {result.success}\n"
        )
        
        if result.success:
            log_entry += (
                f"现货价格: ${result.spot_price:.2f}\n"
                f"总成本: ${result.total_cost:.2f}\n"
            )
        else:
            log_entry += f"错误信息: {result.error_message}\n"
        
        log_entry += f"{'='*80}\n"
        
        # 写入文件
        with open(self.trade_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        logger.info(f"交易记录已保存: {news.news_id}")


async def main():
    """主函数：执行每小时检查和交易流程"""
    logger.info("="*80)
    logger.info("加权情绪跨式期权交易 - Cron Job 开始执行")
    logger.info(f"执行时间: {datetime.now().isoformat()}")
    logger.info("="*80)
    
    try:
        # 1. 初始化组件
        logger.info("初始化组件...")
        api_client = NewsAPIClient()
        news_tracker = NewsTracker()
        executor = SimplifiedStraddleExecutor()
        trade_logger = SimplifiedTradeLogger()
        
        # 2. 获取新闻数据
        logger.info("获取新闻数据...")
        news_list = await api_client.fetch_weighted_news()
        logger.info(f"获取到 {len(news_list)} 条新闻")
        
        if not news_list:
            logger.info("没有新闻数据，结束执行")
            return
        
        # 3. 识别新的高分新闻
        logger.info("识别新的高分新闻（评分 >= 7）...")
        new_high_score_news = await news_tracker.identify_new_news(news_list)
        logger.info(f"识别到 {len(new_high_score_news)} 条新的高分新闻")
        
        if not new_high_score_news:
            logger.info("没有新的高分新闻，结束执行")
            # 仍然更新历史，标记所有新闻为已处理
            await news_tracker.update_history(news_list)
            return
        
        # 4. 对每条高分新闻执行交易
        logger.info("开始执行交易...")
        for news in new_high_score_news:
            logger.info(f"\n处理新闻: {news.news_id}")
            logger.info(f"  内容: {news.content[:80]}...")
            logger.info(f"  评分: {news.importance_score}/10")
            
            try:
                # 执行跨式交易
                result = await executor.execute_straddle(news)
                
                # 记录交易
                await trade_logger.log_trade(news, result)
                
                if result.success:
                    logger.info(f"  ✓ 交易成功")
                else:
                    logger.warning(f"  ✗ 交易失败: {result.error_message}")
            
            except Exception as e:
                logger.error(f"  ✗ 处理新闻时发生错误: {e}", exc_info=True)
        
        # 5. 更新新闻历史
        logger.info("\n更新新闻历史...")
        await news_tracker.update_history(news_list)
        logger.info("新闻历史更新完成")
        
        # 6. 显示统计信息
        total_history = news_tracker.get_history_count()
        logger.info(f"\n统计信息:")
        logger.info(f"  历史新闻总数: {total_history}")
        logger.info(f"  本次处理新闻: {len(news_list)}")
        logger.info(f"  本次高分新闻: {len(new_high_score_news)}")
        
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        logger.info("="*80)
        logger.info("Cron Job 执行完成")
        logger.info("="*80)


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
