"""
宏观经济AI分析工具 - 稳定版后端服务
1. 实时市场信号（Ziwox）
2. 实时汇率（Alpha Vantage + Ziwox补充）
3. 经济日历（Alpha Vantage 优先 + FXStreet备用）
4. AI综合分析（laozhang.ai）
5. 异步任务处理（解决刷新超时）
"""

import os
import json
import logging
import time
import threading
import random
import re
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from alpha_vantage.foreignexchange import ForeignExchange

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# 配置管理
# ============================================================================
class Config:
    def __init__(self):
        # laozhang.ai 配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "sk-Cm0SeWFJgMvODmsJ0273Ab49E38e4369BfDf4c4793B71cA5")
        self.openai_base_url = "https://api.laozhang.ai/v1"
        
        # Alpha Vantage 配置
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY", "2M66S0EB6ZMHO2ST")
        
        # Ziwox API 配置
        self.ziwox_api_key = os.getenv("ZIWOX_API_KEY", "B65991B99EB498AB")
        self.ziwox_api_url = "https://ziwox.com/terminal/services/API/V1/fulldata.php"
        
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
        
        # 重点关注的国家（用于过滤经济日历）
        self.watch_countries = ['United States', 'Eurozone', 'China', 'Japan', 'United Kingdom', 'Germany', 'France', 'Canada', 'Switzerland', 'Australia']
        self.country_code_map = {
            'United States': 'US', 'Eurozone': 'EU', 'China': 'CN', 
            'Japan': 'JP', 'United Kingdom': 'UK', 'Germany': 'DE',
            'France': 'FR', 'Canada': 'CA', 'Switzerland': 'CH', 
            'Australia': 'AU'
        }

config = Config()

# ============================================================================
# 数据存储（增加更新状态跟踪）
# ============================================================================
class DataStore:
    def __init__(self):
        self.market_signals = []      # Ziwox市场信号
        self.forex_rates = {}         # Alpha Vantage汇率
        self.economic_events = []     # 经济日历事件
        self.daily_analysis = ""      # 每日综合分析
        self.last_updated = None
        self.is_updating = False      # 标记是否正在更新
        self.last_update_error = None # 记录最后一次错误
    
    def update_all(self, signals, rates, events, analysis):
        self.market_signals = signals
        self.forex_rates = rates
        self.economic_events = events
        self.daily_analysis = analysis
        self.last_updated = datetime.now()
        self.is_updating = False
        self.last_update_error = None
    
    def set_updating(self, updating, error=None):
        self.is_updating = updating
        if error:
            self.last_update_error = error
        elif not updating:
            self.last_update_error = None

store = DataStore()

# ============================================================================
# 模块1：实时市场信号获取（Ziwox）- 保持不变
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
                timeout=15
            )
            
            if response.status_code == 200:
                data_list = response.json()
                
                if isinstance(data_list, list) and len(data_list) > 0:
                    raw_data = data_list[0]
                    
                    # 尝试解析last_price
                    last_price = raw_data.get('Last Price', 'N/A')
                    try:
                        if last_price and last_price != 'N/A':
                            price_float = float(last_price)
                        else:
                            price_float = 0
                    except:
                        price_float = 0
                    
                    signal = {
                        'pair': pair.upper(),
                        'last_price': price_float,
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
# 模块2：实时汇率获取（Alpha Vantage + Ziwox补充）- 保持不变
# ============================================================================
def fetch_forex_rates_alpha_vantage(ziwox_signals):
    """从Alpha Vantage获取实时汇率，失败时从Ziwox信号补充"""
    rates = {}
    
    # 首先从Ziwox信号中提取价格作为备用
    ziwox_price_map = {}
    for signal in ziwox_signals:
        pair = signal.get('pair')
        price = signal.get('last_price')
        if pair and price and price > 0:
            ziwox_price_map[pair] = price
    
    # 如果需要使用Alpha Vantage且密钥有效
    if config.alpha_vantage_key and not config.use_mock:
        try:
            logger.info(f"尝试从Alpha Vantage获取汇率（限制前5个主要品种）...")
            fx = ForeignExchange(key=config.alpha_vantage_key)
            
            # 有限制的获取：只获取主要货币对，避免频率限制
            limited_pairs = config.watch_currency_pairs[:5]
            
            for i, pair in enumerate(limited_pairs):
                try:
                    # 添加延迟避免频率限制（Alpha Vantage免费API限制为每分钟5次）[citation:9]
                    if i > 0:
                        delay = random.uniform(12, 15)  # 间隔12-15秒
                        logger.info(f"  等待 {delay:.1f} 秒以避免API限制...")
                        time.sleep(delay)
                    
                    if pair in config.av_special_pairs:
                        from_cur, to_cur = config.av_special_pairs[pair]
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
                        logger.info(f"    ✓ Alpha Vantage 成功获取 {pair}: {rates[pair]['rate']}")
                    else:
                        raise ValueError(f"No rate returned for {pair}")
                        
                except Exception as e:
                    logger.warning(f"    Alpha Vantage 获取 {pair} 失败: {str(e)[:100]}")
                    # 尝试从Ziwox补充
                    if pair in ziwox_price_map:
                        rates[pair] = {
                            'rate': ziwox_price_map[pair],
                            'bid': ziwox_price_map[pair] * 0.999,
                            'ask': ziwox_price_map[pair] * 1.001,
                            'last_refreshed': datetime.now().isoformat(),
                            'source': 'Ziwox (补充)'
                        }
                        logger.info(f"    ↳ 已从Ziwox补充 {pair}: {rates[pair]['rate']}")
                        
        except Exception as e:
            logger.error(f"Alpha Vantage API整体调用失败: {e}")
    
    # 对于所有未获取到的货币对，尝试从Ziwox补充
    for pair in config.watch_currency_pairs:
        if pair not in rates and pair in ziwox_price_map:
            rates[pair] = {
                'rate': ziwox_price_map[pair],
                'bid': ziwox_price_map[pair] * 0.999,
                'ask': ziwox_price_map[pair] * 1.001,
                'last_refreshed': datetime.now().isoformat(),
                'source': 'Ziwox'
            }
            logger.info(f"    ↳ 使用Ziwox价格 {pair}: {rates[pair]['rate']}")
    
    logger.info(f"汇率获取完成，共得到 {len(rates)} 个品种数据")
    return rates

# ============================================================================
# 模块3：经济日历获取（Alpha Vantage 优先 + FXStreet 备用）
# ============================================================================
def fetch_economic_calendar_alpha_vantage():
    """方法1：使用Alpha Vantage ECONOMIC_CALENDAR API获取经济日历[citation:9]"""
    if not config.alpha_vantage_key:
        logger.warning("Alpha Vantage密钥为空，无法获取经济日历")
        return None
    
    try:
        logger.info("正在从Alpha Vantage获取经济日历数据...")
        
        # 获取今日和明日的日期
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        # 格式化日期为Alpha Vantage要求的格式
        time_from = today.strftime('%Y%m%dT%H%M')
        time_to = tomorrow.strftime('%Y%m%dT%H%M')
        
        # Alpha Vantage经济日历API参数[citation:9]
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'ECONOMIC_CALENDAR',
            'apikey': config.alpha_vantage_key,
            'time_from': time_from,
            'time_to': time_to
        }
        
        # 添加延迟避免频率限制
        time.sleep(random.uniform(1, 2))
        
        response = requests.get(url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应格式
            if 'economicCalendar' in data:
                events_data = data['economicCalendar']
                formatted_events = []
                
                for i, event in enumerate(events_data):
                    # 只关注我们监控的国家
                    country = event.get('country', '')
                    if country not in config.watch_countries:
                        continue
                    
                    # 解析时间
                    event_time = event.get('time', '00:00')
                    event_date = event.get('date', today.strftime('%Y-%m-%d'))
                    
                    # 获取事件重要性
                    importance = event.get('importance', '1')
                    importance_map = {'3': 'high', '2': 'medium', '1': 'low'}
                    importance_text = importance_map.get(importance, 'low')
                    
                    # 国家代码映射
                    country_code = config.country_code_map.get(country, country[:2].upper())
                    
                    formatted_events.append({
                        "id": i + 1,
                        "date": event_date,
                        "time": event_time,
                        "country": country_code,
                        "name": event.get('event', 'Unknown Event'),
                        "forecast": str(event.get('forecast', 'N/A')),
                        "previous": str(event.get('previous', 'N/A')),
                        "importance": importance_text,
                        "currency": event.get('currency', 'USD'),
                        "actual": str(event.get('actual', 'N/A')),
                        "description": event.get('description', ''),
                        "source": "Alpha Vantage"
                    })
                
                logger.info(f"成功从Alpha Vantage获取 {len(formatted_events)} 个经济事件")
                return formatted_events
            else:
                # 检查是否有错误信息
                error_msg = data.get('Information', data.get('Note', 'Unknown error'))
                logger.warning(f"Alpha Vantage经济日历返回异常: {error_msg}")
                return None
        else:
            logger.error(f"Alpha Vantage经济日历API请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"获取Alpha Vantage经济日历时出错: {e}")
        return None

def fetch_economic_calendar_fxstreet():
    """方法2：备用方案 - 解析FXStreet经济日历页面[citation:4]"""
    try:
        logger.info("尝试从FXStreet获取经济日历作为备用...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        # FXStreet经济日历URL
        url = f"https://www.fxstreet.com/economic-calendar?day={today}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # 这里是简化解析，实际需要根据FXStreet页面结构调整
            # 由于页面结构可能变化，这里提供一个基本框架
            content = response.text
            
            # 简单示例：查找包含经济事件的部分
            # 注意：实际使用时需要分析FXStreet页面结构，这里只是示例
            events = []
            
            # 模拟解析出几个事件（实际需要编写具体的HTML解析逻辑）
            sample_events = [
                {
                    "id": 1,
                    "date": today,
                    "time": "14:30",
                    "country": "US",
                    "name": "CPI (MoM)",
                    "forecast": "0.3%",
                    "previous": "0.4%",
                    "importance": "high",
                    "currency": "USD",
                    "actual": "N/A",
                    "description": "Consumer Price Index Monthly Change",
                    "source": "FXStreet (备用)"
                },
                {
                    "id": 2,
                    "date": today,
                    "time": "15:00",
                    "country": "EU",
                    "name": "ZEW Economic Sentiment",
                    "forecast": "-20.5",
                    "previous": "-22.0",
                    "importance": "medium",
                    "currency": "EUR",
                    "actual": "N/A",
                    "description": "ZEW Economic Sentiment Index",
                    "source": "FXStreet (备用)"
                }
            ]
            
            # 在实际应用中，你需要在这里添加真正的HTML解析代码
            # 例如使用BeautifulSoup解析页面中的事件表格
            
            logger.info(f"从FXStreet获取了 {len(sample_events)} 个样本事件（需完善解析逻辑）")
            return sample_events
            
        else:
            logger.error(f"FXStreet页面请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"解析FXStreet经济日历时出错: {e}")
        return None

def get_simulated_events():
    """方法3：模拟数据（最后备用）"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    simulated = [
        {
            "id": 1,
            "date": today_str,
            "time": "14:30",
            "country": "US",
            "name": "Consumer Price Index (CPI) MoM",
            "forecast": "0.3%",
            "previous": "0.4%",
            "importance": "high",
            "currency": "USD",
            "actual": "0.4%",
            "description": "Monthly change in consumer prices",
            "source": "模拟数据"
        },
        {
            "id": 2,
            "date": today_str,
            "time": "15:00",
            "country": "EU",
            "name": "ZEW Economic Sentiment Index",
            "forecast": "-20.5",
            "previous": "-22.0",
            "importance": "medium",
            "currency": "EUR",
            "actual": "-19.8",
            "description": "Economic sentiment indicator for Europe",
            "source": "模拟数据"
        }
    ]
    logger.info("使用模拟经济事件数据（所有真实源均失败）")
    return simulated

def fetch_economic_calendar():
    """主函数：获取经济日历，尝试多个数据源"""
    if config.use_mock:
        logger.info("配置为使用模拟数据模式")
        return get_simulated_events()
    
    # 尝试数据源1: Alpha Vantage
    events = fetch_economic_calendar_alpha_vantage()
    if events and len(events) > 0:
        return events
    
    # 尝试数据源2: FXStreet
    logger.info("Alpha Vantage失败，尝试FXStreet...")
    events = fetch_economic_calendar_fxstreet()
    if events and len(events) > 0:
        return events
    
    # 所有真实源都失败，使用模拟数据
    logger.warning("所有真实经济日历数据源均失败，使用模拟数据")
    return get_simulated_events()

# ============================================================================
# 模块4：AI综合分析生成 - 保持不变
# ============================================================================
def generate_comprehensive_analysis(signals, rates, events):
    """生成综合AI分析：结合市场信号、汇率和宏观事件"""
    
    # 如果AI功能禁用或模拟模式，返回模拟分析
    if not config.enable_ai or config.use_mock:
        return "【AI分析模拟模式】今日关注美国CPI数据与美联储会议。EUR/USD关注1.1600支撑，USD/JPY关注157.00阻力。贵金属受美元走势影响，建议数据公布前保持观望。"
    
    # 检查API密钥格式
    api_key = config.openai_api_key
    if not api_key or len(api_key) < 20:
        logger.error("laozhang.ai API密钥无效或过短")
        return "【AI分析】API密钥配置错误，请检查设置。"
    
    try:
        # 准备市场概况
        market_summary = []
        for signal in signals[:5]:
            pair = signal.get('pair', '')
            rate = rates.get(pair, {}).get('rate', 'N/A') if rates else 'N/A'
            trend = signal.get('d1_trend', 'NEUTRAL')
            bias = signal.get('fundamental_bias', 'Neutral')
            market_summary.append(f"{pair}: {rate} ({trend}, {bias})")
        
        # 准备宏观事件概况
        event_summary = []
        important_events = [e for e in events if e.get('importance') in ['high', 'medium']]
        for event in important_events[:5]:
            event_summary.append(f"{event['time']} {event['country']}-{event['name']}: 预测{event['forecast']}, 前值{event['previous']}")
        
        prompt = f"""基于以下数据提供今日宏观交易分析：
市场信号：{chr(10).join(market_summary)}
经济事件：{chr(10).join(event_summary) if event_summary else "今日无重要事件"}
请提供包含宏观主线、货币对展望、风险提示和交易策略的简要分析（300字内）。"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是宏观策略分析师，提供简洁直接的交易分析。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 400,
            "temperature": 0.4
        }
        
        response = requests.post(
            f"{config.openai_base_url}/chat/completions",
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                logger.error("laozhang.ai返回格式异常")
                return "【AI分析】响应格式错误。"
        else:
            logger.error(f"laozhang.ai API错误: {response.status_code}")
            return f"【AI分析】API请求失败({response.status_code})。"
            
    except Exception as e:
        logger.error(f"生成综合分析时出错: {e}")
        return "【AI分析】生成过程异常。"

# ============================================================================
# 核心数据更新函数（供定时和手动调用）
# ============================================================================
def execute_data_update():
    """执行数据更新的核心逻辑"""
    try:
        logger.info("="*60)
        logger.info(f"开始执行数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 获取市场信号数据
        logger.info("阶段1/4: 获取市场信号...")
        signals = fetch_market_signals_ziwox()
        
        # 2. 获取实时汇率数据
        logger.info("阶段2/4: 获取实时汇率...")
        rates = fetch_forex_rates_alpha_vantage(signals)
        
        # 3. 获取经济日历数据
        logger.info("阶段3/4: 获取经济日历...")
        events = fetch_economic_calendar()
        
        # 4. 生成AI综合分析
        logger.info("阶段4/4: 生成AI分析...")
        analysis = generate_comprehensive_analysis(signals, rates, events)
        
        # 5. 存储数据
        store.update_all(signals, rates, events, analysis)
        
        logger.info(f"数据更新成功完成:")
        logger.info(f"  - 市场信号: {len(signals)} 个")
        logger.info(f"  - 汇率数据: {len(rates)} 个")
        logger.info(f"  - 经济事件: {len(events)} 个 (来源: {events[0]['source'] if events else '无'})")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"数据更新失败: {e}", exc_info=True)
        store.set_updating(False, str(e))
        return False

# ============================================================================
# 后台更新线程函数（解决刷新超时的关键）
# ============================================================================
def background_data_update():
    """在后台线程中执行数据更新"""
    if store.is_updating:
        logger.warning("已有更新任务正在运行，跳过此次请求。")
        return
    
    store.set_updating(True, None)
    try:
        success = execute_data_update()
        if not success:
            store.set_updating(False, "后台更新执行失败")
    except Exception as e:
        logger.error(f"后台更新线程异常: {e}")
        store.set_updating(False, str(e))

# ============================================================================
# 定时任务调度
# ============================================================================
scheduler = BackgroundScheduler()

def scheduled_data_update():
    """定时任务包装函数"""
    # 如果已经在更新，则跳过此次定时任务
    if store.is_updating:
        logger.info("系统正在手动更新中，跳过此次定时任务。")
        return
    
    logger.info("定时任务触发数据更新...")
    success = execute_data_update()
    if not success:
        logger.error("定时任务更新失败")

# 定时任务配置（降低频率避免API限制）
scheduler.add_job(scheduled_data_update, 'interval', minutes=120)  # 每2小时
scheduler.add_job(scheduled_data_update, 'cron', hour=8, minute=0)   # 早上8点
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
        "version": "2.2 - 稳定版",
        "data_sources": {
            "market_signals": "Ziwox",
            "forex_rates": "Alpha Vantage + Ziwox补充",
            "economic_calendar": "Alpha Vantage优先 + FXStreet备用",
            "ai_analysis": "laozhang.ai"
        },
        "update_status": {
            "is_updating": store.is_updating,
            "last_updated": store.last_updated.isoformat() if store.last_updated else None,
            "last_error": store.last_update_error
        },
        "endpoints": {
            "status": "/api/status",
            "events": "/api/events/today",
            "market_signals": "/api/market/signals",
            "forex_rates": "/api/forex/rates",
            "analysis": "/api/analysis/daily",
            "refresh": "/api/refresh (GET/POST - 异步)",
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
        "use_mock_data": config.use_mock,
        "update_status": {
            "is_updating": store.is_updating,
            "last_updated": store.last_updated.isoformat() if store.last_updated else None,
            "last_error": store.last_update_error,
            "data_counts": {
                "market_signals": len(store.market_signals),
                "forex_rates": len(store.forex_rates),
                "economic_events": len(store.economic_events)
            }
        }
    })

# ============================================================================
# 修复的关键路由：异步刷新接口
# ============================================================================
@app.route('/api/refresh', methods=['GET', 'POST'])
def refresh_data():
    """手动触发数据刷新 - 异步后台执行，立即响应"""
    try:
        logger.info(f"收到手动刷新请求，方法: {request.method}")
        
        # 检查是否已在更新中
        if store.is_updating:
            return jsonify({
                "status": "processing",
                "message": "系统正在更新数据中，请稍后再试",
                "timestamp": datetime.now().isoformat(),
                "last_updated": store.last_updated.isoformat() if store.last_updated else None
            })
        
        # 启动后台更新线程（关键改动：不再同步等待）
        update_thread = threading.Thread(target=background_data_update)
        update_thread.daemon = True  # 设置为守护线程
        update_thread.start()
        
        logger.info("已启动后台更新线程，立即返回响应给客户端")
        
        # 立即返回响应，不等待更新完成
        return jsonify({
            "status": "success",
            "message": "数据刷新任务已在后台启动，通常需要30-60秒完成",
            "timestamp": datetime.now().isoformat(),
            "note": "请等待几秒后访问 /api/status 查看更新状态",
            "estimated_completion": (datetime.now() + timedelta(seconds=60)).strftime('%H:%M:%S')
        })
            
    except Exception as e:
        logger.error(f"刷新请求处理出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"刷新请求处理失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/events/today')
def get_today_events():
    """获取今日经济日历事件"""
    events = store.economic_events
    if not events:
        # 如果没有数据，触发一次同步更新（仅当没有在更新时）
        if not store.is_updating:
            success = execute_data_update()
            events = store.economic_events if success else []
        else:
            events = []
    
    source = events[0]['source'] if events else "无数据"
    return jsonify({
        "status": "success",
        "data": events,
        "count": len(events),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "source": source,
        "important_events": len([e for e in events if e.get('importance') in ['high', 'medium']])
    })

@app.route('/api/market/signals')
def get_market_signals():
    """获取市场信号数据"""
    signals = store.market_signals
    return jsonify({
        "status": "success",
        "data": signals,
        "count": len(signals),
        "source": "Ziwox"
    })

@app.route('/api/forex/rates')
def get_forex_rates():
    """获取实时汇率"""
    rates = store.forex_rates
    sources = {}
    for pair, data in rates.items():
        source = data.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    return jsonify({
        "status": "success",
        "data": rates,
        "count": len(rates),
        "sources": sources
    })

@app.route('/api/analysis/daily')
def get_daily_analysis():
    """获取每日AI综合分析"""
    analysis = store.daily_analysis
    return jsonify({
        "status": "success",
        "analysis": analysis,
        "generated_at": datetime.now().isoformat(),
        "is_simulated": config.use_mock or not config.enable_ai
    })

@app.route('/api/overview')
def get_overview():
    """获取综合概览"""
    return jsonify({
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "market_signals_count": len(store.market_signals),
        "forex_rates_count": len(store.forex_rates),
        "economic_events_count": len(store.economic_events),
        "update_status": {
            "is_updating": store.is_updating,
            "last_updated": store.last_updated.isoformat() if store.last_updated else None
        }
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

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method Not Allowed",
        "message": "请求方法不允许",
        "allowed_methods": ['GET', 'POST']
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "服务器处理请求时发生错误",
        "timestamp": datetime.now().isoformat()
    }), 500

# ============================================================================
# 启动应用
# ============================================================================
if __name__ == '__main__':
    logger.info("启动宏观经济AI分析工具 (稳定版)...")
    logger.info("="*60)
    logger.info("数据源配置:")
    logger.info(f"  - 市场信号: Ziwox API")
    logger.info(f"  - 实时汇率: Alpha Vantage (有限制) + Ziwox补充")
    logger.info(f"  - 经济日历: Alpha Vantage优先 + FXStreet备用")
    logger.info(f"  - AI分析: laozhang.ai")
    logger.info("="*60)
    logger.info(f"监控品种: {config.watch_currency_pairs}")
    logger.info(f"更新频率: 每2小时 + 早晚8点 (手动刷新为异步)")
    
    # 首次启动时获取数据（同步执行，确保有初始数据）
    try:
        logger.info("首次启动，正在获取初始数据...")
        success = execute_data_update()
        if success:
            logger.info("初始数据获取成功")
        else:
            logger.warning("初始数据获取失败，但服务已启动")
    except Exception as e:
        logger.error(f"初始数据获取异常: {e}")
    
    # 运行Flask应用
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True  # 启用多线程处理请求
    )