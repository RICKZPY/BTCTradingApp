"""
宏观经济AI分析工具 - 完整版后端服务
1. 实时市场信号（Ziwox）
2. 实时汇率（Alpha Vantage）
3. 宏观经济日历（TradingEconomics或模拟数据）
4. AI综合分析（laozhang.ai）
"""

import os
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from alpha_vantage.foreignexchange import ForeignExchange
import tradingeconomics as te

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 配置管理
# ============================================================================
class Config:
    def __init__(self):
        # laozhang.ai 配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = "https://api.laozhang.ai/v1"
        
        # Alpha Vantage 配置
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY", "2M66S0EB6ZMHO2ST")
        
        # Ziwox API 配置
        self.ziwox_api_key = os.getenv("ZIWOX_API_KEY", "B65991B99EB498AB")
        self.ziwox_api_url = "https://ziwox.com/terminal/services/API/V1/fulldata.php"
        
        # TradingEconomics 配置
        self.te_key = os.getenv("TRADINGECONOMICS_KEY", "guest:guest")
        
        # 模式开关
        self.use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
        self.enable_ai = os.getenv("ENABLE_AI", "true").lower() == "true"
        
        # 监控的货币对
        self.watch_currency_pairs = [
            'EURUSD', 'GBPUSD', 'USDCHF', 'USDCNH', 
            'USDJPY', 'AUDUSD', 'XAUUSD', 'XAGUSD', 'BTCUSD'
        ]
        
        # Ziwox需要小写参数
        self.ziwox_pairs = [pair.lower() for pair in self.watch_currency_pairs]
        
        # Alpha Vantage特殊品种映射
        self.av_special_pairs = {
            'XAUUSD': ('XAU', 'USD'),
            'XAGUSD': ('XAG', 'USD'),
            'BTCUSD': ('BTC', 'USD')
        }
        
        # 重点关注的国家
        self.watch_countries = ['US', 'EU', 'CN', 'JP', 'GB', 'AU', 'CA', 'CH']
        
        # 货币与国家映射
        self.currency_to_country = {
            'USD': 'US', 'EUR': 'EU', 'CNY': 'CN', 'CNH': 'CN',
            'JPY': 'JP', 'GBP': 'GB', 'AUD': 'AU', 
            'CAD': 'CA', 'CHF': 'CH', 'XAU': 'GLOBAL', 
            'XAG': 'GLOBAL', 'BTC': 'CRYPTO'
        }

config = Config()

# ============================================================================
# 模拟数据生成器（用于TradingEconomics API不可用时）
# ============================================================================
class MockDataGenerator:
    """模拟宏观经济事件数据生成器"""
    
    def __init__(self):
        # 模拟今日宏观经济事件
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.sample_events = [
            {
                "id": 1,
                "date": today_str,
                "time": "20:30",
                "country": "US",
                "name": "CPI月率",
                "forecast": "0.3%",
                "previous": "0.4%",
                "importance": 3,
                "currency": "USD",
                "actual": "0.4%",
                "description": "美国消费者价格指数月度变化"
            },
            {
                "id": 2,
                "date": today_str,
                "time": "15:00",
                "country": "EU",
                "name": "ZEW经济景气指数",
                "forecast": "-20.5",
                "previous": "-22.0",
                "importance": 2,
                "currency": "EUR",
                "actual": "-19.8",
                "description": "欧洲经济研究中心调查的经济景气指数"
            },
            {
                "id": 3,
                "date": today_str,
                "time": "21:00",
                "country": "US",
                "name": "美联储利率决议",
                "forecast": "5.5%",
                "previous": "5.5%",
                "importance": 3,
                "currency": "USD",
                "actual": "5.5%",
                "description": "美联储联邦基金利率决定"
            },
            {
                "id": 4,
                "date": today_str,
                "time": "07:50",
                "country": "JP",
                "name": "GDP年率",
                "forecast": "1.2%",
                "previous": "1.0%",
                "importance": 2,
                "currency": "JPY",
                "actual": "1.1%",
                "description": "日本国内生产总值年度增长率"
            },
            {
                "id": 5,
                "date": today_str,
                "time": "10:00",
                "country": "CN",
                "name": "贸易帐",
                "forecast": "75.0B",
                "previous": "72.9B",
                "importance": 2,
                "currency": "CNY",
                "actual": "77.2B",
                "description": "中国进出口贸易差额"
            }
        ]
    
    def generate_events(self):
        """生成模拟宏观经济事件"""
        logger.info("使用模拟宏观经济事件数据")
        return self.sample_events

mock_gen = MockDataGenerator()

# ============================================================================
# 数据存储
# ============================================================================
class DataStore:
    def __init__(self):
        self.market_signals = []      # Ziwox市场信号
        self.forex_rates = {}         # Alpha Vantage汇率
        self.economic_events = []     # 宏观经济日历事件
        self.daily_analysis = ""      # 每日综合分析
        self.last_updated = None
    
    def update_all(self, signals, rates, events, analysis):
        self.market_signals = signals
        self.forex_rates = rates
        self.economic_events = events
        self.daily_analysis = analysis
        self.last_updated = datetime.now()

store = DataStore()

# ============================================================================
# 模块1：实时市场信号获取（Ziwox）
# ============================================================================
def fetch_market_signals_ziwox():
    """从Ziwox获取市场交易信号数据"""
    if not config.ziwox_api_key:
        logger.error("Ziwox API密钥为空")
        return []
    
    all_signals = []
    
    for pair in config.ziwox_pairs:
        try:
            params = {
                'expn': 'ziwoxuser',
                'apikey': config.ziwox_api_key,
                'apitype': 'json',
                'pair': pair
            }
            
            logger.info(f"正在从Ziwox获取 {pair.upper()} 的市场信号...")
            response = requests.get(
                config.ziwox_api_url,
                params=params,
                headers={'User-Agent': 'MacroEconomicAI/1.0'},
                timeout=10
            )
            
            if response.status_code == 200:
                data_list = response.json()
                
                if isinstance(data_list, list) and len(data_list) > 0:
                    raw_data = data_list[0]
                    
                    signal = {
                        'pair': pair.upper(),
                        'last_price': raw_data.get('Last Price', 'N/A'),
                        'fundamental_bias': raw_data.get('Fundamental Bias', 'Neutral'),
                        'fundamental_power': raw_data.get('Fundamental Power', '--'),
                        'ai_bullish_forecast': raw_data.get('AI Bullish Forecast', '50'),
                        'ai_bearish_forecast': raw_data.get('AI Bearish Forecast', '50'),
                        'd1_trend': raw_data.get('D1 Trend', 'NEUTRAL'),
                        'd1_rsi': raw_data.get('D1 RSI', '50'),
                        'retail_long_ratio': raw_data.get('Retail Long Ratio', '50%'),
                        'retail_short_ratio': raw_data.get('Retail Short Ratio', '50%'),
                        'support_levels': raw_data.get('supports', '').split()[:3],
                        'resistance_levels': raw_data.get('resistance', '').split()[:3],
                        'pivot_points': raw_data.get('pivot', '').split()[:1],
                        'risk_sentiment': raw_data.get('Risk Sentiment', 'Neutral'),
                        'source': 'Ziwox',
                        'fetched_at': datetime.now().isoformat()
                    }
                    all_signals.append(signal)
                    logger.info(f"  成功解析 {pair.upper()} 的市场信号")
                    
            else:
                logger.warning(f"  请求 {pair.upper()} 数据失败，状态码: {response.status_code}")
            
            time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"  获取 {pair} 数据时出错: {e}")
    
    logger.info(f"Ziwox市场信号获取完成，共得到 {len(all_signals)} 个货币对数据")
    return all_signals

# ============================================================================
# 模块2：实时汇率获取（Alpha Vantage）
# ============================================================================
def fetch_forex_rates_alpha_vantage():
    """从Alpha Vantage获取实时汇率"""
    if not config.alpha_vantage_key:
        logger.warning("Alpha Vantage密钥为空，跳过汇率获取")
        return {}

    rates = {}
    logger.info(f"开始从Alpha Vantage获取 {len(config.watch_currency_pairs)} 个品种汇率...")

    try:
        fx = ForeignExchange(key=config.alpha_vantage_key)

        for pair in config.watch_currency_pairs:
            try:
                if pair in config.av_special_pairs:
                    from_cur, to_cur = config.av_special_pairs[pair]
                    logger.info(f"  正在获取特殊品种 {pair}...")
                else:
                    from_cur = pair[:3]
                    to_cur = pair[3:]

                data, _ = fx.get_currency_exchange_rate(
                    from_currency=from_cur,
                    to_currency=to_cur
                )

                if data and '5. Exchange Rate' in data:
                    rates[pair] = {
                        'rate': float(data['5. Exchange Rate']),
                        'bid': data.get('8. Bid Price', data['5. Exchange Rate']),
                        'ask': data.get('9. Ask Price', data['5. Exchange Rate']),
                        'last_refreshed': data.get('6. Last Refreshed', datetime.now().isoformat()),
                        'source': 'Alpha Vantage'
                    }
                    logger.info(f"    ✓ 成功获取 {pair}: {rates[pair]['rate']}")
                else:
                    raise ValueError(f"No rate returned for {pair}")

                time.sleep(0.3)  # 避免API限制

            except Exception as e:
                logger.warning(f"    Alpha Vantage 获取 {pair} 失败: {str(e)[:100]}")
                # 尝试从其他信号源补充（这里可以扩展）
                
        logger.info(f"汇率获取完成，共得到 {len(rates)} 个品种数据")
        return rates

    except Exception as e:
        logger.error(f"Alpha Vantage API整体调用失败: {e}")
        return {}

# ============================================================================
# 模块3：宏观经济日历获取（TradingEconomics或模拟）
# ============================================================================
def fetch_economic_calendar():
    """获取今日宏观经济日历事件"""
    if config.use_mock:
        return mock_gen.generate_events()
    
    try:
        logger.info("正在从TradingEconomics获取宏观经济日历...")
        
        # 配置TradingEconomics
        te.login(config.te_key)
        
        # 获取今日事件
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 获取重要事件
        events = te.getCalendarData(
            country='all',
            importance='1,2,3',
            initDate=today,
            output_type='df'
        )
        
        if events is not None and not events.empty:
            events_data = events.to_dict('records')
            formatted_events = []
            
            for i, event in enumerate(events_data):
                formatted_events.append({
                    "id": i + 1,
                    "date": event.get('Date', today),
                    "time": event.get('Time', '00:00'),
                    "country": event.get('Country', 'Unknown'),
                    "name": event.get('Event', 'Unknown Event'),
                    "forecast": str(event.get('Forecast', 'N/A')),
                    "previous": str(event.get('Previous', 'N/A')),
                    "importance": int(event.get('Importance', 1)),
                    "currency": event.get('Currency', 'USD'),
                    "actual": str(event.get('Actual', 'N/A')),
                    "description": event.get('Description', '')
                })
            
            logger.info(f"成功获取 {len(formatted_events)} 个宏观经济事件")
            return formatted_events
        else:
            logger.warning("TradingEconomics返回空数据，使用模拟数据")
            return mock_gen.generate_events()
            
    except Exception as e:
        logger.error(f"TradingEconomics API失败: {e}")
        logger.info("切换到模拟数据模式")
        return mock_gen.generate_events()

# ============================================================================
# 模块4：AI综合分析生成
# ============================================================================
def generate_comprehensive_analysis(signals, rates, events):
    """生成综合AI分析：结合市场信号、汇率和宏观事件"""
    if not config.enable_ai or not config.openai_api_key:
        return "AI分析功能未启用"
    
    try:
        # 准备市场概况
        market_summary = []
        for signal in signals[:5]:  # 取前5个主要品种
            pair = signal.get('pair', '')
            rate = rates.get(pair, {}).get('rate', 'N/A') if rates else 'N/A'
            trend = signal.get('d1_trend', 'NEUTRAL')
            bias = signal.get('fundamental_bias', 'Neutral')
            market_summary.append(f"{pair}: {rate} ({trend}, {bias})")
        
        # 准备宏观事件概况
        event_summary = []
        important_events = [e for e in events if e.get('importance', 1) >= 2]
        for event in important_events[:5]:  # 取前5个重要事件
            event_summary.append(f"{event['country']}-{event['name']}: {event['forecast']}")
        
        # 构建AI提示词
        prompt = f"""作为资深宏观策略分析师，请基于以下三方面数据提供今日综合分析：

一、市场信号概况：
{chr(10).join(market_summary)}

二、重要宏观经济事件（今日）：
{chr(10).join(event_summary) if event_summary else "今日无重要宏观事件"}

三、监控品种清单：
{', '.join(config.watch_currency_pairs)}

---
请提供一份专业、简洁的每日宏观交易报告，包含：

📅 **宏观主线**：总结今日最重要的宏观经济主题与市场焦点

📊 **市场预期**：基于日历事件，分析哪些数据可能超预期/低于预期

💱 **货币对展望**：
- 美元指数：受哪些事件影响，关键位
- EUR/USD：关键驱动因素与技术位
- USD/JPY：关键驱动因素与技术位
- 贵金属（XAUUSD/XAGUSD）：与美元/实际利率关联性
- 加密货币（BTCUSD）：独立驱动因素

⚠️ **风险提示**：今日主要交易风险（数据意外、央行讲话、流动性等）

🎯 **交易策略建议**：1-2条明确的交易思路（品种、方向、关键位）

要求：分析逻辑清晰，有数据支撑，直接服务于今日交易决策。字数控制在400-500字。"""
        
        # 调用AI API
        headers = {
            "Authorization": f"Bearer {config.openai_api_key.strip()}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{config.openai_base_url}/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "你是顶尖的宏观策略分析师，擅长结合宏观经济事件、市场信号和技术分析提供清晰的交易指导。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.4
            },
            timeout=40
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"AI API错误: {response.status_code}")
            return f"【AI分析生成失败，HTTP {response.status_code}】"
            
    except Exception as e:
        logger.error(f"生成综合分析时出错: {e}")
        return "综合分析生成异常"

# ============================================================================
# 定时任务：整合所有数据源
# ============================================================================
scheduler = BackgroundScheduler()

def scheduled_data_update():
    """定时更新所有数据：市场信号 + 汇率 + 宏观事件"""
    try:
        logger.info("="*60)
        logger.info(f"开始执行数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 并行获取数据
        def get_market_data():
            signals = fetch_market_signals_ziwox()
            rates = fetch_forex_rates_alpha_vantage()
            return signals, rates
        
        def get_economic_data():
            return fetch_economic_calendar()
        
        # 启动线程
        market_thread = threading.Thread(target=lambda: globals().update(market_result=get_market_data()))
        economic_thread = threading.Thread(target=lambda: globals().update(economic_result=get_economic_data()))
        
        market_thread.start()
        economic_thread.start()
        market_thread.join()
        economic_thread.join()
        
        # 获取结果
        signals, rates = market_result
        events = economic_result
        
        # 2. 生成AI综合分析
        analysis = generate_comprehensive_analysis(signals, rates, events)
        
        # 3. 存储数据
        store.update_all(signals, rates, events, analysis)
        
        logger.info(f"数据更新完成:")
        logger.info(f"  - 市场信号: {len(signals)} 个")
        logger.info(f"  - 汇率数据: {len(rates)} 个")
        logger.info(f"  - 宏观事件: {len(events)} 个")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"定时任务失败: {e}", exc_info=True)

# 定时任务配置
scheduler.add_job(scheduled_data_update, 'interval', minutes=60)  # 每小时更新
scheduler.add_job(scheduled_data_update, 'cron', hour=7, minute=0)   # 早上7点
scheduler.add_job(scheduled_data_update, 'cron', hour=16, minute=0)  # 下午4点

scheduler.start()

# ============================================================================
# Flask路由
# ============================================================================

@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "service": "宏观经济AI分析工具",
        "version": "2.0 - 完整版",
        "data_sources": ["Ziwox市场信号", "Alpha Vantage汇率", "TradingEconomics宏观日历"],
        "last_updated": store.last_updated.isoformat() if store.last_updated else None,
        "endpoints": {
            "status": "/api/status",
            "events": "/api/events/today",
            "market_signals": "/api/market/signals",
            "forex_rates": "/api/forex/rates",
            "analysis": "/api/analysis/daily",
            "refresh": "/api/refresh",
            "overview": "/api/overview"
        }
    })

@app.route('/api/status')
def get_api_status():
    """服务状态检查"""
    return jsonify({
        "status": "healthy",
        "mode": "real-time",
        "ai_enabled": config.enable_ai,
        "data_summary": {
            "market_signals": len(store.market_signals),
            "forex_rates": len(store.forex_rates),
            "economic_events": len(store.economic_events)
        },
        "last_updated": store.last_updated.isoformat() if store.last_updated else None
    })

@app.route('/api/events/today')
def get_today_events():
    """获取今日宏观经济日历事件"""
    events = store.economic_events
    if not events:
        scheduled_data_update()
        events = store.economic_events
    
    return jsonify({
        "status": "success",
        "data": events,
        "count": len(events),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "important_events": len([e for e in events if e.get('importance', 1) >= 2])
    })

@app.route('/api/market/signals')
def get_market_signals():
    """获取市场信号数据"""
    signals = store.market_signals
    if not signals:
        scheduled_data_update()
        signals = store.market_signals
    
    return jsonify({
        "status": "success",
        "data": signals,
        "count": len(signals),
        "pairs": config.watch_currency_pairs
    })

@app.route('/api/forex/rates')
def get_forex_rates():
    """获取实时汇率"""
    rates = store.forex_rates
    return jsonify({
        "status": "success",
        "data": rates,
        "count": len(rates)
    })

@app.route('/api/analysis/daily')
def get_daily_analysis():
    """获取每日AI综合分析"""
    analysis = store.daily_analysis
    if not analysis:
        scheduled_data_update()
        analysis = store.daily_analysis
    
    return jsonify({
        "status": "success",
        "analysis": analysis,
        "generated_at": datetime.now().isoformat(),
        "data_sources_used": 3  # 市场信号 + 汇率 + 宏观事件
    })

@app.route('/api/overview')
def get_overview():
    """获取综合概览（所有数据）"""
    return jsonify({
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "market_signals": {
            "count": len(store.market_signals),
            "sample": store.market_signals[:3] if store.market_signals else []
        },
        "forex_rates": {
            "count": len(store.forex_rates),
            "sample": {k: store.forex_rates[k] for k in list(store.forex_rates.keys())[:3]} if store.forex_rates else {}
        },
        "economic_events": {
            "count": len(store.economic_events),
            "important": [e for e in store.economic_events if e.get('importance', 1) >= 2][:3]
        },
        "daily_analysis_preview": store.daily_analysis[:200] + "..." if store.daily_analysis else "无"
    })

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """手动刷新数据"""
    scheduled_data_update()
    return jsonify({
        "status": "success",
        "message": "数据刷新已触发",
        "timestamp": datetime.now().isoformat()
    })

# ============================================================================
# 错误处理
# ============================================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "请求的资源不存在",
        "available_routes": [
            "/",
            "/api/status",
            "/api/events/today",
            "/api/market/signals",
            "/api/forex/rates",
            "/api/analysis/daily",
            "/api/overview",
            "/api/refresh"
        ]
    }), 404

# ============================================================================
# 启动应用
# ============================================================================
if __name__ == '__main__':
    logger.info("启动宏观经济AI分析工具 (完整版)...")
    logger.info("="*60)
    logger.info("数据源配置:")
    logger.info(f"  - 市场信号: Ziwox")
    logger.info(f"  - 实时汇率: Alpha Vantage")
    logger.info(f"  - 宏观日历: TradingEconomics" + (" (模拟模式)" if config.use_mock else ""))
    logger.info(f"  - AI分析: laozhang.ai")
    logger.info("="*60)
    logger.info(f"监控品种: {config.watch_currency_pairs}")
    logger.info(f"AI功能: {'已启用' if config.enable_ai else '已禁用'}")
    
    # 首次启动时获取数据
    try:
        scheduled_data_update()
    except Exception as e:
        logger.error(f"首次数据获取失败: {e}")
    
    # 运行Flask应用
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)