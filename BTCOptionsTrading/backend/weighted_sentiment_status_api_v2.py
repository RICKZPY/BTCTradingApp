#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - 移动端友好状态 API
Mobile-friendly status API for weighted sentiment trading

优化特性：
1. UTF-8 编码，解决中文乱码问题
2. 精简持仓信息，只显示关键数据
3. 关联新闻和仓位，显示触发交易的新闻内容
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from aiohttp import web
from typing import List, Dict, Optional

from weighted_sentiment_news_tracker import NewsTracker


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MobileFriendlyStatusAPI:
    """移动端友好的状态查询 API"""
    
    def __init__(self, port=5004):
        """初始化 API
        
        Args:
            port: HTTP 服务器端口，默认 5004
        """
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
        # 初始化组件
        self.news_tracker = NewsTracker()
        self.log_dir = Path(__file__).parent / "logs"
        self.db_path = Path(__file__).parent / "data" / "weighted_news_history.db"
    
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/positions', self.handle_positions)
        self.app.router.add_get('/api/iv-history', self.handle_iv_history)
        self.app.router.add_get('/iv-chart', self.handle_iv_chart)
        self.app.router.add_get('/', self.handle_root)
    
    async def handle_root(self, request):
        """处理根路径请求"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>加权情绪交易状态</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { color: #333; font-size: 24px; }
                .endpoint { 
                    background: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .endpoint h3 { margin-top: 0; color: #007AFF; }
                a { color: #007AFF; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 加权情绪交易状态</h1>
                <p>移动端优化版本</p>
                
                <div class="endpoint">
                    <h3>📈 系统状态</h3>
                    <p>查看系统运行状态和统计信息</p>
                    <p><a href="/api/status">查看状态 →</a></p>
                </div>
                
                <div class="endpoint">
                    <h3>💼 持仓信息</h3>
                    <p>查看当前持仓及关联的新闻</p>
                    <p><a href="/api/positions">查看持仓 →</a></p>
                </div>
                
                <div class="endpoint">
                    <h3>📊 IV 历史图表</h3>
                    <p>查看隐含波动率历史变化趋势</p>
                    <p><a href="/iv-chart">查看图表 →</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        return web.Response(
            text=html,
            content_type='text/html',
            charset='utf-8'
        )
    
    def _parse_trade_log(self) -> List[Dict]:
        """解析交易日志，提取持仓和关联新闻"""
        trade_log = self.log_dir / "weighted_sentiment_trades.log"
        
        if not trade_log.exists():
            return []
        
        positions = []
        
        try:
            with open(trade_log, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按分隔符分割交易记录
            trade_entries = content.split('='*80)
            
            for entry in trade_entries:
                entry = entry.strip()
                if not entry or '交易成功: True' not in entry:
                    continue
                
                # 解析交易信息
                position = {}
                lines = entry.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == '交易时间':
                        position['交易时间'] = value
                    elif key == '新闻 ID':
                        position['新闻ID'] = value
                    elif key == '新闻内容':
                        position['新闻内容'] = value
                    elif key == '情绪':
                        position['情绪'] = value
                    elif key == '重要性评分':
                        position['评分'] = value
                    elif key == '虚拟交易':
                        position['虚拟交易'] = value == 'True'
                    elif key == '现货价格':
                        position['现货价格'] = value
                    elif key == '看涨期权':
                        position['看涨合约'] = value
                    elif key == '看跌期权':
                        position['看跌合约'] = value
                    elif key == '平均 IV':
                        position['平均IV'] = value
                    elif key == '总成本':
                        position['总成本'] = value                
                if position and '新闻内容' in position:
                    positions.append(position)
            
            # 返回全部记录
            return positions
        
        except Exception as e:
            logger.error(f"解析交易日志失败: {e}")
            return []
    
    async def handle_status(self, request):
        """处理状态查询请求 - 移动端优化"""
        try:
            # 读取最后执行时间
            cron_log = self.log_dir / "weighted_sentiment_cron.log"
            last_run = "未知"
            last_run_status = "未知"
            
            if cron_log.exists():
                with open(cron_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # 查找最后执行时间
                    for line in reversed(lines[-100:]):
                        if "执行时间:" in line:
                            parts = line.split("执行时间:")
                            if len(parts) > 1:
                                last_run = parts[1].strip()
                        
                        if "识别到" in line and "条新的高分新闻" in line:
                            last_run_status = line.strip()
                            break
            
            # 获取历史统计
            total_news = self.news_tracker.get_history_count()
            
            # 获取最近交易数量
            positions = self._parse_trade_log()
            
            status = {
                "服务": "加权情绪跨式交易",
                "状态": "运行中 ✓",
                "最后执行": last_run,
                "执行结果": last_run_status,
                "历史新闻总数": total_news,
                "当前持仓数": len(positions),
                "查询时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return web.json_response(
                status,
                dumps=lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
            )
        
        except Exception as e:
            logger.error(f"处理状态查询时发生错误: {e}")
            return web.json_response(
                {"错误": str(e)},
                status=500,
                dumps=lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
            )
    
    async def handle_positions(self, request):
        """处理持仓查询请求 - 精简版，关联新闻"""
        try:
            positions = self._parse_trade_log()
            
            if not positions:
                return web.json_response(
                    {
                        "持仓": [],
                        "消息": "暂无持仓"
                    },
                    dumps=lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
                )
            
            # 精简持仓信息
            simplified_positions = []
            
            for pos in positions:
                is_virtual = pos.get('虚拟交易', False)
                simplified = {
                    "📅 时间": pos.get('交易时间', '未知')[:16],
                    "🔮 类型": "虚拟交易（主网行情）" if is_virtual else "真实交易",
                    "📰 新闻": pos.get('新闻内容', '未知')[:100] + ('...' if len(pos.get('新闻内容', '')) > 100 else ''),
                    "😊 情绪": pos.get('情绪', '未知'),
                    "⭐ 评分": pos.get('评分', '未知'),
                    "💰 现货": pos.get('现货价格', '未知'),
                    "📊 IV": pos.get('平均IV', '未知'),
                    "📈 看涨": self._simplify_instrument(pos.get('看涨合约', '未知')),
                    "📉 看跌": self._simplify_instrument(pos.get('看跌合约', '未知')),
                    "💵 成本": pos.get('总成本', '未知')
                }
                simplified_positions.append(simplified)
            
            response = {
                "持仓数量": len(simplified_positions),
                "持仓列表": simplified_positions,
                "查询时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return web.json_response(
                response,
                dumps=lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
            )
        
        except Exception as e:
            logger.error(f"处理持仓查询时发生错误: {e}")
            return web.json_response(
                {"错误": str(e)},
                status=500,
                dumps=lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
            )
    
    def _simplify_instrument(self, instrument_name: str) -> str:
        """简化合约名称显示
        
        例如: BTC-28MAR26-95000-C -> 28MAR 95K C
        """
        if not instrument_name or instrument_name == '未知':
            return '未知'
        
        try:
            parts = instrument_name.split('-')
            if len(parts) >= 4:
                date = parts[1][:5]  # 28MAR
                strike = f"{int(parts[2])/1000:.0f}K"  # 95K
                option_type = parts[3]  # C or P
                return f"{date} {strike} {option_type}"
        except:
            pass
        
        return instrument_name
    
    async def handle_iv_history(self, request):
        """处理IV历史数据查询请求"""
        try:
            positions = self._parse_trade_log()
            
            # 提取IV历史数据
            iv_history = []
            for pos in positions:
                iv_str = pos.get('平均IV', '未知')
                if iv_str != '未知' and '%' in iv_str:
                    try:
                        iv_value = float(iv_str.replace('%', ''))
                        iv_history.append({
                            "时间": pos.get('交易时间', '未知'),
                            "IV": iv_value,
                            "成本": pos.get('总成本', '未知'),
                            "新闻": pos.get('新闻内容', '未知')[:50] + '...',
                            "虚拟": pos.get('虚拟交易', False)
                        })
                    except:
                        pass
            
            return web.json_response(
                {
                    "数据": iv_history,
                    "数量": len(iv_history)
                },
                dumps=lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
            )
        
        except Exception as e:
            logger.error(f"处理IV历史查询时发生错误: {e}")
            return web.json_response(
                {"错误": str(e)},
                status=500,
                dumps=lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
            )
    
    async def handle_iv_chart(self, request):
        """处理IV图表页面请求"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>IV 历史图表</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container { 
                    max-width: 1200px; 
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { 
                    color: #333; 
                    font-size: 24px;
                    margin-bottom: 20px;
                }
                .chart-container {
                    position: relative;
                    height: 400px;
                    margin-bottom: 30px;
                }
                .stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }
                .stat-card {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #007AFF;
                }
                .stat-label {
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 5px;
                }
                .stat-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }
                .loading {
                    text-align: center;
                    padding: 40px;
                    color: #666;
                }
                .back-link {
                    display: inline-block;
                    margin-bottom: 20px;
                    color: #007AFF;
                    text-decoration: none;
                }
                .back-link:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-link">← 返回首页</a>
                <h1>📊 隐含波动率（IV）历史趋势</h1>
                
                <div class="stats" id="stats">
                    <div class="stat-card">
                        <div class="stat-label">当前 IV</div>
                        <div class="stat-value" id="current-iv">--</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">平均 IV</div>
                        <div class="stat-value" id="avg-iv">--</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">最高 IV</div>
                        <div class="stat-value" id="max-iv">--</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">最低 IV</div>
                        <div class="stat-value" id="min-iv">--</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="ivChart"></canvas>
                </div>
                
                <div id="loading" class="loading">加载中...</div>
            </div>
            
            <script>
                async function loadIVData() {
                    try {
                        const response = await fetch('/api/iv-history');
                        const data = await response.json();
                        
                        if (!data.数据 || data.数据.length === 0) {
                            document.getElementById('loading').innerHTML = 
                                '暂无 IV 数据。<br>下次交易执行后将显示 IV 历史。';
                            return;
                        }
                        
                        document.getElementById('loading').style.display = 'none';
                        
                        // 提取数据
                        const labels = data.数据.map(item => {
                            const date = new Date(item.时间);
                            return date.toLocaleString('zh-CN', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        });
                        const ivValues = data.数据.map(item => item.IV);
                        const costs = data.数据.map(item => {
                            const cost = item.成本.replace('$', '').replace(',', '');
                            return parseFloat(cost);
                        });
                        
                        // 计算统计数据
                        const currentIV = ivValues[ivValues.length - 1];
                        const avgIV = ivValues.reduce((a, b) => a + b, 0) / ivValues.length;
                        const maxIV = Math.max(...ivValues);
                        const minIV = Math.min(...ivValues);
                        
                        document.getElementById('current-iv').textContent = currentIV.toFixed(1) + '%';
                        document.getElementById('avg-iv').textContent = avgIV.toFixed(1) + '%';
                        document.getElementById('max-iv').textContent = maxIV.toFixed(1) + '%';
                        document.getElementById('min-iv').textContent = minIV.toFixed(1) + '%';
                        
                        // 区分真实/虚拟交易点颜色
                        const pointColors = data.数据.map(item => 
                            item.虚拟 ? 'rgba(150,150,150,0.8)' : 'rgba(0,122,255,0.9)'
                        );
                        const pointRadii = data.数据.map(item => item.虚拟 ? 4 : 5);
                        
                        // 创建图表
                        const ctx = document.getElementById('ivChart').getContext('2d');
                        new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: labels,
                                datasets: [{
                                    label: 'IV (%)',
                                    data: ivValues,
                                    borderColor: '#007AFF',
                                    backgroundColor: 'rgba(0, 122, 255, 0.1)',
                                    pointBackgroundColor: pointColors,
                                    pointRadius: pointRadii,
                                    tension: 0.4,
                                    fill: true,
                                    yAxisID: 'y'
                                }, {
                                    label: '成本 ($)',
                                    data: costs,
                                    borderColor: '#FF3B30',
                                    backgroundColor: 'rgba(255, 59, 48, 0.1)',
                                    tension: 0.4,
                                    fill: true,
                                    yAxisID: 'y1'
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                interaction: {
                                    mode: 'index',
                                    intersect: false,
                                },
                                plugins: {
                                    legend: {
                                        display: true,
                                        position: 'top',
                                    },
                                    tooltip: {
                                        callbacks: {
                                            afterLabel: function(context) {
                                                const index = context.dataIndex;
                                                const item = data.数据[index];
                                                const tag = item.虚拟 ? ' 🔮虚拟' : ' ✅真实';
                                                return tag + ' | 新闻: ' + item.新闻;
                                            }
                                        }
                                    }
                                },
                                scales: {
                                    y: {
                                        type: 'linear',
                                        display: true,
                                        position: 'left',
                                        title: {
                                            display: true,
                                            text: 'IV (%)'
                                        }
                                    },
                                    y1: {
                                        type: 'linear',
                                        display: true,
                                        position: 'right',
                                        title: {
                                            display: true,
                                            text: '成本 ($)'
                                        },
                                        grid: {
                                            drawOnChartArea: false,
                                        }
                                    }
                                }
                            }
                        });
                        
                    } catch (error) {
                        console.error('加载数据失败:', error);
                        document.getElementById('loading').innerHTML = 
                            '加载失败: ' + error.message;
                    }
                }
                
                // 页面加载时获取数据
                loadIVData();
                
                // 每30秒刷新一次
                setInterval(loadIVData, 30000);
            </script>
        </body>
        </html>
        """
        return web.Response(
            text=html,
            content_type='text/html',
            charset='utf-8'
        )
    
    def run(self):
        """运行 API 服务器"""
        logger.info(f"启动移动端友好状态 API，端口: {self.port}")
        logger.info(f"访问 http://0.0.0.0:{self.port}/ 查看状态")
        web.run_app(self.app, host='0.0.0.0', port=self.port)


def main():
    """主函数"""
    api = MobileFriendlyStatusAPI(port=5004)
    api.run()


if __name__ == "__main__":
    main()
