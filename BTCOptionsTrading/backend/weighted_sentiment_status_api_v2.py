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

BASE_DIR = Path(__file__).parent


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
        self.impact_file = Path(__file__).parent / "data" / "news_impact.json"
    
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/positions', self.handle_positions)
        self.app.router.add_get('/positions', self.handle_positions_html)
        self.app.router.add_get('/api/iv-history', self.handle_iv_history)
        self.app.router.add_get('/api/iv-detail', self.handle_iv_detail)
        self.app.router.add_get('/api/news-impact', self.handle_news_impact)
        self.app.router.add_get('/api/news-events', self.handle_news_events)
        self.app.router.add_get('/api/news-events-v2', self.handle_news_events_v2)
        self.app.router.add_post('/webhook/news', self.handle_news_webhook)
        self.app.router.add_post('/webhook/news-v3', self.handle_news_webhook_v3)
        self.app.router.add_post('/vol/open', self.handle_vol_open)
        self.app.router.add_post('/vol/close', self.handle_vol_close)
        self.app.router.add_get('/api/perp-positions', self.handle_perp_positions)
        self.app.router.add_get('/api/perp-price', self.handle_perp_price)
        self.app.router.add_get('/perp', self.handle_perp_page)
        self.app.router.add_get('/iv-chart', self.handle_iv_chart)
        self.app.router.add_get('/iv-detail-chart', self.handle_iv_detail_chart)
        self.app.router.add_get('/news-impact', self.handle_news_impact_page)
        self.app.router.add_get('/vol-account', self.handle_vol_account)
        self.app.router.add_get('/api/vol-account', self.handle_vol_account_api)
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
                    <p><a href="/positions">📱 卡片页面 →</a> &nbsp; <a href="/api/positions">JSON →</a></p>
                </div>
                
                <div class="endpoint">
                    <h3>📊 IV 历史图表</h3>
                    <p>查看隐含波动率历史变化趋势（含 DVOL 市场背景）</p>
                    <p><a href="/iv-chart">查看图表 →</a></p>
                </div>
                
                <div class="endpoint">
                    <h3>🔬 合约 IV 5分钟走势</h3>
                    <p>查看持仓合约的精细 IV 变化（每5分钟采集）</p>
                    <p><a href="/iv-detail-chart">查看走势 →</a></p>
                </div>
                
                <div class="endpoint">
                    <h3>🔍 新闻事后影响验证</h3>
                    <p>追踪每条触发交易的新闻对 BTC 价格的实际影响（T+1h/4h/24h）</p>
                    <p><a href="/news-impact">查看验证 →</a> &nbsp; <a href="/api/news-impact">JSON →</a></p>
                </div>
                
                <div class="endpoint">
                    <h3>⚡ Vol 账户持仓（qCoXRSu6）</h3>
                    <p>新闻驱动永续合约策略 - 正面多头/负面空头，3天平仓</p>
                    <p><a href="/vol-account">查看 Vol 账户 →</a> &nbsp; <a href="/perp">永续合约持仓详情 →</a></p>
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
                    elif key == 'Combo ID':
                        position['combo_id'] = value
                    elif key == '下单数量':
                        try:
                            position['quantity'] = float(value.replace(' BTC', ''))
                        except Exception:
                            pass
                    elif key == '盈亏平衡':
                        position['盈亏平衡'] = value  # 格式: "$65000.00 ~ $68000.00"
                    elif key == '现货价格':
                        position['现货价格'] = value
                    elif key == '看涨期权':
                        position['看涨合约'] = value
                        position['_current_side'] = 'call'
                    elif key == '看跌期权':
                        position['看跌合约'] = value
                        position['_current_side'] = 'put'
                    elif key == '执行价':
                        # 只取看涨期权的执行价（call/put 同执行价）
                        if position.get('_current_side') == 'call' and '执行价' not in position:
                            try:
                                position['执行价'] = float(value.replace('$', '').replace(',', ''))
                            except Exception:
                                pass
                    elif key == '入场价(BTC)':
                        # 区分看涨/看跌（看涨期权行在前）
                        if '看涨合约' in position and '看跌合约' not in position:
                            position['call_entry_btc'] = value
                        else:
                            position['put_entry_btc'] = value
                    elif key == '权利金':
                        # 兼容旧日志（没有入场价字段，用权利金代替）
                        try:
                            btc_val = float(value.replace(' BTC', ''))
                            side = position.get('_current_side')
                            if side == 'call' and 'call_entry_btc' not in position:
                                position['call_entry_btc'] = str(btc_val)
                            elif side == 'put' and 'put_entry_btc' not in position:
                                position['put_entry_btc'] = str(btc_val)
                        except Exception:
                            pass
                    elif key == '平均 IV':
                        position['平均IV'] = value
                    elif key == '总成本':
                        position['总成本'] = value                
                if position and '新闻内容' in position:
                    # 如果没有记录盈亏平衡，用已有数据实时计算
                    if '盈亏平衡' not in position:
                        try:
                            strike = position.get('执行价')
                            call_e = float(position.get('call_entry_btc', 0))
                            put_e = float(position.get('put_entry_btc', 0))
                            spot_str = position.get('现货价格', '0').replace('$', '').replace(',', '')
                            spot = float(spot_str)
                            if strike and call_e and put_e and spot:
                                # 盈亏平衡 = 执行价 ± 总权利金(USD per BTC)
                                # 不乘数量，因为盈亏平衡是价格概念
                                total_prem_usd = (call_e + put_e) * spot
                                be_lower = strike - total_prem_usd
                                be_upper = strike + total_prem_usd
                                position['盈亏平衡'] = f"${be_lower:.2f} ~ ${be_upper:.2f}"
                        except Exception:
                            pass
                    positions.append(position)

            # 只保留 23MAR26 及以后的合约（过滤掉已清理的早期持仓）
            EXCLUDED = ('27MAR26', '20MAR26')
            positions = [
                p for p in positions
                if not any(ex in p.get('看涨合约', '') for ex in EXCLUDED)
            ]
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
                    "📐 盈亏平衡": pos.get('盈亏平衡', '未记录'),
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
    
    def _build_card_html(self, pos: dict, pnl_data: dict) -> str:
        """构建单个持仓卡片 HTML"""
        is_virtual = pos.get('虚拟交易', False)
        trade_time = pos.get('交易时间', '未知')
        call_inst = pos.get('看涨合约', '')
        combo_id = pos.get('combo_id', '')
        be_range = pos.get('盈亏平衡', '')
        news_text = pos.get('新闻内容', '未知')
        sentiment = pos.get('情绪', '未知')
        score = pos.get('评分', '未知')
        spot = pos.get('现货价格', '未知')
        avg_iv = pos.get('平均IV', '未知')
        total_cost = pos.get('总成本', '未知')
        call_simple = self._simplify_instrument(call_inst)
        put_simple = self._simplify_instrument(pos.get('看跌合约', '未知'))

        pnl_key = f"{trade_time[:16]}_{call_inst}"
        pnl = pnl_data.get(pnl_key, {})
        is_settled = pnl.get('settled', False)
        if pnl:
            total_pnl = pnl.get('total_pnl_usd', 0)
            pnl_pct = pnl.get('pnl_pct', 0)
            sign = "+" if total_pnl >= 0 else ""
            pnl_color = "#34C759" if total_pnl >= 0 else "#FF3B30"
            settled_tag = ' <span style="font-size:11px;background:#888;color:white;padding:1px 6px;border-radius:8px;margin-left:4px">已结算</span>' if is_settled else ''
            pnl_html = f'<div class="pnl" style="color:{pnl_color}">📊 PnL: {sign}{total_pnl:.2f} USD ({sign}{pnl_pct:.1f}%){settled_tag}</div>'
        else:
            is_settled = False
            pnl_html = '<div class="pnl" style="color:#aaa">📊 PnL: 待更新</div>'

        badge = '🔮 虚拟' if is_virtual else '✅ 真实'
        badge_color = '#888' if is_virtual else '#007AFF'
        sl = sentiment.lower()
        sentiment_emoji = '📈' if '看涨' in sentiment or 'bullish' in sl else ('📉' if '看跌' in sentiment or 'bearish' in sl else '😐')

        # 生成唯一 card ID 用于图表
        import hashlib
        card_id = hashlib.md5(f"{trade_time[:16]}_{call_inst}".encode()).hexdigest()[:8]
        # 只对未到期合约显示 IV 图
        iv_chart_html = ''
        if call_inst:
            # 解析盈亏平衡数值传给 JS
            be_lower_val, be_upper_val = 0, 0
            if be_range:
                try:
                    parts = be_range.replace('$', '').replace(',', '').split('~')
                    be_lower_val = float(parts[0].strip())
                    be_upper_val = float(parts[1].strip())
                except Exception:
                    pass
            settled_label = ' <span style="font-size:10px;background:#888;color:white;padding:1px 5px;border-radius:6px;margin-left:4px">历史快照</span>' if is_settled else ''
            iv_chart_html = f"""
  <div class="iv-toggle" onclick="toggleIV(this, '{card_id}', '{call_inst}', '{trade_time[:16]}', {be_lower_val}, {be_upper_val})">
    📈 查看 IV + BTC 走势图 ▼{settled_label}
  </div>
  <div id="iv-{card_id}" style="display:none;margin-top:8px">
    <div id="iv-tip-{card_id}" style="font-size:12px;font-weight:600;margin-bottom:4px"></div>
    <div style="font-size:11px;color:#888;margin-bottom:4px">IV 走势</div>
    <div style="position:relative;height:100px"><canvas id="canvas-iv-{card_id}"></canvas></div>
    <div style="font-size:11px;color:#888;margin:8px 0 4px">BTC 价格（虚线=盈亏平衡区间）</div>
    <div style="position:relative;height:120px"><canvas id="canvas-spot-{card_id}"></canvas></div>
    <div id="iv-loading-{card_id}" style="text-align:center;color:#aaa;font-size:12px;padding:10px">加载中...</div>
  </div>"""

        return f"""
<div class="card">
  <div class="card-header">
    <span class="badge" style="background:{badge_color}">{badge}</span>
    <span class="time">🕐 {trade_time[:16]}</span>
  </div>
  <div class="news">📰 {news_text[:120]}{'...' if len(news_text) > 120 else ''}</div>
  <div class="row">
    <span>{sentiment_emoji} {sentiment}</span>
    <span>⭐ 评分: {score}</span>
    <span>💰 现货: {spot}</span>
  </div>
  <div class="row">
    <span>📈 看涨: {call_simple}</span>
    <span>📉 看跌: {put_simple}</span>
    <span>📊 IV: {avg_iv}</span>
  </div>
  <div class="cost">💵 成本: {total_cost}</div>
  {f'<div class="combo-id">🔗 Combo: <a href="https://www.deribit.com/combo/{combo_id}" target="_blank">{combo_id}</a></div>' if combo_id else ''}
  {'' if is_settled else self._build_be_html(be_range, str(pnl.get('spot_price', '')) if pnl else '')}
  {pnl_html}
  {iv_chart_html}
</div>"""

    async def handle_positions_html(self, request):
        """持仓卡片页面 - 最新20条直接展示，历史记录可折叠"""
        try:
            positions = self._parse_trade_log()
            pnl_data = self._load_pnl()

            RECENT_COUNT = 20
            reversed_positions = list(reversed(positions))  # 最新在前
            recent = reversed_positions[:RECENT_COUNT]
            older = reversed_positions[RECENT_COUNT:]

            if not positions:
                recent_html = '<div class="empty">📭 暂无持仓记录</div>'
                older_section = ''
            else:
                recent_html = ''.join(self._build_card_html(p, pnl_data) for p in recent)

                if older:
                    older_cards = ''.join(self._build_card_html(p, pnl_data) for p in older)
                    older_section = f"""
<div class="older-toggle" onclick="toggleOlder(this)">
  📦 展开历史记录（{len(older)} 条）▼
</div>
<div id="older-cards" style="display:none">
  {older_cards}
</div>"""
                else:
                    older_section = ''

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>持仓记录</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:0;padding:16px;background:#f0f2f5}}
.container{{max-width:800px;margin:0 auto}}
h1{{color:#333;font-size:22px;margin-bottom:4px}}
.subtitle{{color:#888;font-size:13px;margin-bottom:16px}}
.back-link{{display:inline-block;margin-bottom:16px;color:#007AFF;text-decoration:none;font-size:14px}}
.card{{background:white;border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.card-header{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.badge{{color:white;font-size:11px;padding:3px 8px;border-radius:10px;font-weight:600}}
.time{{color:#888;font-size:12px}}
.news{{font-size:14px;color:#333;line-height:1.5;margin-bottom:10px;padding:8px;background:#f8f9fa;border-radius:8px;border-left:3px solid #007AFF}}
.row{{display:flex;flex-wrap:wrap;gap:12px;font-size:13px;color:#555;margin-bottom:6px}}
.cost{{font-size:15px;font-weight:600;color:#333;margin-top:8px}}
.combo-id{{font-size:12px;color:#888;margin-top:4px}}
.combo-id a{{color:#007AFF;text-decoration:none}}
.be-range{{font-size:13px;color:#555;margin-top:6px;padding:6px 10px;background:#f8f9fa;border-radius:8px;border-left:3px solid #FF9500}}
.be-lower,.be-upper{{font-weight:700;color:#333}}
.be-note{{font-size:11px;color:#aaa;margin-left:6px}}
.pnl{{font-size:15px;font-weight:700;margin-top:4px}}
.empty{{text-align:center;padding:40px;color:#aaa;font-size:16px}}
.count{{background:#007AFF;color:white;border-radius:12px;padding:2px 10px;font-size:13px;margin-left:8px}}
.formula-box{{background:white;border-radius:12px;padding:14px 16px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06);border-left:4px solid #FF9500}}
.formula-title{{font-size:13px;font-weight:700;color:#FF9500;margin-bottom:10px}}
.formula-row{{margin-bottom:8px;font-size:12px;line-height:1.6}}
.formula-label{{display:inline-block;font-weight:700;color:#333;min-width:110px}}
.formula-expr{{color:#555}}
.formula-note{{display:block;color:#aaa;font-size:11px;margin-left:110px;margin-top:1px}}
.older-toggle{{background:white;border-radius:10px;padding:14px 16px;margin-bottom:14px;
  box-shadow:0 2px 8px rgba(0,0,0,.06);cursor:pointer;color:#007AFF;font-size:14px;
  font-weight:600;text-align:center;border:1.5px dashed #007AFF}}
.older-toggle:hover{{background:#f0f7ff}}
.older-toggle.open{{border-style:solid}}
.iv-toggle{{font-size:12px;color:#007AFF;cursor:pointer;margin-top:8px;padding:4px 0;border-top:1px solid #f0f2f5}}
.iv-toggle:hover{{color:#0056CC}}
</style>
</head>
<body>
<div class="container">
  <a href="/" class="back-link">← 返回首页</a>
  <h1>💼 持仓记录 <span class="count">{len(positions)}</span></h1>
  <div class="subtitle">更新时间: {now_str}（显示最新 {min(RECENT_COUNT, len(positions))} 条）</div>
  <div class="formula-box">
    <div class="formula-title">🎯 主账户交易策略（0366QIa2）</div>
    <div class="formula-row">
      <span class="formula-label">策略一</span>
      <span class="formula-expr">ATM Straddle — 测试新闻打分准确性，每次 8 分新闻触发时买入 ATM Straddle，$10,000 仓位</span>
      <span class="formula-note">触发：评分 ≥ 8 | IV &lt; 55% | IV 趋势向上 | 48h 无重复</span>
    </div>
    <div class="formula-row">
      <span class="formula-label">策略二</span>
      <span class="formula-expr">Calendar Spread — 同一账户，当近远期 IV 差 ≥ 3% 时，卖近期买远期，净成本 $200-500</span>
      <span class="formula-note">触发：近期 IV ≥ 50% 且 近远期 IV 差 ≥ 3%</span>
    </div>
    <div class="formula-row">
      <span class="formula-label">Vol 账户</span>
      <span class="formula-expr">新闻驱动永续合约（qCoXRSu6 + vXkaBDto）— 正面新闻多头，负面新闻空头，$1000/笔，3天平仓</span>
      <span class="formula-note">触发：ATM IV ≥ 55% | <a href="/vol-account" style="color:#007AFF">查看 Vol 账户持仓 →</a></span>
    </div>
  </div>
  <div class="formula-box">
    <div class="formula-title">📐 计算说明</div>
    <div class="formula-row">
      <span class="formula-label">💵 成本</span>
      <span class="formula-expr">= (Call mark_price + Put mark_price) × 0.1 BTC × BTC现货价</span>
      <span class="formula-note">例: (0.019 + 0.019) × 0.1 × $66,500 ≈ $252</span>
    </div>
    <div class="formula-row">
      <span class="formula-label">📊 PnL</span>
      <span class="formula-expr">= (当前 mark_price − 入场 mark_price) × 0.1 BTC × 当前BTC价</span>
      <span class="formula-note">Call PnL + Put PnL，每日 UTC 00:00 / 04:00 / 08:00 / 12:00 / 16:00 / 20:00 更新</span>
    </div>
    <div class="formula-row">
      <span class="formula-label">⚠️ 与Deribit差异</span>
      <span class="formula-expr">Deribit 界面按 1 BTC 面值显示，我们下单 0.1 BTC，故成本约为 Deribit 显示的 1/10</span>
    </div>
  </div>
  {recent_html}
  {older_section}
</div>
<script>
function toggleOlder(el) {{
  const div = document.getElementById('older-cards');
  const hidden = div.style.display === 'none';
  div.style.display = hidden ? 'block' : 'none';
  el.classList.toggle('open', hidden);
  const count = {len(older)};
  el.textContent = hidden
    ? '📦 收起历史记录（' + count + ' 条）▲'
    : '📦 展开历史记录（' + count + ' 条）▼';
}}

const ivCharts = {{}};
async function toggleIV(el, cardId, instrument, tradeTime, beLower, beUpper) {{
  const div = document.getElementById('iv-' + cardId);
  const hidden = div.style.display === 'none';
  div.style.display = hidden ? 'block' : 'none';
  el.textContent = hidden ? '📈 收起 IV 走势图 ▲' : '📈 查看 IV 走势图 ▼';
  if (!hidden || ivCharts[cardId]) return;

  const loading = document.getElementById('iv-loading-' + cardId);
  try {{
    const r = await fetch('/api/iv-detail?instrument=' + encodeURIComponent(instrument) + '&limit=2016');
    const data = await r.json();
    loading.style.display = 'none';
    if (!data.数据 || data.数据.length === 0) {{
      loading.textContent = '暂无 IV 数据';
      loading.style.display = 'block';
      return;
    }}
    // 只显示从下单时间开始的数据
    const tradeTs = new Date(tradeTime).getTime();
    const pts = data.数据.filter(p => p.ts * 1000 >= tradeTs - 300000);
    if (pts.length === 0) {{
      loading.textContent = '下单后暂无 IV 数据';
      loading.style.display = 'block';
      return;
    }}

    const ivData   = pts.map(p => ({{x: p.ts * 1000, y: p.iv}}));
    const spotData = pts.map(p => ({{x: p.ts * 1000, y: p.spot}}));

    // ── IV 图 ──────────────────────────────────────────────
    const ctx1 = document.getElementById('canvas-iv-' + cardId).getContext('2d');
    new Chart(ctx1, {{
      type: 'line',
      data: {{ datasets: [{{
        label: 'IV (%)',
        data: ivData,
        borderColor: '#007AFF',
        backgroundColor: 'rgba(0,122,255,0.06)',
        borderWidth: 1.5, pointRadius: 0, tension: 0.2, fill: true
      }}] }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }},
          tooltip: {{ callbacks: {{ title: i => new Date(i[0].parsed.x).toLocaleString('zh-CN') }} }}
        }},
        scales: {{
          x: {{ type: 'time', time: {{ tooltipFormat: 'MM-dd HH:mm', displayFormats: {{ hour: 'MM-dd HH:mm' }} }},
            ticks: {{ maxTicksLimit: 5, font: {{ size: 10 }} }} }},
          y: {{ title: {{ display: true, text: 'IV(%)', font: {{ size: 10 }} }},
            ticks: {{ font: {{ size: 10 }} }} }}
        }}
      }}
    }});

    // ── BTC 价格图（含盈亏平衡线）──────────────────────────
    const ctx2 = document.getElementById('canvas-spot-' + cardId).getContext('2d');
    const spotMin = Math.min(...spotData.map(p=>p.y));
    const spotMax = Math.max(...spotData.map(p=>p.y));
    const yMin = Math.min(spotMin, beLower) * 0.998;
    const yMax = Math.max(spotMax, beUpper) * 1.002;

    // 判断是否曾进入盈利区间
    const hadProfit = spotData.some(p => p.y < beLower || p.y > beUpper);

    new Chart(ctx2, {{
      type: 'line',
      data: {{ datasets: [
        {{
          label: 'BTC 价格 ($)',
          data: spotData,
          borderColor: hadProfit ? '#34C759' : '#FF9500',
          backgroundColor: 'rgba(0,0,0,0)',
          borderWidth: 1.5, pointRadius: 0, tension: 0.2
        }},
        {{
          label: '上限 $' + beUpper.toLocaleString(),
          data: spotData.map(p => ({{x: p.x, y: beUpper}})),
          borderColor: 'rgba(52,199,89,0.7)',
          borderWidth: 1.5, borderDash: [5,3],
          pointRadius: 0, fill: false
        }},
        {{
          label: '下限 $' + beLower.toLocaleString(),
          data: spotData.map(p => ({{x: p.x, y: beLower}})),
          borderColor: 'rgba(52,199,89,0.7)',
          borderWidth: 1.5, borderDash: [5,3],
          pointRadius: 0, fill: false
        }}
      ] }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: true, position: 'top', labels: {{ font: {{ size: 10 }} }} }},
          tooltip: {{ callbacks: {{ title: i => new Date(i[0].parsed.x).toLocaleString('zh-CN') }} }},
          annotation: hadProfit ? {{}} : {{}}
        }},
        scales: {{
          x: {{ type: 'time', time: {{ tooltipFormat: 'MM-dd HH:mm', displayFormats: {{ hour: 'MM-dd HH:mm' }} }},
            ticks: {{ maxTicksLimit: 5, font: {{ size: 10 }} }} }},
          y: {{ min: yMin, max: yMax,
            title: {{ display: true, text: 'BTC ($)', font: {{ size: 10 }} }},
            ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v.toLocaleString() }} }}
        }}
      }}
    }});

    // 盈利区间提示
    if (hadProfit) {{
      const tip = document.getElementById('iv-tip-' + cardId);
      if (tip) {{ tip.textContent = '✅ 曾进入盈利区间'; tip.style.color = '#34C759'; }}
    }}

    ivCharts[cardId] = true;
  }} catch(e) {{
    loading.textContent = '加载失败: ' + e.message;
    loading.style.display = 'block';
  }}
}}
</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
</script>
</body>
</html>"""
            return web.Response(text=html, content_type='text/html', charset='utf-8')

        except Exception as e:
            logger.error(f"持仓HTML页面错误: {e}")
            return web.Response(text=f"<h1>错误: {e}</h1>", content_type='text/html', charset='utf-8')

    def _load_pnl(self) -> dict:
        """加载 PnL 数据"""
        if not self.pnl_file.exists():
            return {}
        try:
            return json.loads(self.pnl_file.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _build_be_html(self, be_range: str, current_spot: str = '') -> str:
        """构建盈亏平衡点 HTML，并标注当前价格是否在盈利区间"""
        if not be_range:
            return ''
        try:
            # 格式: "$65000.00 ~ $68000.00"
            parts = be_range.replace('$', '').replace(',', '').split('~')
            be_lower = float(parts[0].strip())
            be_upper = float(parts[1].strip())
            # 尝试解析当前价格（来自 PnL 数据）
            in_profit = None
            if current_spot:
                try:
                    spot = float(str(current_spot).replace('$', '').replace(',', ''))
                    in_profit = spot < be_lower or spot > be_upper
                except Exception:
                    pass
            status = ''
            if in_profit is True:
                status = ' <span style="color:#34C759;font-weight:700">✅ 到期可盈利</span>'
            elif in_profit is False:
                status = ' <span style="color:#FF9500;font-weight:700">⏳ 需更大波动</span>'
            return (
                f'<div class="be-range">📐 到期盈亏平衡: '
                f'BTC &lt; <span class="be-lower">${be_lower:,.0f}</span>'
                f' 或 &gt; '
                f'<span class="be-upper">${be_upper:,.0f}</span>'
                f'{status}'
                f'<span class="be-note">（与当前PnL无关，仅指到期时）</span></div>'
            )
        except Exception:
            return f'<div class="be-range">📐 到期盈亏平衡: {be_range}</div>'

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
        """从 Deribit 主网拉取 BTC-DVOL 历史数据（小时级别），自动分批处理长时间范围"""
        all_data = []
        BATCH_MS = 720 * 3600 * 1000  # 每批最多 720 小时（30天）
        current_start = start_ts
        try:
            async with aiohttp.ClientSession() as session:
                while current_start < end_ts:
                    current_end = min(current_start + BATCH_MS, end_ts)
                    url = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
                    params = {
                        "currency": "BTC",
                        "start_timestamp": current_start,
                        "end_timestamp": current_end,
                        "resolution": "3600"
                    }
                    async with session.get(url, params=params,
                                           timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        data = await resp.json()
                        if 'result' in data and 'data' in data['result']:
                            batch = [
                                {"ts": row[0], "dvol": round(row[4], 2)}
                                for row in data['result']['data']
                            ]
                            all_data.extend(batch)
                    current_start = current_end + 1
        except Exception as e:
            logger.warning(f"获取 DVOL 历史数据失败: {e}")
        # 去重并排序
        seen = set()
        result = []
        for d in sorted(all_data, key=lambda x: x['ts']):
            if d['ts'] not in seen:
                seen.add(d['ts'])
                result.append(d)
        return result

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

            # 计算 DVOL 查询时间范围：从新闻历史最早记录到现在，覆盖完整研究周期
            dvol_data = []
            try:
                import sqlite3 as _sq3
                news_db = BASE_DIR / "data" / "weighted_news_history.db"
                earliest_ts = None
                if news_db.exists():
                    conn = _sq3.connect(news_db)
                    row = conn.execute("SELECT MIN(timestamp) FROM news_history").fetchone()
                    conn.close()
                    if row and row[0]:
                        try:
                            earliest_dt = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
                            earliest_ts = int(earliest_dt.timestamp() * 1000)
                        except Exception:
                            pass
                # 如果没有新闻历史，回退到交易记录时间
                if earliest_ts is None and iv_history:
                    times = [datetime.fromisoformat(p['时间']) for p in iv_history]
                    earliest_ts = int((min(times).timestamp() - 86400) * 1000)
                if earliest_ts is None:
                    earliest_ts = int((datetime.now().timestamp() - 30 * 86400) * 1000)
                end_ts = int(datetime.now().timestamp() * 1000)
                dvol_data = await self._fetch_dvol_history(earliest_ts, end_ts)
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

    async def handle_iv_detail(self, request):
        """返回某个合约的 5 分钟 IV 时间序列"""
        instrument = request.rel_url.query.get('instrument', '')
        limit = int(request.rel_url.query.get('limit', 2016))  # 默认最近 7 天

        if not instrument:
            # 无参数时返回所有有数据的合约列表
            try:
                db_path = BASE_DIR / "data" / "iv_history.db"
                if not db_path.exists():
                    return web.json_response({"合约列表": [], "消息": "暂无数据"},
                        dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))
                conn = sqlite3.connect(db_path)
                rows = conn.execute(
                    "SELECT instrument, COUNT(*) as cnt, MAX(ts) as last_ts "
                    "FROM iv_snapshots GROUP BY instrument ORDER BY instrument"
                ).fetchall()
                conn.close()
                return web.json_response(
                    {"合约列表": [{"合约": r[0], "数据点数": r[1],
                                  "最新时间": datetime.utcfromtimestamp(r[2]).strftime("%Y-%m-%d %H:%M UTC")}
                                 for r in rows]},
                    dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2)
                )
            except Exception as e:
                return web.json_response({"错误": str(e)}, status=500,
                    dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))

        try:
            db_path = BASE_DIR / "data" / "iv_history.db"
            if not db_path.exists():
                return web.json_response({"数据": [], "消息": "暂无采集数据，请先运行 iv_collector.py"},
                    dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))

            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                "SELECT ts, mark_iv, mark_price, spot_price FROM iv_snapshots "
                "WHERE instrument=? ORDER BY ts DESC LIMIT ?",
                (instrument, limit)
            ).fetchall()
            conn.close()

            data = [{"ts": r[0], "iv": r[1], "price_btc": r[2], "spot": r[3]} for r in reversed(rows)]
            return web.json_response(
                {"合约": instrument, "数据": data, "数量": len(data)},
                dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            return web.json_response({"错误": str(e)}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))

    async def handle_iv_detail_chart(self, request):
        """5分钟 IV 走势图页面"""
        # 先获取所有有数据的合约列表，用于下拉选择
        db_path = BASE_DIR / "data" / "iv_history.db"
        instruments_json = "[]"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                rows = conn.execute(
                    "SELECT instrument FROM iv_snapshots GROUP BY instrument ORDER BY instrument"
                ).fetchall()
                conn.close()
                import json as _json
                instruments_json = _json.dumps([r[0] for r in rows])
            except Exception:
                pass

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>合约 IV 5分钟走势</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5}}
.container{{max-width:1200px;margin:0 auto;background:white;padding:20px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.1)}}
h1{{color:#333;font-size:22px;margin-bottom:16px}}
.controls{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;align-items:center}}
select,button{{padding:8px 14px;border-radius:6px;border:1px solid #ddd;font-size:14px}}
button{{background:#007AFF;color:white;border:none;cursor:pointer}}
button:hover{{background:#0056CC}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:20px}}
.stat-card{{background:#f8f9fa;padding:10px;border-radius:8px;border-left:4px solid #007AFF}}
.stat-card.green{{border-left-color:#34C759}}.stat-card.red{{border-left-color:#FF3B30}}
.stat-label{{font-size:11px;color:#666;margin-bottom:3px}}
.stat-value{{font-size:20px;font-weight:bold;color:#333}}
.chart-container{{position:relative;height:400px;margin-bottom:20px}}
.chart-container2{{position:relative;height:250px}}
.back-link{{display:inline-block;margin-bottom:16px;color:#007AFF;text-decoration:none}}
.loading{{text-align:center;padding:30px;color:#888}}
.no-data{{text-align:center;padding:40px;color:#aaa;font-size:14px}}
</style>
</head>
<body>
<div class="container">
<a href="/" class="back-link">← 返回首页</a>
<h1>🔬 合约 IV 5分钟走势</h1>

<div class="controls">
  <select id="instrument-select">
    <option value="">-- 选择合约 --</option>
  </select>
  <select id="range-select">
    <option value="288">最近 24 小时</option>
    <option value="2016" selected>最近 7 天</option>
    <option value="8640">最近 30 天</option>
  </select>
  <button onclick="loadData()">加载</button>
  <span id="last-update" style="font-size:12px;color:#888"></span>
</div>

<div class="stats" id="stats" style="display:none">
  <div class="stat-card"><div class="stat-label">当前 IV</div><div class="stat-value" id="s-current">--</div></div>
  <div class="stat-card green"><div class="stat-label">最低 IV</div><div class="stat-value" id="s-min">--</div></div>
  <div class="stat-card red"><div class="stat-label">最高 IV</div><div class="stat-value" id="s-max">--</div></div>
  <div class="stat-card"><div class="stat-label">平均 IV</div><div class="stat-value" id="s-avg">--</div></div>
  <div class="stat-card"><div class="stat-label">IV 变化</div><div class="stat-value" id="s-change">--</div></div>
</div>

<div class="chart-container"><canvas id="ivChart"></canvas></div>
<div class="chart-container2"><canvas id="priceChart"></canvas></div>
<div id="loading" class="loading" style="display:none">加载中...</div>
<div id="no-data" class="no-data">请选择合约后点击加载</div>
</div>

<script>
const INSTRUMENTS = {instruments_json};
let ivChartInst = null, priceChartInst = null;

// 填充下拉列表
const sel = document.getElementById('instrument-select');
INSTRUMENTS.forEach(inst => {{
  const opt = document.createElement('option');
  opt.value = inst; opt.textContent = inst;
  sel.appendChild(opt);
}});

async function loadData() {{
  const inst = document.getElementById('instrument-select').value;
  const limit = document.getElementById('range-select').value;
  if (!inst) {{ alert('请先选择合约'); return; }}

  document.getElementById('loading').style.display = 'block';
  document.getElementById('no-data').style.display = 'none';
  document.getElementById('stats').style.display = 'none';

  try {{
    const r = await fetch(`/api/iv-detail?instrument=${{encodeURIComponent(inst)}}&limit=${{limit}}`);
    const data = await r.json();

    document.getElementById('loading').style.display = 'none';

    if (!data.数据 || data.数据.length === 0) {{
      document.getElementById('no-data').textContent = '该合约暂无 IV 数据（采集器尚未运行或合约不在持仓中）';
      document.getElementById('no-data').style.display = 'block';
      return;
    }}

    const pts = data.数据;
    const ivVals = pts.map(p => p.iv);
    const priceVals = pts.map(p => p.spot);

    // 统计
    const cur = ivVals[ivVals.length-1];
    const first = ivVals[0];
    const mn = Math.min(...ivVals), mx = Math.max(...ivVals);
    const avg = ivVals.reduce((a,b)=>a+b,0)/ivVals.length;
    const chg = cur - first;
    document.getElementById('s-current').textContent = cur.toFixed(1)+'%';
    document.getElementById('s-min').textContent = mn.toFixed(1)+'%';
    document.getElementById('s-max').textContent = mx.toFixed(1)+'%';
    document.getElementById('s-avg').textContent = avg.toFixed(1)+'%';
    document.getElementById('s-change').textContent = (chg>=0?'+':'')+chg.toFixed(1)+'%';
    document.getElementById('s-change').style.color = chg>=0?'#FF3B30':'#34C759';
    document.getElementById('stats').style.display = 'grid';
    document.getElementById('last-update').textContent =
      '最新: ' + new Date(pts[pts.length-1].ts*1000).toLocaleString('zh-CN');

    const ivDataset = pts.map(p=>({{x:p.ts*1000, y:p.iv}}));
    const priceDataset = pts.map(p=>({{x:p.ts*1000, y:p.spot}}));

    // IV 图表
    if (ivChartInst) ivChartInst.destroy();
    const ctx1 = document.getElementById('ivChart').getContext('2d');
    ivChartInst = new Chart(ctx1, {{
      type: 'line',
      data: {{ datasets: [{{
        label: inst + ' IV (%)',
        data: ivDataset,
        borderColor: '#007AFF',
        backgroundColor: 'rgba(0,122,255,0.08)',
        borderWidth: 1.5,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.2,
        fill: true
      }}] }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{ legend: {{ display: true, position: 'top' }} }},
        scales: {{
          x: {{ type: 'time', time: {{ tooltipFormat: 'MM-dd HH:mm', displayFormats: {{ hour: 'MM-dd HH:mm', day: 'MM-dd' }} }} }},
          y: {{ title: {{ display: true, text: 'IV (%)' }} }}
        }}
      }}
    }});

    // 现货价格图表
    if (priceChartInst) priceChartInst.destroy();
    const ctx2 = document.getElementById('priceChart').getContext('2d');
    priceChartInst = new Chart(ctx2, {{
      type: 'line',
      data: {{ datasets: [{{
        label: 'BTC 现货价格 ($)',
        data: priceDataset,
        borderColor: '#FF9500',
        backgroundColor: 'rgba(255,149,0,0.06)',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.2,
        fill: true
      }}] }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{ legend: {{ display: true, position: 'top' }} }},
        scales: {{
          x: {{ type: 'time', time: {{ tooltipFormat: 'MM-dd HH:mm', displayFormats: {{ hour: 'MM-dd HH:mm', day: 'MM-dd' }} }} }},
          y: {{ title: {{ display: true, text: 'BTC ($)' }} }}
        }}
      }}
    }});

  }} catch(e) {{
    document.getElementById('loading').style.display = 'none';
    document.getElementById('no-data').textContent = '加载失败: ' + e.message;
    document.getElementById('no-data').style.display = 'block';
  }}
}}

// 如果 URL 带了 instrument 参数，自动加载
const urlInst = new URLSearchParams(location.search).get('instrument');
if (urlInst) {{
  document.getElementById('instrument-select').value = urlInst;
  loadData();
}}
</script>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html', charset='utf-8')

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
            "  <span>▲ 旧打分（5002）&nbsp; ● 新打分（5003，含novelty）</span>\n"
            "  <span style=\"margin-left:8px\">新闻筛选：\n"
            "    <button id=\"btn10\" onclick=\"filterNews(10)\" style=\"background:rgba(255,59,48,0.9);color:white;border:none;border-radius:6px;padding:2px 8px;cursor:pointer;font-size:12px\">🔴 10分</button>\n"
            "    <button id=\"btn8\" onclick=\"filterNews(8)\" style=\"background:rgba(255,149,0,0.9);color:white;border:none;border-radius:6px;padding:2px 8px;cursor:pointer;font-size:12px\">🟠 8-9分</button>\n"
            "    <button id=\"btn7\" onclick=\"filterNews(7)\" style=\"background:rgba(255,204,0,0.9);color:white;border:none;border-radius:6px;padding:2px 8px;cursor:pointer;font-size:12px\">🟡 7分</button>\n"
            "    <button id=\"btn5\" onclick=\"filterNews(5)\" style=\"background:rgba(100,149,237,0.9);color:white;border:none;border-radius:6px;padding:2px 8px;cursor:pointer;font-size:12px\">🔵 5-6分</button>\n"
            "    <button id=\"btnAll\" onclick=\"filterNews(0)\" style=\"background:#888;color:white;border:none;border-radius:6px;padding:2px 8px;cursor:pointer;font-size:12px\">全部</button>\n"
            "  </span>\n"
            "</div>\n"
            "<div class=\"chart-container\"><canvas id=\"ivChart\"></canvas></div>\n"
            "<div id=\"news-panel\" style=\"display:none;background:white;border-radius:10px;padding:12px 16px;margin-top:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);font-size:13px\"></div>\n"
            "<div id=\"loading\" class=\"loading\">加载中...</div>\n"
            "</div>\n"
            "<script>\n"
            "let _newsEvents=[];\n"
            "let _newsEventsV2=[];\n"
            "let _chart=null;\n"
            "async function loadIVData(){\n"
            "  try{\n"
            "    const [r1,r2,r3]=await Promise.all([fetch('/api/iv-history'),fetch('/api/news-events?min_score=7'),fetch('/api/news-events-v2?min_score=5')]);\n"
            "    const data=await r1.json();\n"
            "    const nd=await r2.json(); _newsEvents=nd.events||[];\n"
            "    const nd2=await r3.json(); _newsEventsV2=nd2.events||[];\n"
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
            "    const newsDataset=(window._newsEvents||[]).length>0?_newsEvents.map(e=>{const c=dvolPoints.length?dvolPoints.reduce((a,b)=>Math.abs(b.x-e.ts)<Math.abs(a.x-e.ts)?b:a,dvolPoints[0]):{y:0};return{x:e.ts,y:c.y,s:e.score,t:e.content,u:e.news_id};}).filter(p=>p.y>0&&(_filterMin===0||p.s>=_filterMin&&(_filterMin===10?p.s===10:_filterMin===8?p.s>=8&&p.s<10:p.s===7))):[];\n"
            "    const newsDatasetV2=_newsEventsV2.map(e=>{const c=dvolPoints.length?dvolPoints.reduce((a,b)=>Math.abs(b.x-e.ts)<Math.abs(a.x-e.ts)?b:a,dvolPoints[0]):{y:0};return{x:e.ts,y:c.y*0.97,s:e.score,t:e.content,u:e.news_id,base:e.base_score,nov:e.novelty,mul:e.novelty_multiplier};}).filter(p=>p.y>0&&(_filterMin===0||p.s>=_filterMin&&(_filterMin===10?p.s===10:_filterMin===8?p.s>=8&&p.s<10:p.s===7)));\n"
            "    if(_chart){\n"
            "      _chart.data.datasets[0].data=dvolPoints;\n"
            "      _chart.data.datasets[1].data=newsDataset;\n"
            "      _chart.data.datasets[2].data=newsDatasetV2;\n"
            "      _chart.data.datasets[3].data=tradePoints;\n"
            "      _chart.data.datasets[3].pointBackgroundColor=ptColors;\n"
            "      _chart.data.datasets[3].pointRadius=ptRadii;\n"
            "      _chart.data.datasets[4].data=costPoints;\n"
            "      _chart.update();\n"
            "    } else {\n"
            "    _chart=new Chart(ctx,{type:'line',data:{datasets:[\n"
            "      {label:'BTC-DVOL 市场IV(%)',data:dvolPoints,borderColor:'#34C759',backgroundColor:'rgba(52,199,89,0.06)',borderWidth:1.5,pointRadius:0,tension:0.3,fill:false,yAxisID:'y',order:3},\n"
            "      {label:'新闻事件',type:'scatter',data:newsDataset,pointBackgroundColor:function(c){const s=c.raw&&c.raw.s||0;return s>=10?'rgba(255,59,48,0.9)':s>=8?'rgba(255,149,0,0.9)':'rgba(255,204,0,0.85)';},pointRadius:function(c){const s=c.raw&&c.raw.s||0;return s>=10?9:s>=8?7:5;},pointHoverRadius:12,pointStyle:'triangle',showLine:false,yAxisID:'y',order:0},\n"
            "      {label:'新闻事件(新打分)',type:'scatter',data:newsDatasetV2,pointBackgroundColor:function(c){const s=c.raw&&c.raw.s||0;return s>=10?'rgba(255,59,48,0.6)':s>=8?'rgba(255,149,0,0.6)':s>=7?'rgba(255,204,0,0.6)':'rgba(100,149,237,0.7)';},pointRadius:function(c){const s=c.raw&&c.raw.s||0;return s>=10?9:s>=8?7:s>=7?5:4;},pointHoverRadius:12,pointStyle:'circle',showLine:false,yAxisID:'y',order:0,hidden:false},\n"
            "      {label:'交易 IV(%)',data:tradePoints,borderColor:'rgba(0,122,255,0.4)',borderWidth:1,borderDash:[4,4],pointBackgroundColor:ptColors,pointRadius:ptRadii,pointHoverRadius:9,showLine:true,tension:0,fill:false,yAxisID:'y',order:1,hidden:true},\n"
            "      {label:'交易成本($)',data:costPoints,borderColor:'#FF3B30',backgroundColor:'rgba(255,59,48,0.08)',borderWidth:1.5,pointRadius:4,tension:0.3,fill:true,yAxisID:'y1',order:2,hidden:true}\n"
            "    ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},\n"
            "    plugins:{legend:{display:true,position:'top'},tooltip:{callbacks:{afterBody:function(items){\n"
            "      const ti=items.find(i=>i.dataset.label==='交易 IV(%)');\n"
            "      if(ti){const p=tradePoints[ti.dataIndex];if(p)return[(p.v?'🔮 虚拟':\'✅ 真实\')+' | '+p.n];}\n"
            "      const ni=items.find(i=>i.dataset.label==='新闻事件');\n"
            "      if(ni&&ni.raw){return['[旧打分 '+ni.raw.s+'/10] '+(ni.raw.t||'')];}\n"
            "      const ni2=items.find(i=>i.dataset.label==='新闻事件(新打分)');\n"
            "      if(ni2&&ni2.raw){const p=ni2.raw;return['[新打分 '+p.s+'/10] base='+p.base+' novelty='+p.nov+' ×'+p.mul,'  '+(p.t||'')];}\n"
            "      return[];\n"
            "    }}}},\n"
            "    onClick:function(evt,els){const el=els.find(e=>e.datasetIndex===1||e.datasetIndex===2);if(!el||!el.element)return;const p=el.element.$context.raw;if(!p)return;const em=p.s>=10?'🔴':p.s>=8?'🟠':'🟡';const isV2=el.datasetIndex===2;const panel=document.getElementById('news-panel');panel.style.display='block';let extra=isV2?'<br><span style=\"color:#888;font-size:11px\">新打分: base='+p.base+' novelty='+p.nov+' ×'+p.mul+'</span>':'';panel.innerHTML='<b>'+em+' ['+(isV2?'新':'旧')+' '+p.s+'/10]</b> '+new Date(p.x).toLocaleString('zh-CN')+'<br><span style=\"color:#555\">'+(p.t||'（无摘要）')+'</span>'+extra+'<br><a href=\"'+p.u+'\" target=\"_blank\" style=\"color:#007AFF;font-size:11px\">查看原文 →</a>';},\n"
            "    scales:{x:{type:'time',time:{tooltipFormat:'MM-dd HH:mm',displayFormats:{hour:'MM-dd HH:mm',day:'MM-dd'}}},\n"
            "    y:{type:'linear',position:'left',title:{display:true,text:'IV(%)'}},\n"
            "    y1:{type:'linear',position:'right',title:{display:true,text:'成本($)'},grid:{drawOnChartArea:false}}}\n"
            "    }});\n"
            "    } // end else\n"
            "  }catch(e){console.error(e);document.getElementById('loading').innerHTML='加载失败: '+e.message;}\n"
            "}\n"
            "loadIVData();setInterval(loadIVData,60000);\n"
            "let _filterMin=0;\n"
            "function filterNews(minScore){\n"
            "  _filterMin=minScore;\n"
            "  ['btn10','btn8','btn7','btn5','btnAll'].forEach(id=>document.getElementById(id).style.opacity='0.5');\n"
            "  const active=minScore===10?'btn10':minScore===8?'btn8':minScore===7?'btn7':minScore===5?'btn5':'btnAll';\n"
            "  document.getElementById(active).style.opacity='1';\n"
            "  if(!_chart)return;\n"
            "  const dvolPoints=_chart.data.datasets[0].data;\n"
            "  const filterFn=p=>p.y>0&&(minScore===0||p.s>=minScore&&(minScore===10?p.s===10:minScore===8?p.s>=8&&p.s<10:minScore===7?p.s===7:p.s>=5&&p.s<7));\n"
            "  const filtered=_newsEvents.map(e=>{const c=dvolPoints.length?dvolPoints.reduce((a,b)=>Math.abs(b.x-e.ts)<Math.abs(a.x-e.ts)?b:a,dvolPoints[0]):{y:0};return{x:e.ts,y:c.y,s:e.score,t:e.content,u:e.news_id};}).filter(filterFn);\n"
            "  const filteredV2=_newsEventsV2.map(e=>{const c=dvolPoints.length?dvolPoints.reduce((a,b)=>Math.abs(b.x-e.ts)<Math.abs(a.x-e.ts)?b:a,dvolPoints[0]):{y:0};return{x:e.ts,y:c.y*0.97,s:e.score,t:e.content,u:e.news_id,base:e.base_score,nov:e.novelty,mul:e.novelty_multiplier};}).filter(filterFn);\n"
            "  _chart.data.datasets[1].data=filtered;\n"
            "  _chart.data.datasets[2].data=filteredV2;\n"
            "  _chart.update();\n"
            "}\n"
            "</script></body></html>"
        )
        return web.Response(text=html, content_type='text/html', charset='utf-8')

    async def handle_news_events(self, request):
        """返回所有新闻事件（时间戳+分数+内容），用于 IV 图表标注"""
        min_score = int(request.rel_url.query.get('min_score', 7))
        try:
            import sqlite3 as _sq
            db_path = BASE_DIR / "data" / "weighted_news_history.db"
            if not db_path.exists():
                return web.json_response({"events": [], "count": 0},
                    dumps=lambda o: json.dumps(o, ensure_ascii=False))
            conn = _sq.connect(db_path)
            rows = conn.execute(
                "SELECT news_id, timestamp, importance_score FROM news_history "
                "WHERE importance_score >= ? ORDER BY timestamp",
                (min_score,)
            ).fetchall()
            conn.close()
            # 从 news_impact.json 补充内容
            impact_map = {}
            if self.impact_file.exists():
                try:
                    for item in json.loads(self.impact_file.read_text(encoding='utf-8')).values():
                        nid = item.get('news_id', '')
                        if nid:
                            impact_map[nid] = item.get('news_content', '')
                except Exception:
                    pass
            from datetime import timezone as _tz
            events = []
            for news_id, ts_str, score in rows:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=_tz.utc)
                    events.append({
                        "ts": int(ts.timestamp() * 1000),
                        "score": score,
                        "news_id": news_id,
                        "content": impact_map.get(news_id, '')[:80]
                    })
                except Exception:
                    pass
            return web.json_response({"events": events, "count": len(events)},
                dumps=lambda o: json.dumps(o, ensure_ascii=False))
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def handle_news_events_v2(self, request):
        """从新打分接口（5003）实时拉取新闻，用于 IV 图表对比标注"""
        min_score = float(request.rel_url.query.get('min_score', 7))
        NEW_API = "http://43.106.51.106:5003/api/weighted-sentiment/news"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(NEW_API, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    raw = await resp.json()
            news_list = raw.get('data', {}).get('news', raw.get('news', []))
            from datetime import timezone as _tz
            events = []
            for item in news_list:
                score = float(item.get('importance_score', 0))
                if score < min_score:
                    continue
                ts_str = item.get('published_at') or item.get('pubDate', '')
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=_tz.utc)
                    events.append({
                        "ts": int(ts.timestamp() * 1000),
                        "score": score,
                        "base_score": item.get('base_score', ''),
                        "novelty": item.get('novelty', ''),
                        "novelty_multiplier": item.get('novelty_multiplier', ''),
                        "news_id": item.get('guid', ''),
                        "content": item.get('title', '')[:80]
                    })
                except Exception:
                    pass
            events.sort(key=lambda x: x['ts'])
            return web.json_response({"events": events, "count": len(events)},
                dumps=lambda o: json.dumps(o, ensure_ascii=False))
        except Exception as e:
            return web.json_response({"error": str(e), "events": [], "count": 0},
                dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def handle_news_impact(self, request):
        """返回新闻影响数据 JSON"""
        if not self.impact_file.exists():
            return web.json_response(
                {"数据": [], "消息": "暂无数据，请先运行 news_impact_tracker.py"},
                dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2)
            )
        try:
            data = json.loads(self.impact_file.read_text(encoding='utf-8'))
            items = sorted(data.values(), key=lambda x: x.get('trade_time', ''), reverse=True)
            return web.json_response(
                {"数量": len(items), "数据": items},
                dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            return web.json_response({"错误": str(e)}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))

    async def handle_news_impact_page(self, request):
        """新闻事后影响验证页面"""
        impact_data = {}
        if self.impact_file.exists():
            try:
                impact_data = json.loads(self.impact_file.read_text(encoding='utf-8'))
            except Exception:
                pass

        items = sorted(impact_data.values(), key=lambda x: x.get('trade_time', ''), reverse=True)

        cards_html = ""
        if not items:
            cards_html = '<div class="empty">📭 暂无数据，请先运行 news_impact_tracker.py</div>'
        else:
            for item in items:
                changes = item.get('price_changes', {})
                score = item.get('score', '?')
                sentiment = item.get('sentiment', '')
                sl = sentiment.lower()
                s_emoji = '📈' if '看涨' in sentiment or 'bullish' in sl else ('📉' if '看跌' in sentiment or 'bearish' in sl else '😐')
                spot = item.get('spot_at_trade', 0)
                conclusion = item.get('conclusion', '待计算')
                trade_time = item.get('trade_time', '')[:16]
                news = item.get('news_content', '')[:120]
                call_inst = item.get('call_instrument', '')
                combo_id = item.get('combo_id', '')

                # IV 基础信息
                iv_changes = item.get('iv_changes', {})
                iv0 = iv_changes.get('iv_at_t0')
                iv0_str = f"{iv0:.1f}%" if iv0 is not None else "无数据"

                # 对齐表格：价格变化 + IV 变化，T+1h / T+4h / T+24h 三列
                def price_cell(label):
                    val = changes.get(label)
                    if val is None:
                        return '<td class="pending">待计算</td>'
                    color = "#34C759" if val > 0 else ("#FF3B30" if val < 0 else "#888")
                    sign = "+" if val > 0 else ""
                    return f'<td style="color:{color};font-weight:700">{sign}{val:.2f}%</td>'

                def iv_cell(chg_key, abs_key):
                    chg = iv_changes.get(chg_key)
                    abs_v = iv_changes.get(abs_key)
                    if chg is None:
                        return '<td class="pending">无数据</td>'
                    color = "#FF9500" if chg > 0 else ("#5AC8FA" if chg < 0 else "#888")
                    sign = "+" if chg > 0 else ""
                    return f'<td style="color:{color};font-weight:700">{sign}{chg:.1f}%<br><small style="color:#aaa;font-weight:400">{abs_v:.1f}%</small></td>'

                table_html = f"""
<table class="impact-table">
  <thead><tr><th></th><th>T+1h</th><th>T+4h</th><th>T+24h</th></tr></thead>
  <tbody>
    <tr><td class="row-label">💰 价格</td>{price_cell('T+1h')}{price_cell('T+4h')}{price_cell('T+24h')}</tr>
    <tr><td class="row-label">📉 IV变化</td>{iv_cell('iv_chg_t1h','iv_t1h')}{iv_cell('iv_chg_t4h','iv_t4h')}{iv_cell('iv_chg_t24h','iv_t24h')}</tr>
  </tbody>
</table>"""

                # 结论颜色
                if '未引发' in conclusion or '不足' in conclusion:
                    conc_color = "#888"
                elif '显著' in conclusion:
                    conc_color = "#FF9500"
                else:
                    conc_color = "#007AFF"

                cards_html += f"""
<div class="card">
  <div class="card-header">
    <span class="time">🕐 {trade_time}</span>
    <span class="score">⭐ {score}</span>
    <span class="sentiment">{s_emoji} {sentiment}</span>
  </div>
  <div class="news">📰 {news}{'...' if len(item.get('news_content',''))>120 else ''}</div>
  <div class="spot">💰 下单时 BTC: ${spot:,.0f} &nbsp;|&nbsp; 📈 {self._simplify_instrument(call_inst)} &nbsp;|&nbsp; 📉 IV: {iv0_str}</div>
  {f'<div class="combo-id">🔗 Combo: <a href="https://www.deribit.com/combo/{combo_id}" target="_blank">{combo_id}</a></div>' if combo_id else ''}
  {table_html}
  <div class="conclusion" style="color:{conc_color}">💡 {conclusion}</div>
</div>"""

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>新闻影响验证</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:0;padding:16px;background:#f0f2f5}}
.container{{max-width:800px;margin:0 auto}}
h1{{color:#333;font-size:22px;margin-bottom:4px}}
.subtitle{{color:#888;font-size:13px;margin-bottom:16px}}
.back-link{{display:inline-block;margin-bottom:16px;color:#007AFF;text-decoration:none;font-size:14px}}
.card{{background:white;border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.card-header{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:10px;align-items:center}}
.time{{color:#888;font-size:12px}}
.score{{font-size:13px;font-weight:600;color:#FF9500}}
.sentiment{{font-size:13px;color:#555}}
.news{{font-size:14px;color:#333;line-height:1.5;margin-bottom:10px;padding:8px;background:#f8f9fa;border-radius:8px;border-left:3px solid #007AFF}}
.spot{{font-size:12px;color:#888;margin-bottom:10px}}
.impact-table{{width:100%;border-collapse:collapse;margin-bottom:10px;font-size:14px}}
.impact-table th{{background:#f0f2f5;padding:6px 10px;text-align:center;font-size:11px;color:#666;font-weight:600}}
.impact-table td{{padding:8px 10px;text-align:center;border-bottom:1px solid #f0f2f5}}
.impact-table td.row-label{{text-align:left;font-size:12px;color:#888;font-weight:600;white-space:nowrap}}
.impact-table td.pending{{color:#ccc;font-size:12px}}
.conclusion{{font-size:14px;font-weight:600;padding:8px;background:#f8f9fa;border-radius:8px}}
.empty{{text-align:center;padding:40px;color:#aaa}}
.count{{background:#007AFF;color:white;border-radius:12px;padding:2px 10px;font-size:13px;margin-left:8px}}
.section-label{{font-size:11px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:8px 0 4px}}
</style>
</head>
<body>
<div class="container">
  <a href="/" class="back-link">← 返回首页</a>
  <h1>🔍 新闻事后影响验证 <span class="count">{len(items)}</span></h1>
  <div class="subtitle">更新时间: {now_str} &nbsp;|&nbsp; 追踪新闻发布后 BTC 价格变化</div>
  {cards_html}
</div>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html', charset='utf-8')

    async def handle_news_webhook_v3(self, request):
        """接收 weight_extractor_v3 推送的新闻，用 vXkaBDto 账户执行策略
        
        触发条件（三维框架）：
        - A（资金流动直接性）≥ 3（间接但快速传导以上）
        - B（市场预期差）≥ 2（部分超预期以上）
        - 总分 ≥ 7
        - has_similar_high_scores = False
        
        策略：ATM Straddle，$5,000 仓位（测试账户）
        """
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"error": "invalid json"}, status=400)

        news_items = payload.get('news', [])
        if not news_items:
            return web.json_response({"received": 0})

        logger.info(f"Webhook v3 收到 {len(news_items)} 条新闻")
        asyncio.create_task(self._process_webhook_v3(news_items))
        return web.json_response({"received": len(news_items), "status": "processing"})

    async def handle_perp_positions(self, request):
        """返回永续合约持仓列表"""
        try:
            state_file = BASE_DIR / "data" / "perp_positions.json"
            if not state_file.exists():
                return web.json_response({"positions": [], "count": 0},
                    dumps=lambda o: json.dumps(o, ensure_ascii=False))
            positions = json.loads(state_file.read_text(encoding='utf-8'))
            return web.json_response({"positions": positions, "count": len(positions)},
                dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def handle_perp_price(self, request):
        """返回 BTC-PERPETUAL 从指定时间开始的 1 小时 K 线"""
        since_ts = int(request.rel_url.query.get('since', 0))
        if not since_ts:
            since_ts = int(datetime.now().timestamp()) - 3 * 86400
        try:
            end_ts = int(datetime.now().timestamp())
            async with aiohttp.ClientSession() as session:
                r = await session.get(
                    "https://www.deribit.com/api/v2/public/get_tradingview_chart_data",
                    params={
                        "instrument_name": "BTC-PERPETUAL",
                        "start_timestamp": since_ts * 1000,
                        "end_timestamp": end_ts * 1000,
                        "resolution": "60"
                    }, timeout=aiohttp.ClientTimeout(total=10)
                )
                data = await r.json()
            if 'result' not in data or data['result'].get('status') != 'ok':
                return web.json_response({"candles": []},
                    dumps=lambda o: json.dumps(o, ensure_ascii=False))
            res = data['result']
            candles = [{"ts": t, "close": c}
                       for t, c in zip(res.get('ticks', []), res.get('close', []))]
            return web.json_response({"candles": candles},
                dumps=lambda o: json.dumps(o, ensure_ascii=False))
        except Exception as e:
            return web.json_response({"error": str(e), "candles": []}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def handle_perp_page(self, request):
        """永续合约持仓详情页面"""
        state_file = BASE_DIR / "data" / "perp_positions.json"
        positions = []
        if state_file.exists():
            try:
                positions = json.loads(state_file.read_text(encoding='utf-8'))
            except Exception:
                pass

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>永续合约持仓</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:0;padding:16px;background:#f0f2f5}}
.container{{max-width:900px;margin:0 auto}}
h1{{color:#333;font-size:22px;margin-bottom:4px}}
.subtitle{{color:#888;font-size:13px;margin-bottom:16px}}
.back-link{{display:inline-block;margin-bottom:16px;color:#007AFF;text-decoration:none;font-size:14px}}
.card{{background:white;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.card-header{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.dir-badge{{color:white;font-size:12px;padding:3px 10px;border-radius:10px;font-weight:700}}
.news{{font-size:13px;color:#555;padding:8px;background:#f8f9fa;border-radius:8px;margin-bottom:10px;border-left:3px solid #007AFF}}
.info-row{{display:flex;flex-wrap:wrap;gap:16px;font-size:13px;color:#555;margin-bottom:8px}}
.pnl{{font-size:16px;font-weight:700;margin-top:6px}}
.chart-wrap{{position:relative;height:160px;margin-top:10px}}
.toggle-chart{{font-size:12px;color:#007AFF;cursor:pointer;margin-top:6px}}
.empty{{text-align:center;padding:40px;color:#aaa}}
.closed-badge{{font-size:11px;background:#888;color:white;padding:1px 6px;border-radius:6px;margin-left:6px}}
</style>
</head>
<body>
<div class="container">
  <a href="/vol-account" class="back-link">← 返回 Vol 账户</a>
  <h1>📊 永续合约持仓</h1>
  <div class="subtitle">更新时间: {now_str} | 两账户合计 {len(positions)} 条</div>
  <div id="cards">{'<div class="empty">📭 暂无持仓记录</div>' if not positions else ''}</div>
</div>
<script>
const positions = {json.dumps(positions, ensure_ascii=False)};
const charts = {{}};

async function getCurrentSpot() {{
  try {{
    const r = await fetch('https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd');
    const d = await r.json();
    return d.result.index_price;
  }} catch(e) {{ return 0; }}
}}

async function renderCards() {{
  const spot = await getCurrentSpot();
  const container = document.getElementById('cards');
  if (!positions.length) return;
  let html = '';
  positions.forEach((p, i) => {{
    const isLong = p.direction === 'buy';
    const dirColor = isLong ? '#34C759' : '#FF3B30';
    const dirLabel = isLong ? '📈 多头' : '📉 空头';
    const pnlUsd = spot > 0 ? (isLong ? (spot - p.entry_price) / p.entry_price : (p.entry_price - spot) / p.entry_price) * p.amount_usd : 0;
    const pnlPct = spot > 0 ? (isLong ? (spot - p.entry_price) / p.entry_price : (p.entry_price - spot) / p.entry_price) * 100 : 0;
    const pnlColor = pnlUsd >= 0 ? '#34C759' : '#FF3B30';
    const sign = pnlUsd >= 0 ? '+' : '';
    const closedBadge = p.closed ? '<span class="closed-badge">已平仓</span>' : '';
    const closeAt = p.close_time ? p.close_time.slice(0,16) : '';
    html += `
<div class="card">
  <div class="card-header">
    <span class="dir-badge" style="background:${{dirColor}}">${{dirLabel}}</span>
    <span style="font-size:13px;color:#888">🕐 ${{p.open_time.slice(0,16)}}</span>
    <span style="font-size:13px;color:#888">账户: ${{p.account}}</span>
    ${{closedBadge}}
  </div>
  <div class="news">📰 [${{p.score}}/10] ${{p.news_title}}</div>
  <div class="info-row">
    <span>💰 入场价: <b>$${{p.entry_price.toLocaleString()}}</b></span>
    <span>💵 仓位: $${{p.amount_usd}}</span>
    ${{spot > 0 ? '<span>📍 当前价: <b>$' + spot.toLocaleString() + '</b></span>' : ''}}
    <span>⏰ 平仓: ${{closeAt}}</span>
  </div>
  ${{spot > 0 ? '<div class="pnl" style="color:' + pnlColor + '">📊 浮动PnL: ' + sign + '$' + pnlUsd.toFixed(2) + ' (' + sign + pnlPct.toFixed(2) + '%)</div>' : ''}}
  <div class="toggle-chart" onclick="toggleChart(${{i}}, '${{p.open_time}}', ${{p.entry_price}})">📈 查看 BTC 价格走势 ▼</div>
  <div id="chart-${{i}}" style="display:none">
    <div class="chart-wrap"><canvas id="canvas-${{i}}"></canvas></div>
  </div>
</div>`;
  }});
  container.innerHTML = html;
}}

async function toggleChart(idx, openTime, entryPrice) {{
  const div = document.getElementById('chart-' + idx);
  const hidden = div.style.display === 'none';
  div.style.display = hidden ? 'block' : 'none';
  if (!hidden || charts[idx]) return;
  const sinceTs = Math.floor(new Date(openTime).getTime() / 1000);
  const r = await fetch('/api/perp-price?since=' + sinceTs);
  const d = await r.json();
  if (!d.candles || !d.candles.length) return;
  const priceData = d.candles.map(c => ({{x: c.ts, y: c.close}}));
  const ctx = document.getElementById('canvas-' + idx).getContext('2d');
  charts[idx] = new Chart(ctx, {{
    type: 'line',
    data: {{ datasets: [
      {{label: 'BTC 价格', data: priceData, borderColor: '#007AFF', backgroundColor: 'rgba(0,122,255,0.06)', borderWidth: 1.5, pointRadius: 0, tension: 0.2, fill: true}},
      {{label: '入场价 $' + entryPrice.toLocaleString(), data: priceData.map(p => ({{x: p.x, y: entryPrice}})), borderColor: 'rgba(255,149,0,0.8)', borderWidth: 1.5, borderDash: [5,3], pointRadius: 0, fill: false}}
    ]}},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: true, position: 'top', labels: {{ font: {{ size: 10 }} }} }},
        tooltip: {{ callbacks: {{ title: i => new Date(i[0].parsed.x).toLocaleString('zh-CN') }} }}
      }},
      scales: {{
        x: {{ type: 'time', time: {{ tooltipFormat: 'MM-dd HH:mm', displayFormats: {{ hour: 'MM-dd HH:mm' }} }}, ticks: {{ maxTicksLimit: 5, font: {{ size: 10 }} }} }},
        y: {{ ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v.toLocaleString() }} }}
      }}
    }}
  }});
}}

renderCards();
setInterval(renderCards, 30000);
</script>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html', charset='utf-8')

    async def handle_vol_open(self, request):
        """手动/定时触发 Vol 账户开仓"""
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from vol_account_strategy import VolAccountStrategy
            vol = VolAccountStrategy()
            result = await vol.open_position()
            if result:
                return web.json_response({"status": "opened", "premium_usd": result['premium_usd']},
                    dumps=lambda o: json.dumps(o, ensure_ascii=False))
            return web.json_response({"status": "skipped"},
                dumps=lambda o: json.dumps(o, ensure_ascii=False))
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def handle_vol_close(self, request):
        """手动触发 Vol 账户平仓"""
        try:
            body = await request.json()
            reason = body.get('reason', '手动平仓')
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from vol_account_strategy import VolAccountStrategy
            vol = VolAccountStrategy()
            result = await vol.close_position(reason)
            if result:
                return web.json_response({"status": "closed", "pnl_usd": result['pnl_usd']},
                    dumps=lambda o: json.dumps(o, ensure_ascii=False))
            return web.json_response({"status": "no_position"},
                dumps=lambda o: json.dumps(o, ensure_ascii=False))
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def _process_webhook_v3(self, news_items: list):
        """处理 v3 新闻：1) 触发 vXkaBDto 账户下单；2) 触发 Vol 账户平仓"""
        import sys, os
        sys.path.insert(0, str(BASE_DIR))
        try:
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / '.env')
            import aiohttp as _aio

            TESTNET = "https://test.deribit.com/api/v2"
            API_KEY = "vXkaBDto"
            API_SECRET = "J54Ccsff9g5PlYK-ELRVunkvnST-cZ6puVBXbhwYrnY"
            TARGET_LEG_USD = 2500.0  # 每腿 $2500，两腿合计 $5000
            LOG_FILE = BASE_DIR / "logs" / "v3_trades.log"

            # 认证
            async with _aio.ClientSession() as session:
                r = await session.get(f"{TESTNET}/public/auth", params={
                    "grant_type": "client_credentials",
                    "client_id": API_KEY, "client_secret": API_SECRET
                })
                d = await r.json()
                if 'result' not in d:
                    logger.error(f"v3 webhook 认证失败: {d}")
                    return
                token = d['result']['access_token']
                headers = {"Authorization": f"Bearer {token}"}

                # 获取现货价格
                r2 = await session.get("https://www.deribit.com/api/v2/public/get_index_price",
                                       params={"index_name": "btc_usd"})
                spot = (await r2.json())['result']['index_price']

            for item in news_items:
                score = float(item.get('importance_score', 0))
                a_score = int(item.get('capital_flow_directness_score', 0))
                b_score = int(item.get('market_expectation_gap_score', 0))
                similar = item.get('has_similar_high_scores', False)
                title = item.get('title', '')[:80]
                guid = item.get('guid', '')

                # 过滤条件
                if score < 7 or a_score < 3 or b_score < 2 or similar:
                    logger.info(f"v3 跳过: score={score} A={a_score} B={b_score} similar={similar} | {title[:50]}")
                    continue

                logger.info(f"v3 触发下单: score={score} A={a_score} B={b_score} | {title}")

                # 查找 ATM 合约（+3天）
                from datetime import datetime, timedelta
                now = datetime.now()
                target = now + timedelta(days=3)

                async with _aio.ClientSession() as session:
                    r3 = await session.get("https://www.deribit.com/api/v2/public/get_instruments",
                                           params={"currency": "BTC", "kind": "option", "expired": "false"})
                    instruments = (await r3.json()).get('result', [])

                expiries = set()
                for inst in instruments:
                    ts = inst.get('expiration_timestamp')
                    if ts:
                        expiries.add(datetime.fromtimestamp(ts / 1000))
                future = sorted(e for e in expiries if e > now)
                if not future:
                    continue
                chosen = min(future, key=lambda e: abs((e - target).total_seconds()))

                calls, puts = [], []
                for inst in instruments:
                    ts = inst.get('expiration_timestamp')
                    if not ts or datetime.fromtimestamp(ts / 1000).date() != chosen.date():
                        continue
                    strike = inst.get('strike', 0)
                    name = inst.get('instrument_name', '')
                    opt = inst.get('option_type', '')
                    diff = abs(strike - spot)
                    if opt == 'call':
                        calls.append((name, strike, diff))
                    elif opt == 'put':
                        puts.append((name, strike, diff))

                if not calls or not puts:
                    continue
                calls.sort(key=lambda x: x[2])
                puts.sort(key=lambda x: x[2])
                call_inst = calls[0][0]
                put_inst = [p for p in puts if p[1] == calls[0][1]]
                put_inst = put_inst[0][0] if put_inst else puts[0][0]

                # 获取价格，计算数量
                import math
                async with _aio.ClientSession() as session:
                    rc = await session.get("https://www.deribit.com/api/v2/public/ticker",
                                           params={"instrument_name": call_inst})
                    call_price = (await rc.json()).get('result', {}).get('mark_price', 0)

                if call_price <= 0:
                    continue
                raw_amt = TARGET_LEG_USD / (call_price * spot)
                amount = max(0.1, round(math.ceil(raw_amt / 0.1) * 0.1, 1))

                # 下单
                async with _aio.ClientSession() as session:
                    rc = await session.get(f"{TESTNET}/private/buy",
                        params={"instrument_name": call_inst, "amount": amount, "type": "market"},
                        headers=headers)
                    call_order = (await rc.json()).get('result', {})
                    rp = await session.get(f"{TESTNET}/private/buy",
                        params={"instrument_name": put_inst, "amount": amount, "type": "market"},
                        headers=headers)
                    put_order = (await rp.json()).get('result', {})

                call_oid = call_order.get('order', {}).get('order_id', 'FAILED')
                put_oid = put_order.get('order', {}).get('order_id', 'FAILED')
                total_cost = call_price * 2 * amount * spot

                log_entry = (
                    f"\n{'='*80}\n"
                    f"账户: {API_KEY} (v3策略)\n"
                    f"交易时间: {datetime.now().isoformat()}\n"
                    f"新闻: {title}\n"
                    f"分数: {score}/10 | A={a_score} B={b_score}\n"
                    f"现货: ${spot:,.2f}\n"
                    f"看涨: {call_inst} | 订单: {call_oid}\n"
                    f"看跌: {put_inst} | 订单: {put_oid}\n"
                    f"数量: {amount} BTC | 估算成本: ${total_cost:.2f}\n"
                    f"{'='*80}\n"
                )
                with open(LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                logger.info(f"✓ v3 下单成功: {call_inst} + {put_inst} | ${total_cost:.2f}")

                # 同时触发 Vol 账户（qCoXRSu6）平仓：重大新闻来了，卖出的 Straddle 需要止损
                try:
                    from vol_account_strategy import VolAccountStrategy
                    vol = VolAccountStrategy()
                    vol_state = vol.get_state()
                    if vol_state.get('has_position'):
                        reason = f"新闻止损 [{score}/10 A={a_score} B={b_score}]: {title[:50]}"
                        await vol.close_position(reason)
                        logger.info(f"  ✓ Vol 账户已平仓（新闻止损）")
                except Exception as ve:
                    logger.warning(f"  Vol 账户平仓失败: {ve}")

        except Exception as e:
            logger.error(f"v3 webhook 处理异常: {e}", exc_info=True)

    async def handle_news_webhook(self, request):
        """接收情绪 API 服务器推送的新高分新闻，立即触发下单评估"""
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"error": "invalid json"}, status=400)

        news_items = payload.get('news', [])
        if not news_items:
            return web.json_response({"received": 0})

        logger.info(f"Webhook 收到 {len(news_items)} 条新闻，启动下单评估...")

        # 异步触发下单流程，不阻塞 webhook 响应
        asyncio.create_task(self._process_webhook_news(news_items))

        return web.json_response({"received": len(news_items), "status": "processing"})

    async def handle_vol_account_api(self, request):
        """Vol 账户 JSON API"""
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from vol_account_strategy import VolAccountStrategy
            vol = VolAccountStrategy()

            summary = await vol.get_account_summary()
            positions = await vol.get_positions()

            # 解析历史交易日志
            trade_log = BASE_DIR / "logs" / "vol_account_trades.log"
            trades = []
            if trade_log.exists():
                content = trade_log.read_text(encoding='utf-8')
                for entry in content.split('=' * 80):
                    entry = entry.strip()
                    if '策略: IV Reversion' not in entry:
                        continue
                    t = {}
                    for line in entry.split('\n'):
                        line = line.strip()
                        if ':' not in line:
                            continue
                        k, v = line.split(':', 1)
                        k, v = k.strip(), v.strip()
                        if k == '交易时间':
                            t['time'] = v
                        elif k == '现货价格':
                            t['spot'] = v
                        elif k == 'ATM IV':
                            t['atm_iv'] = v
                        elif k == '卖出 OTM Call':
                            t['call'] = v
                        elif k == '卖出 OTM Put':
                            t['put'] = v
                        elif k == '总收入':
                            t['premium'] = v
                        elif k == '盈利区间':
                            t['profit_range'] = v
                        elif k == '触发新闻':
                            t['news'] = v
                    if t:
                        trades.append(t)

            return web.json_response({
                "账户": "qCoXRSu6",
                "策略": "IV Reversion (OTM Strangle)",
                "余额_BTC": summary.get('balance', 0),
                "可用_BTC": summary.get('available_funds', 0),
                "当前持仓数": len(positions),
                "当前持仓": [
                    {
                        "合约": p.get('instrument_name'),
                        "方向": "卖出" if p.get('size', 0) < 0 else "买入",
                        "数量": abs(p.get('size', 0)),
                        "delta": round(p.get('delta', 0), 4),
                        "浮动盈亏_BTC": round(p.get('floating_profit_loss', 0), 6),
                    }
                    for p in positions
                ],
                "历史交易": trades,
                "查询时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error(f"Vol 账户 API 错误: {e}")
            return web.json_response({"错误": str(e)}, status=500,
                dumps=lambda o: json.dumps(o, ensure_ascii=False, indent=2))

    async def handle_vol_account(self, request):
        """Vol 账户持仓管理页面"""
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from vol_account_strategy import VolAccountStrategy
            vol = VolAccountStrategy()

            summary = await vol.get_account_summary()
            positions = await vol.get_positions()
            balance = summary.get('balance', 0)
            available = summary.get('available_funds', 0)
            margin = summary.get('initial_margin', 0)

            # 持仓卡片
            pos_html = ''
            if not positions:
                pos_html = '<div class="empty">📭 当前无持仓</div>'
            else:
                for p in positions:
                    name = p.get('instrument_name', '')
                    size = p.get('size', 0)
                    direction = '📉 卖出' if size < 0 else '📈 买入'
                    delta = p.get('delta', 0)
                    pnl = p.get('floating_profit_loss', 0)
                    pnl_usd = pnl * 67000  # 估算
                    pnl_color = '#34C759' if pnl >= 0 else '#FF3B30'
                    sign = '+' if pnl >= 0 else ''
                    pos_html += f"""
    <div class="pos-card">
      <div class="pos-name">{name}</div>
      <div class="pos-row">
    <span>{direction} {abs(size)} BTC</span>
    <span>Delta: {delta:.4f}</span>
    <span style="color:{pnl_color}">浮动PnL: {sign}{pnl:.6f} BTC ({sign}{pnl_usd:.0f} USD)</span>
      </div>
    </div>"""

            # 历史交易
            trade_log = BASE_DIR / "logs" / "vol_account_trades.log"
            trades_html = ''
            if trade_log.exists():
                content = trade_log.read_text(encoding='utf-8')
                entries = [e.strip() for e in content.split('=' * 80) if 'IV Reversion' in e]
                for entry in reversed(entries[-10:]):
                    lines = {k.strip(): v.strip() for line in entry.split('\n')
                             if ':' in line for k, v in [line.split(':', 1)]}
                    t_time = lines.get('交易时间', '')[:16]
                    t_spot = lines.get('现货价格', '')
                    t_iv = lines.get('ATM IV', '')
                    t_call = lines.get('卖出 OTM Call', '')
                    t_put = lines.get('卖出 OTM Put', '')
                    t_prem = lines.get('总收入', '')
                    t_range = lines.get('盈利区间', '')
                    t_news = lines.get('触发新闻', '')[:80]
                    trades_html += f"""
    <div class="trade-card">
      <div class="trade-header">
    <span class="trade-time">🕐 {t_time}</span>
    <span class="trade-prem">💰 收入: {t_prem}</span>
      </div>
      <div class="trade-news">📰 {t_news}</div>
      <div class="trade-row">
    <span>现货: {t_spot}</span>
    <span>ATM IV: {t_iv}</span>
      </div>
      <div class="trade-row">
    <span>📉 卖出 Call: {t_call}</span>
    <span>📉 卖出 Put: {t_put}</span>
      </div>
      <div class="trade-range">📐 盈利区间: {t_range}</div>
    </div>"""
            if not trades_html:
                trades_html = '<div class="empty">📭 暂无历史交易</div>'

            # v3 策略交易记录
            v3_log = BASE_DIR / "logs" / "v3_trades.log"
            v3_trades_html = ''
            if v3_log.exists():
                v3_content = v3_log.read_text(encoding='utf-8')
                v3_entries = [e.strip() for e in v3_content.split('=' * 80) if '账户: vXkaBDto' in e]
                for entry in reversed(v3_entries[-10:]):
                    lines = {k.strip(): v.strip() for line in entry.split('\n')
                             if ':' in line for k, v in [line.split(':', 1)]}
                    t_time = lines.get('交易时间', '')[:16]
                    t_news = lines.get('新闻', '')[:80]
                    t_score = lines.get('分数', '')
                    t_spot = lines.get('现货', '')
                    t_call = lines.get('看涨', '')
                    t_put = lines.get('看跌', '')
                    t_cost = lines.get('估算成本', '')
                    v3_trades_html += f"""
<div class="trade-card" style="border-left:3px solid #5AC8FA">
  <div class="trade-header">
    <span class="trade-time">🕐 {t_time}</span>
    <span style="font-size:13px;font-weight:700;color:#5AC8FA">💰 {t_cost}</span>
  </div>
  <div class="trade-news">📰 {t_news}</div>
  <div class="trade-row">
    <span>分数: {t_score}</span>
    <span>现货: {t_spot}</span>
  </div>
  <div class="trade-row">
    <span>📈 {t_call}</span>
    <span>📉 {t_put}</span>
  </div>
</div>"""
            if not v3_trades_html:
                v3_trades_html = '<div class="empty">📭 暂无 v3 策略交易</div>'

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vol 账户持仓</title>
    <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:0;padding:16px;background:#f0f2f5}}
    .container{{max-width:800px;margin:0 auto}}
    h1{{color:#333;font-size:22px;margin-bottom:4px}}
    .subtitle{{color:#888;font-size:13px;margin-bottom:16px}}
    .back-link{{display:inline-block;margin-bottom:16px;color:#007AFF;text-decoration:none;font-size:14px}}
    .account-box{{background:white;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.08);border-left:4px solid #FF9500}}
    .account-title{{font-size:13px;font-weight:700;color:#FF9500;margin-bottom:10px}}
    .account-row{{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}}
    .account-item{{text-align:center}}
    .account-label{{font-size:11px;color:#888}}
    .account-value{{font-size:18px;font-weight:700;color:#333}}
    .section-title{{font-size:16px;font-weight:700;color:#333;margin:16px 0 8px}}
    .pos-card{{background:white;border-radius:10px;padding:12px 16px;margin-bottom:10px;box-shadow:0 2px 6px rgba(0,0,0,.06);border-left:3px solid #FF3B30}}
    .pos-name{{font-size:14px;font-weight:700;color:#333;margin-bottom:6px}}
    .pos-row{{display:flex;flex-wrap:wrap;gap:12px;font-size:13px;color:#555}}
    .trade-card{{background:white;border-radius:10px;padding:12px 16px;margin-bottom:10px;box-shadow:0 2px 6px rgba(0,0,0,.06)}}
    .trade-header{{display:flex;justify-content:space-between;margin-bottom:8px}}
    .trade-time{{font-size:12px;color:#888}}
    .trade-prem{{font-size:14px;font-weight:700;color:#34C759}}
    .trade-news{{font-size:13px;color:#555;margin-bottom:8px;padding:6px;background:#f8f9fa;border-radius:6px}}
    .trade-row{{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:#666;margin-bottom:4px}}
    .trade-range{{font-size:13px;font-weight:600;color:#007AFF;margin-top:6px}}
    .empty{{text-align:center;padding:30px;color:#aaa}}
    .strategy-box{{background:#f8f9fa;border-radius:10px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#555;border-left:3px solid #007AFF}}
    </style>
    </head>
    <body>
    <div class="container">
      <a href="/" class="back-link">← 返回首页</a>
      <h1>⚡ Vol 账户持仓管理</h1>
      <div class="subtitle">账户: qCoXRSu6 | 更新时间: {now_str}</div>

      <div class="strategy-box">
    <strong>策略：新闻驱动永续合约（BTC-PERPETUAL）</strong><br>
    当新闻评分 ≥ 7 分时，根据情绪方向自动下单：<br>
    📈 正面新闻 → 两账户各买入 $1,000 多头，3 天后平仓<br>
    📉 负面新闻 → 两账户各卖出 $1,000 空头，3 天后平仓<br>
    账户：qCoXRSu6 + vXkaBDto（测试网）
      </div>

      <div class="account-box">
    <div class="account-title">📊 账户概览</div>
    <div class="account-row">
          <div class="account-item">
        <div class="account-label">总余额</div>
        <div class="account-value">{balance:.4f} BTC</div>
          </div>
          <div class="account-item">
        <div class="account-label">可用资金</div>
        <div class="account-value">{available:.4f} BTC</div>
          </div>
          <div class="account-item">
        <div class="account-label">占用保证金</div>
        <div class="account-value">{margin:.4f} BTC</div>
          </div>
          <div class="account-item">
        <div class="account-label">当前持仓</div>
        <div class="account-value">{len(positions)} 个</div>
          </div>
    </div>
      </div>

      <div class="section-title">📋 当前持仓</div>
      {pos_html}

      <div class="section-title">🧪 v3 策略交易（vXkaBDto 账户）</div>
      {v3_trades_html}

      <div class="section-title">📊 永续合约持仓（两账户）<a href="/perp" style="font-size:12px;color:#007AFF;font-weight:400;margin-left:8px">查看详情 →</a></div>
      <div id="perp-positions">加载中...</div>
    </div>
    <script>
    // 加载永续合约持仓
    async function loadPerpPositions(){{
      try{{
        const r=await fetch('/api/perp-positions');
        const d=await r.json();
        const el=document.getElementById('perp-positions');
        if(!d.positions||d.positions.length===0){{el.innerHTML='<div class="empty">📭 暂无永续合约持仓</div>';return;}}
        let html='';
        for(const p of d.positions){{
          const dir=p.direction==='buy'?'📈 多头':'📉 空头';
          const closed=p.closed?'<span style="background:#888;color:white;font-size:11px;padding:1px 6px;border-radius:6px;margin-left:4px">已平仓</span>':'';
          const closeAt=p.close_time?p.close_time.slice(0,16):'';
          html+=`<div class="trade-card" style="border-left:3px solid ${{p.direction==='buy'?'#34C759':'#FF3B30'}}">
            <div class="trade-header"><span class="trade-time">🕐 ${{p.open_time.slice(0,16)}}</span><span>${{dir}} $${{p.amount_usd}}${{closed}}</span></div>
            <div class="trade-news">📰 [${{p.score}}/10] ${{p.news_title}}</div>
            <div class="trade-row"><span>账户: ${{p.account}}</span><span>入场: $${{p.entry_price.toLocaleString()}}</span><span>计划平仓: ${{closeAt}}</span></div>
          </div>`;
        }}
        el.innerHTML=html;
      }}catch(e){{document.getElementById('perp-positions').textContent='加载失败';}}
    }}
    loadPerpPositions();
    </script>
    </body>
    </html>"""
            return web.Response(text=html, content_type='text/html', charset='utf-8')
        except Exception as e:
            logger.error(f"Vol 账户页面错误: {e}")
            return web.Response(text=f"<h1>错误: {e}</h1>", content_type='text/html', charset='utf-8')

    async def _process_webhook_news(self, news_items: list):
        """处理 webhook 推送的新闻，执行下单评估"""
        import sys
        sys.path.insert(0, str(BASE_DIR))
        try:
            from weighted_sentiment_cron import StraddleExecutor, SimplifiedTradeLogger, TradeFilter
            from weighted_sentiment_news_tracker import NewsTracker
            from weighted_sentiment_models import WeightedNews
            from datetime import timezone
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / '.env')

            news_tracker = NewsTracker()
            executor = StraddleExecutor()
            trade_filter = TradeFilter(executor)
            trade_logger = SimplifiedTradeLogger()

            news_list = []
            for item in news_items:
                try:
                    score = float(item.get('importance_score', 0))
                    sentiment_map = {'积极': 'positive', '正面': 'positive',
                                     '负面': 'negative', '消极': 'negative',
                                     '中立': 'neutral', 'positive': 'positive',
                                     'negative': 'negative', 'neutral': 'neutral'}
                    sentiment = sentiment_map.get(str(item.get('sentiment', '')), 'neutral')
                    ts_str = item.get('published_at') or item.get('pubDate', '')
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except Exception:
                        ts = datetime.now(timezone.utc)
                    news_list.append(WeightedNews(
                        news_id=item.get('guid', ''),
                        content=item.get('title', ''),
                        sentiment=sentiment,
                        importance_score=score,
                        timestamp=ts,
                        has_similar_high_scores=bool(item.get('has_similar_high_scores', False)),
                        event_category=str(item.get('event_category', ''))
                    ))
                except Exception as e:
                    logger.warning(f"Webhook 新闻解析失败: {e}")

            new_news = await news_tracker.identify_new_news(news_list)
            if not new_news:
                logger.info("Webhook: 无新的高分新闻")
                await news_tracker.update_history(news_list)
                return

            for news in new_news:
                logger.info(f"Webhook 处理: [{news.importance_score}/10] {news.content[:60]}...")
                try:
                    spot_price = await executor.get_spot_price()
                    call_inst, put_inst = await executor.find_atm_options(spot_price)
                    if not call_inst or not put_inst:
                        continue
                    allowed, reason = await trade_filter.check(news, call_inst, put_inst)
                    if not allowed:
                        logger.info(f"  ⏭ {reason}")
                        continue
                    logger.info(f"  ✓ 过滤通过，下单: {reason}")
                    result = await executor.execute_straddle(news)
                    call_iv, put_iv = 0.0, 0.0
                    if result.success and result.call_option and result.put_option:
                        call_iv = await executor.get_option_iv(result.call_option.instrument_name)
                        put_iv = await executor.get_option_iv(result.put_option.instrument_name)
                    await trade_logger.log_trade(news, result, call_iv, put_iv)
                    if result.success:
                        logger.info(f"  ✓ 下单成功: {result.call_option.instrument_name} | ${result.total_cost:.2f}")
                except Exception as e:
                    logger.error(f"  ✗ Webhook 下单失败: {e}", exc_info=True)

            await news_tracker.update_history(news_list)

        except Exception as e:
            logger.error(f"Webhook 处理异常: {e}", exc_info=True)

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
