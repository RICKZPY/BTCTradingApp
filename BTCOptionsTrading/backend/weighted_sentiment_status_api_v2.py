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
import aiohttp
import json
import logging
import sqlite3
from datetime import datetime, timezone
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
        self.pnl_file = Path(__file__).parent / "data" / "pnl_history.json"
    
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
                    elif key == '入场价(BTC)':
                        # 区分看涨/看跌（看涨期权行在前）
                        if '看涨合约' in position and '看跌合约' not in position:
                            position['call_entry_btc'] = value
                        else:
                            position['put_entry_btc'] = value
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
            pnl_data = self._load_pnl()
            
            for pos in positions:
                is_virtual = pos.get('虚拟交易', False)
                trade_time = pos.get('交易时间', '未知')
                call_inst = pos.get('看涨合约', '')
                
                # 查找 PnL（用 trade_time[:16] + call_instrument 匹配）
                pnl_key = f"{trade_time[:16]}_{call_inst}"
                pnl = pnl_data.get(pnl_key, {})
                
                if pnl:
                    total_pnl = pnl.get('total_pnl_usd', 0)
                    pnl_pct = pnl.get('pnl_pct', 0)
                    pnl_sign = "+" if total_pnl >= 0 else ""
                    pnl_str = f"{pnl_sign}{total_pnl:.2f} USD ({pnl_sign}{pnl_pct:.1f}%)"
                    pnl_updated = pnl.get('updated_at', '')
                else:
                    pnl_str = "待更新（运行 pnl_updater.py）"
                    pnl_updated = ""
                
                simplified = {
                    "📅 时间": trade_time[:16],
                    "🔮 类型": "虚拟交易（主网行情）" if is_virtual else "真实交易",
                    "📰 新闻": pos.get('新闻内容', '未知')[:100] + ('...' if len(pos.get('新闻内容', '')) > 100 else ''),
                    "😊 情绪": pos.get('情绪', '未知'),
                    "⭐ 评分": pos.get('评分', '未知'),
                    "💰 现货": pos.get('现货价格', '未知'),
                    "📊 IV": pos.get('平均IV', '未知'),
                    "📈 看涨": self._simplify_instrument(call_inst),
                    "📉 看跌": self._simplify_instrument(pos.get('看跌合约', '未知')),
                    "💵 成本": pos.get('总成本', '未知'),
                    "📊 PnL": pnl_str,
                }
                if pnl_updated:
                    simplified["🕐 PnL更新"] = pnl_updated
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
    
    def _load_pnl(self) -> dict:
        """加载 PnL 数据"""
        if not self.pnl_file.exists():
            return {}
        try:
            return json.loads(self.pnl_file.read_text(encoding='utf-8'))
        except Exception:
            return {}

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
    
    async def _fetch_dvol_history(self, start_ts: int, end_ts: int) -> list:
        """从 Deribit 主网拉取 BTC-DVOL 历史数据（小时级别）"""
        try:
            url = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
            params = {
                "currency": "BTC",
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "resolution": "3600"  # 1小时
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    if 'result' in data and 'data' in data['result']:
                        # 每条: [timestamp_ms, open, high, low, close]
                        # DVOL 直接是百分比形式（53.06 = 53.06%），无需换算
                        return [
                            {
                                "ts": row[0],
                                "dvol": round(row[4], 2)  # close值，已是百分比
                            }
                            for row in data['result']['data']
                        ]
        except Exception as e:
            logger.warning(f"获取 DVOL 历史数据失败: {e}")
        return []

    async def handle_iv_history(self, request):
        """处理IV历史数据查询请求，附加 DVOL 市场背景数据"""
        try:
            positions = self._parse_trade_log()

            # 提取交易 IV 历史
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
                    except Exception:
                        pass

            # 计算 DVOL 查询时间范围（覆盖所有交易时间，前后各扩展 24 小时）
            dvol_data = []
            if iv_history:
                try:
                    times = [datetime.fromisoformat(p['时间']) for p in iv_history]
                    start_dt = min(times)
                    end_dt = max(times)
                    # 前后各扩展 24 小时，让 DVOL 曲线有上下文
                    start_ts = int((start_dt.timestamp() - 86400) * 1000)
                    end_ts = int((end_dt.timestamp() + 86400) * 1000)
                    dvol_data = await self._fetch_dvol_history(start_ts, end_ts)
                except Exception as e:
                    logger.warning(f"计算 DVOL 时间范围失败: {e}")

            return web.json_response(
                {
                    "数据": iv_history,
                    "数量": len(iv_history),
                    "DVOL": dvol_data
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
        """处理IV图表页面请求，含 DVOL 市场背景曲线"""
        html = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            "<meta charset=\"UTF-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "<title>IV 历史图表</title>\n"
            "<script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js\"></script>\n"
            "<script src=\"https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js\"></script>\n"
            "<style>\n"
            "body{font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5}\n"
            ".container{max-width:1200px;margin:0 auto;background:white;padding:20px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.1)}\n"
            "h1{color:#333;font-size:24px;margin-bottom:20px}\n"
            ".chart-container{position:relative;height:460px;margin-bottom:30px}\n"
            ".stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}\n"
            ".stat-card{background:#f8f9fa;padding:12px;border-radius:8px;border-left:4px solid #007AFF}\n"
            ".stat-card.dvol{border-left-color:#34C759}\n"
            ".stat-label{font-size:11px;color:#666;margin-bottom:4px}\n"
            ".stat-value{font-size:22px;font-weight:bold;color:#333}\n"
            ".legend-note{font-size:12px;color:#888;margin-bottom:16px;display:flex;gap:16px;flex-wrap:wrap}\n"
            ".dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px;vertical-align:middle}\n"
            ".loading{text-align:center;padding:40px;color:#666}\n"
            ".back-link{display:inline-block;margin-bottom:20px;color:#007AFF;text-decoration:none}\n"
            "</style>\n"
            "</head>\n"
            "<body>\n"
            "<div class=\"container\">\n"
            "<a href=\"/\" class=\"back-link\">← 返回首页</a>\n"
            "<h1>📊 隐含波动率（IV）历史趋势</h1>\n"
            "<div class=\"stats\">\n"
            "  <div class=\"stat-card\"><div class=\"stat-label\">最新交易 IV</div><div class=\"stat-value\" id=\"current-iv\">--</div></div>\n"
            "  <div class=\"stat-card\"><div class=\"stat-label\">平均交易 IV</div><div class=\"stat-value\" id=\"avg-iv\">--</div></div>\n"
            "  <div class=\"stat-card\"><div class=\"stat-label\">最高交易 IV</div><div class=\"stat-value\" id=\"max-iv\">--</div></div>\n"
            "  <div class=\"stat-card\"><div class=\"stat-label\">最低交易 IV</div><div class=\"stat-value\" id=\"min-iv\">--</div></div>\n"
            "  <div class=\"stat-card dvol\"><div class=\"stat-label\">当前 DVOL（市场）</div><div class=\"stat-value\" id=\"current-dvol\">--</div></div>\n"
            "</div>\n"
            "<div class=\"legend-note\">\n"
            "  <span><span class=\"dot\" style=\"background:#007AFF\"></span>交易 IV（蓝=真实，灰=虚拟）</span>\n"
            "  <span><span class=\"dot\" style=\"background:#34C759\"></span>BTC-DVOL 市场整体 30日IV</span>\n"
            "  <span><span class=\"dot\" style=\"background:#FF3B30\"></span>交易成本</span>\n"
            "</div>\n"
            "<div class=\"chart-container\"><canvas id=\"ivChart\"></canvas></div>\n"
            "<div id=\"loading\" class=\"loading\">加载中...</div>\n"
            "</div>\n"
            "<script>\n"
            "async function loadIVData(){\n"
            "  try{\n"
            "    const r=await fetch('/api/iv-history');\n"
            "    const data=await r.json();\n"
            "    const hasT=data.数据&&data.数据.length>0;\n"
            "    const hasD=data.DVOL&&data.DVOL.length>0;\n"
            "    if(!hasT&&!hasD){document.getElementById('loading').innerHTML='暂无数据';return;}\n"
            "    document.getElementById('loading').style.display='none';\n"
            "    const tradePoints=hasT?data.数据.map(item=>({x:new Date(item.时间).getTime(),y:item.IV,v:item.虚拟,n:item.新闻,c:item.成本})):[];\n"
            "    const ptColors=tradePoints.map(p=>p.v?'rgba(150,150,150,0.85)':\'rgba(0,122,255,0.9)\');\n"
            "    const ptRadii=tradePoints.map(p=>p.v?5:7);\n"
            "    const dvolPoints=hasD?data.DVOL.map(d=>({x:d.ts,y:d.dvol})):[];\n"
            "    const costPoints=hasT?data.数据.map(item=>({x:new Date(item.时间).getTime(),y:parseFloat(item.成本.replace('$','').replace(',',''))||null})):[];\n"
            "    if(hasT){\n"
            "      const iv=tradePoints.map(p=>p.y);\n"
            "      document.getElementById('current-iv').textContent=iv[iv.length-1].toFixed(1)+'%';\n"
            "      document.getElementById('avg-iv').textContent=(iv.reduce((a,b)=>a+b,0)/iv.length).toFixed(1)+'%';\n"
            "      document.getElementById('max-iv').textContent=Math.max(...iv).toFixed(1)+'%';\n"
            "      document.getElementById('min-iv').textContent=Math.min(...iv).toFixed(1)+'%';\n"
            "    }\n"
            "    if(hasD){document.getElementById('current-dvol').textContent=dvolPoints[dvolPoints.length-1].y.toFixed(1)+'%';}\n"
            "    const ctx=document.getElementById('ivChart').getContext('2d');\n"
            "    new Chart(ctx,{type:'line',data:{datasets:[\n"
            "      {label:'BTC-DVOL 市场IV(%)',data:dvolPoints,borderColor:'#34C759',backgroundColor:'rgba(52,199,89,0.06)',borderWidth:1.5,pointRadius:0,tension:0.3,fill:false,yAxisID:'y',order:3},\n"
            "      {label:'交易 IV(%)',data:tradePoints,borderColor:'rgba(0,122,255,0.4)',borderWidth:1,borderDash:[4,4],pointBackgroundColor:ptColors,pointRadius:ptRadii,pointHoverRadius:9,showLine:true,tension:0,fill:false,yAxisID:'y',order:1},\n"
            "      {label:'交易成本($)',data:costPoints,borderColor:'#FF3B30',backgroundColor:'rgba(255,59,48,0.08)',borderWidth:1.5,pointRadius:4,tension:0.3,fill:true,yAxisID:'y1',order:2}\n"
            "    ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},\n"
            "    plugins:{legend:{display:true,position:'top'},tooltip:{callbacks:{afterBody:function(items){\n"
            "      const ti=items.find(i=>i.dataset.label==='交易 IV(%)');\n"
            "      if(ti){const p=tradePoints[ti.dataIndex];if(p)return[(p.v?'🔮 虚拟':\'✅ 真实\')+' | '+p.n];}\n"
            "      return[];\n"
            "    }}}},\n"
            "    scales:{x:{type:'time',time:{tooltipFormat:'MM-dd HH:mm',displayFormats:{hour:'MM-dd HH:mm',day:'MM-dd'}}},\n"
            "    y:{type:'linear',position:'left',title:{display:true,text:'IV(%)'}},\n"
            "    y1:{type:'linear',position:'right',title:{display:true,text:'成本($)'},grid:{drawOnChartArea:false}}}\n"
            "    }});\n"
            "  }catch(e){console.error(e);document.getElementById('loading').innerHTML='加载失败: '+e.message;}\n"
            "}\n"
            "loadIVData();setInterval(loadIVData,60000);\n"
            "</script></body></html>"
        )
        return web.Response(text=html, content_type='text/html', charset='utf-8')

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
