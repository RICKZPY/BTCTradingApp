#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - 状态查询 API
Simple status query API for weighted sentiment trading

这是一个轻量级的 HTTP API，用于查询系统状态。
适合资源受限环境。

使用方法：
    python weighted_sentiment_status_api.py

API 端点：
    GET /api/status - 查询系统状态
    GET /api/history - 查询新闻历史统计
    GET /api/trades - 查询最近的交易记录
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from aiohttp import web

from weighted_sentiment_news_tracker import NewsTracker


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StatusAPI:
    """状态查询 API"""
    
    def __init__(self, port=5003):
        """初始化 API
        
        Args:
            port: HTTP 服务器端口，默认 5003
        """
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
        # 初始化组件
        self.news_tracker = NewsTracker()
        self.log_dir = Path(__file__).parent / "logs"
    
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/history', self.handle_history)
        self.app.router.add_get('/api/trades', self.handle_trades)
        self.app.router.add_get('/', self.handle_root)
    
    async def handle_root(self, request):
        """处理根路径请求"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>加权情绪跨式期权交易 - 状态 API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
                code { background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>加权情绪跨式期权交易 - 状态 API</h1>
            <p>轻量级状态查询 API，适合资源受限环境</p>
            
            <h2>可用端点：</h2>
            
            <div class="endpoint">
                <h3>GET /api/status</h3>
                <p>查询系统状态</p>
                <p><a href="/api/status">查看</a></p>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/history</h3>
                <p>查询新闻历史统计</p>
                <p><a href="/api/history">查看</a></p>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/trades</h3>
                <p>查询最近的交易记录（最多10条）</p>
                <p><a href="/api/trades">查看</a></p>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def handle_status(self, request):
        """处理状态查询请求"""
        try:
            # 读取最后执行时间
            cron_log = self.log_dir / "weighted_sentiment_cron.log"
            last_run = "未知"
            
            if cron_log.exists():
                # 读取最后几行日志
                with open(cron_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines[-50:]):  # 检查最后50行
                        if "执行时间:" in line:
                            # 提取时间戳
                            parts = line.split("执行时间:")
                            if len(parts) > 1:
                                last_run = parts[1].strip()
                            break
            
            # 获取历史统计
            total_news = self.news_tracker.get_history_count()
            
            status = {
                "service": "weighted-sentiment-straddle-trading",
                "status": "running",
                "last_run": last_run,
                "total_news_processed": total_news,
                "timestamp": datetime.now().isoformat()
            }
            
            return web.json_response(status)
        
        except Exception as e:
            logger.error(f"处理状态查询时发生错误: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    async def handle_history(self, request):
        """处理历史统计查询请求"""
        try:
            total_news = self.news_tracker.get_history_count()
            
            history = {
                "total_news_processed": total_news,
                "timestamp": datetime.now().isoformat()
            }
            
            return web.json_response(history)
        
        except Exception as e:
            logger.error(f"处理历史查询时发生错误: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    async def handle_trades(self, request):
        """处理交易记录查询请求"""
        try:
            trade_log = self.log_dir / "weighted_sentiment_trades.log"
            
            if not trade_log.exists():
                return web.json_response({
                    "trades": [],
                    "message": "暂无交易记录"
                })
            
            # 读取最后的交易记录
            with open(trade_log, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单解析交易记录（按分隔符分割）
            trade_entries = content.split('='*80)
            
            # 获取最后10条记录
            recent_trades = []
            for entry in reversed(trade_entries[-11:]):  # 最后11个块（包括最后的空块）
                entry = entry.strip()
                if not entry:
                    continue
                
                # 提取关键信息
                trade_info = {}
                for line in entry.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        trade_info[key.strip()] = value.strip()
                
                if trade_info:
                    recent_trades.append(trade_info)
                
                if len(recent_trades) >= 10:
                    break
            
            return web.json_response({
                "trades": recent_trades,
                "count": len(recent_trades),
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"处理交易查询时发生错误: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    def run(self):
        """运行 API 服务器"""
        logger.info(f"启动状态查询 API，端口: {self.port}")
        logger.info(f"访问 http://localhost:{self.port}/ 查看可用端点")
        web.run_app(self.app, host='0.0.0.0', port=self.port)


def main():
    """主函数"""
    api = StatusAPI(port=5003)
    api.run()


if __name__ == "__main__":
    main()
