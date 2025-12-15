"""
宏观经济AI分析工具 - 完整版本（使用market-calendar-tool实时抓取）
"""

import os
import json
import logging
import time
import threading
import random
import re
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from alpha_vantage.foreignexchange import ForeignExchange
from bs4 import BeautifulSoup
import pandas as pd

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

        # Forex Factory 网址
        self.forex_factory_url = "https://www.forexfactory.com/calendar?day={}"

config = Config()

# ============================================================================
# 数据存储
# ============================================================================
class DataStore:
    def __init__(self):
        self.market_signals = []      # Ziwox市场信号
        self.forex_rates = {}         # Alpha Vantage汇率
        self.economic_events = []     # 财经日历事件
        self.daily_analysis = ""      # 每日AI综合分析
        self.last_updated = None
        self.is_updating = False
        self.last_update_error = None
        self.individual_ai_analysis = {}  # 存储每个事件的AI分析
        self.summary_sections = {     # Summary页面的各个部分
            "market": "",
            "events": "",
            "outlook": "",
            "strategy": "",
            "risks": ""
        }

    def update_all(self, signals, rates, events, analysis, summary_sections=None, individual_analysis=None):
        self.market_signals = signals
        self.forex_rates = rates
        self.economic_events = events
        self.daily_analysis = analysis
        if summary_sections:
            self.summary_sections = summary_sections
        if individual_analysis:
            self.individual_ai_analysis = individual_analysis
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
# 模块1：实时市场信号获取 (Ziwox) - 保持不变
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
# 模块2：实时汇率获取 (Alpha Vantage + Ziwox补充) - 保持不变
# ============================================================================
def fetch_forex_rates_alpha_vantage(ziwox_signals):
    """从Alpha Vantage获取实时汇率，失败时从Ziwox信号补充"""
    rates = {}

    ziwox_price_map = {}
    for signal in ziwox_signals:
        pair = signal.get('pair')
        price = signal.get('last_price')
        if pair and price and price > 0:
            ziwox_price_map[pair] = price

    if config.alpha_vantage_key and not config.use_mock:
        try:
            logger.info(f"尝试从Alpha Vantage获取汇率（限制前5个主要品种）...")
            fx = ForeignExchange(key=config.alpha_vantage_key)

            limited_pairs = config.watch_currency_pairs[:5]

            for i, pair in enumerate(limited_pairs):
                try:
                    if i > 0:
                        delay = random.uniform(12, 15)
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
# 模块3：使用market-calendar-tool实时抓取ForexFactory数据
# ============================================================================
class ForexFactoryCalendar:
    """使用BeautifulSoup实时抓取ForexFactory日历数据"""
    
    def __init__(self):
        self.base_url = "https://www.forexfactory.com/calendar?day={}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.beijing_tz = timezone(timedelta(hours=8))
    
    def fetch_events(self, days=3):
        """获取多天的事件，只返回高和中影响的事件"""
        all_events = []
        
        for i in range(days):
            date = datetime.now(self.beijing_tz) + timedelta(days=i)
            date_str = date.strftime("%Y%m%d")
            url = self.base_url.format(date_str)
            
            try:
                logger.info(f"抓取ForexFactory日历数据，日期: {date.strftime('%Y-%m-%d')}")
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                events = self.parse_events(soup, date)
                
                # 只保留高和中影响的事件
                filtered_events = [e for e in events if e['importance'] >= 2]
                all_events.extend(filtered_events)
                
                logger.info(f"  日期 {date.strftime('%Y-%m-%d')}: 找到 {len(events)} 个事件，过滤后 {len(filtered_events)} 个高/中影响事件")
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"抓取 {date.strftime('%Y-%m-%d')} 数据失败: {e}")
                continue
        
        # 按时间排序
        all_events.sort(key=lambda x: (x['date'], x['time']))
        return all_events
    
    def parse_events(self, soup, date):
        """解析HTML页面，提取事件信息"""
        events = []
        
        try:
            calendar_table = soup.find('div', class_='calendar__table')
            if not calendar_table:
                return events
            
            rows = calendar_table.find_all('tr', class_='calendar__row')
            
            for row in rows:
                # 跳过标题行
                if 'calendar__row--heading' in row.get('class', []):
                    continue
                
                # 跳过空行
                if row.get('class') == ['calendar__row', 'calendar_row--grey']:
                    continue
                
                event = self.parse_event_row(row, date)
                if event:
                    events.append(event)
                    
        except Exception as e:
            logger.error(f"解析事件时出错: {e}")
        
        return events
    
    def parse_event_row(self, row, date):
        """解析单个事件行"""
        try:
            # 获取重要性（影响）
            impact_span = row.find('span', class_='calendar__impact')
            if not impact_span:
                return None
            
            # 只处理高和中影响事件
            impact_classes = impact_span.get('class', [])
            importance = 1  # 默认低影响
            
            if 'calendar__impact--high' in impact_classes:
                importance = 3
            elif 'calendar__impact--medium' in impact_classes:
                importance = 2
            else:
                return None  # 跳过低影响事件
            
            # 获取时间
            time_cell = row.find('td', class_='calendar__time')
            time_str = '00:00'
            if time_cell:
                time_text = time_cell.get_text(strip=True)
                if time_text and time_text != '':
                    time_str = time_text
                    # 转换为24小时格式
                    if 'am' in time_str.lower() or 'pm' in time_str.lower():
                        try:
                            dt = datetime.strptime(time_str, '%I:%M%p')
                            time_str = dt.strftime('%H:%M')
                        except:
                            pass
            
            # 获取货币/国家
            currency_cell = row.find('td', class_='calendar__currency')
            country_code = 'GL'
            currency = 'USD'
            if currency_cell:
                currency_text = currency_cell.get_text(strip=True)
                if currency_text:
                    country_code = self.get_country_code(currency_text)
                    currency = self.get_currency_from_country(country_code)
            
            # 获取事件名称
            event_cell = row.find('td', class_='calendar__event')
            event_name = 'Unknown Event'
            if event_cell:
                event_span = event_cell.find('span', class_='calendar__event-title')
                if event_span:
                    event_name = event_span.get_text(strip=True)
            
            # 获取预测值、前值、实际值
            forecast_cell = row.find('td', class_='calendar__forecast')
            previous_cell = row.find('td', class_='calendar__previous')
            actual_cell = row.find('td', class_='calendar__actual')
            
            forecast = self.get_cell_value(forecast_cell)
            previous = self.get_cell_value(previous_cell)
            actual = self.get_cell_value(actual_cell)
            
            # 检查事件是否已发生（用于确定实际值是否可用）
            event_time = datetime.strptime(f"{date.strftime('%Y-%m-%d')} {time_str}", "%Y-%m-%d %H:%M")
            event_time = event_time.replace(tzinfo=self.beijing_tz)
            now = datetime.now(self.beijing_tz)
            
            # 如果事件时间已过但实际值为空，设置为"待公布"
            if event_time < now and (not actual or actual == 'N/A'):
                actual = '待公布'
            
            # 生成事件ID
            event_id = hash(f"{date.strftime('%Y-%m-%d')}{time_str}{event_name}")
            event_id = abs(event_id) % 1000000
            
            return {
                'id': event_id,
                'date': date.strftime('%Y-%m-%d'),
                'time': time_str,
                'country': country_code,
                'name': event_name,
                'forecast': forecast,
                'previous': previous,
                'actual': actual,
                'importance': importance,
                'currency': currency,
                'description': event_name,
                'source': 'ForexFactory实时抓取'
            }
            
        except Exception as e:
            logger.error(f"解析事件行时出错: {e}")
            return None
    
    def get_cell_value(self, cell):
        """获取单元格的值"""
        if not cell:
            return 'N/A'
        
        text = cell.get_text(strip=True)
        if text == '' or text.lower() == 'n/a':
            return 'N/A'
        return text
    
    def get_country_code(self, currency_text):
        """根据货币文本获取国家代码"""
        currency_to_country = {
            'USD': 'US', 'EUR': 'EU', 'GBP': 'GB', 'JPY': 'JP',
            'AUD': 'AU', 'CAD': 'CA', 'CHF': 'CH', 'CNY': 'CN',
            'NZD': 'NZ', 'RUB': 'RU', 'BRL': 'BR', 'INR': 'IN',
            'KRW': 'KR', 'MXN': 'MX', 'ZAR': 'ZA', 'SEK': 'SE',
            'NOK': 'NO', 'DKK': 'DK', 'TRY': 'TR', 'PLN': 'PL',
            'HKD': 'HK', 'SGD': 'SG', 'THB': 'TH', 'IDR': 'ID'
        }
        
        # 尝试匹配货币代码
        for curr, country in currency_to_country.items():
            if curr in currency_text:
                return country
        
        return 'GL'
    
    def get_currency_from_country(self, country_code):
        """根据国家代码获取货币"""
        country_to_currency = {
            'US': 'USD', 'EU': 'EUR', 'GB': 'GBP', 'JP': 'JPY',
            'AU': 'AUD', 'CA': 'CAD', 'CH': 'CHF', 'CN': 'CNY',
            'NZ': 'NZD', 'RU': 'RUB', 'BR': 'BRL', 'IN': 'INR',
            'KR': 'KRW', 'MX': 'MXN', 'ZA': 'ZAR', 'SE': 'SEK',
            'NO': 'NOK', 'DK': 'DKK', 'TR': 'TRY', 'PL': 'PLN',
            'HK': 'HKD', 'SG': 'SGD', 'TH': 'THB', 'ID': 'IDR'
        }
        
        return country_to_currency.get(country_code, 'USD')

# ============================================================================
# 财经日历获取主函数
# ============================================================================
def fetch_economic_calendar():
    """使用market-calendar-tool实时抓取财经日历"""
    if config.use_mock:
        logger.info("配置为使用模拟数据模式")
        return get_simulated_calendar()
    
    try:
        logger.info("开始实时抓取ForexFactory财经日历...")
        calendar = ForexFactoryCalendar()
        events = calendar.fetch_events(days=3)  # 获取3天的事件
        
        # 为事件添加AI分析
        events_with_ai = add_ai_analysis_to_events(events)
        
        logger.info(f"成功抓取 {len(events_with_ai)} 个高/中影响事件")
        return events_with_ai
        
    except Exception as e:
        logger.error(f"实时抓取财经日历失败: {e}")
        return get_simulated_calendar()

def get_simulated_calendar():
    """模拟数据生成"""
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    today_str = now.strftime("%Y-%m-%d")
    
    events = [
        {
            "id": 1,
            "date": today_str,
            "time": "21:00",
            "country": "US",
            "name": "美国非农就业人数变化",
            "forecast": "180K",
            "previous": "199K",
            "actual": "待公布",
            "importance": 3,
            "currency": "USD",
            "description": "美国非农业就业人数月度变化",
            "source": "模拟数据",
            "ai_analysis": "【AI分析】非农数据是市场关注的焦点，预期18万人。若数据高于预期，将提振美元；若低于预期，可能打压美元。关注实际数据与预期的差异。"
        },
        {
            "id": 2,
            "date": today_str,
            "time": "20:30",
            "country": "US",
            "name": "美国失业率",
            "forecast": "3.8%",
            "previous": "3.8%",
            "actual": "待公布",
            "importance": 3,
            "currency": "USD",
            "description": "美国失业率",
            "source": "模拟数据",
            "ai_analysis": "【AI分析】失业率预期持平于3.8%。若数据上升，可能暗示经济放缓，利空美元；若下降则利好美元。"
        },
        {
            "id": 3,
            "date": today_str,
            "time": "09:30",
            "country": "CN",
            "name": "中国CPI年率",
            "forecast": "0.2%",
            "previous": "0.1%",
            "actual": "0.3%",
            "importance": 2,
            "currency": "CNY",
            "description": "中国消费者价格指数同比变化",
            "source": "模拟数据",
            "ai_analysis": "【AI分析】中国CPI略高于预期，显示通胀温和回升。这对人民币有一定支撑，但影响可能有限。"
        }
    ]
    
    return events

def add_ai_analysis_to_events(events):
    """为事件添加AI分析"""
    if not events:
        return events
    
    # 只为重要性较高的事件生成AI分析
    important_events = [e for e in events if e.get('importance', 1) >= 2]
    
    for event in important_events:
        try:
            ai_analysis = generate_ai_analysis_for_event(event)
            event['ai_analysis'] = ai_analysis
            time.sleep(0.5)  # 避免API调用过于频繁
        except Exception as e:
            logger.error(f"为事件生成AI分析失败: {e}")
            event['ai_analysis'] = "【AI分析】分析生成中..."
    
    # 为其他事件添加默认AI分析
    for event in events:
        if 'ai_analysis' not in event:
            event['ai_analysis'] = "【AI分析】该事件重要性较低，暂无详细分析。"
    
    return events

# ============================================================================
# AI分析生成函数（保持不变）
# ============================================================================
def generate_ai_analysis_for_event(event):
    """为单个事件生成AI分析"""
    if not config.enable_ai:
        return "【AI分析】AI分析功能当前已禁用"
    
    api_key = config.openai_api_key.strip()
    if not api_key or len(api_key) < 30:
        return "【AI分析】API密钥配置无效"
    
    try:
        prompt = f"""你是一位专业的宏观外汇分析师。请基于以下经济事件，生成简要的AI分析：

事件信息：
- 国家：{event.get('country', '未知')}
- 事件：{event.get('name', '未知事件')}
- 时间：{event.get('date', '')} {event.get('time', '')}（北京时间）
- 预测值：{event.get('forecast', 'N/A')}
- 前值：{event.get('previous', 'N/A')}
- 重要性：{event.get('importance', 1)}级

请用中文分析：
1. 该事件对相关货币的可能影响
2. 市场预期与实际情况的对比
3. 1-2条具体的交易建议

请控制在150字以内，直接给出分析，不要多余说明。"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        request_body = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "你是一位经验丰富的外汇宏观交易员，擅长给出清晰、直接、可执行的交易分析。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
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
                ai_content = result['choices'][0]['message']['content']
                return f"【AI分析】{ai_content}"
        else:
            logger.warning(f"AI分析请求失败: {response.status_code}")
            return "【AI分析】数据更新中..."
            
    except Exception as e:
        logger.error(f"生成AI分析时出错: {e}")
    
    return "【AI分析】分析生成中..."

def generate_comprehensive_analysis_with_sections(signals, rates, events):
    """生成基于实时数据的综合AI分析"""
    if not config.enable_ai:
        return get_default_analysis_sections()
    
    try:
        # 使用实时数据生成分析
        prompt = self.build_real_time_analysis_prompt(signals, rates, events)
        ai_response = self.call_ai_api(prompt)
        
        # 解析AI回复
        sections = self.parse_ai_response(ai_response)
        summary = self.generate_summary_from_sections(sections)
        
        return {
            "summary": summary,
            "sections": sections
        }
        
    except Exception as e:
        logger.error(f"生成实时分析失败: {e}")
        return get_default_analysis_sections()

def build_real_time_analysis_prompt(self, signals, rates, events):
    """构建基于实时数据的分析提示词"""
    
    # 提取重要信息
    important_events = [e for e in events if e.get('importance', 1) >= 2]
    event_summary = "\n".join([f"- {e['time']} {e['country']} {e['name']} (预期: {e['forecast']})" 
                               for e in important_events[:5]])
    
    market_summary = ""
    if signals:
        for signal in signals[:3]:
            market_summary += f"- {signal['pair']}: {signal.get('last_price', 'N/A')} ({signal.get('d1_trend', 'NEUTRAL')})\n"
    
    return f"""基于以下实时数据，生成今日外汇市场分析：

【当前市场状况】
{market_summary if market_summary else "暂无实时市场数据"}

【今日重要事件】
{event_summary if event_summary else "今日无重要经济事件"}

请按以下结构提供分析：
1. 市场概况：当前市场整体状况
2. 事件分析：对重要事件的分析和预期
3. 货币对展望：主要货币对的技术分析和关键位
4. 交易策略：具体的交易建议
5. 风险提示：交易风险和注意事项

请使用中文，每个部分150字左右。"""

def get_default_analysis_sections():
    """获取默认分析章节"""
    return {
        "summary": "【AI分析】基于实时数据生成分析中...",
        "sections": {
            "market": "正在分析实时市场数据...",
            "events": "正在分析实时经济事件...",
            "outlook": "正在生成货币对展望...",
            "strategy": "正在制定交易策略...",
            "risks": "正在评估交易风险..."
        }
    }

# ============================================================================
# 核心数据更新函数
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

        # 3. 实时抓取财经日历数据
        logger.info("阶段3/4: 实时抓取财经日历...")
        events = fetch_economic_calendar()
        
        # 确保事件按正确时间排序
        events = sort_events_by_datetime(events)

        # 4. 生成基于实时数据的综合AI分析
        logger.info("阶段4/4: 生成实时AI分析...")
        analysis_result = generate_comprehensive_analysis_with_sections(signals, rates, events)
        
        summary = analysis_result.get("summary", "")
        sections = analysis_result.get("sections", {})

        # 5. 存储数据
        store.update_all(signals, rates, events, summary, sections)

        logger.info(f"数据更新成功完成:")
        logger.info(f"  - 市场信号: {len(signals)} 个")
        logger.info(f"  - 汇率数据: {len(rates)} 个")
        logger.info(f"  - 财经日历: {len(events)} 个（实时抓取，只保留高/中影响）")
        logger.info(f"  - AI分析章节: {len(sections)} 个")
        logger.info("="*60)
        return True

    except Exception as e:
        logger.error(f"数据更新失败: {str(e)}", exc_info=True)
        store.set_updating(False, str(e))
        return False

def sort_events_by_datetime(events):
    """按日期时间排序"""
    if not events:
        return events
    
    # 按日期和时间排序（从早到晚）
    events.sort(key=lambda x: (x.get('date', '9999-12-31'), x.get('time', '23:59')))
    
    return events

# ============================================================================
# 后台更新线程函数（保持不变）
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
# 定时任务调度（保持不变）
# ============================================================================
scheduler = BackgroundScheduler()
scheduler.add_job(execute_data_update, 'interval', minutes=30)  # 每30分钟更新一次
scheduler.add_job(execute_data_update, 'cron', hour='*/1')  # 每小时更新一次
scheduler.start()

# ============================================================================
# Flask路由（保持不变）
# ============================================================================
@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "service": "宏观经济AI分析工具（实时抓取版）",
        "version": "5.0",
        "data_sources": {
            "market_signals": "Ziwox",
            "forex_rates": "Alpha Vantage + Ziwox补充",
            "economic_calendar": "ForexFactory实时抓取（只保留高/中影响）",
            "ai_analysis": "laozhang.ai"
        },
        "update_frequency": "每30分钟自动更新",
        "last_updated": store.last_updated.isoformat() if store.last_updated else None
    })

# ... 其他路由保持不变 ...

# ============================================================================
# 启动应用
# ============================================================================
if __name__ == '__main__':
    logger.info("="*60)
    logger.info("启动宏观经济AI分析工具（实时抓取版）")
    logger.info("财经日历源: ForexFactory实时抓取（只保留高/中影响事件）")
    logger.info("AI分析服务: laozhang.ai（基于实时数据）")
    logger.info(f"模拟模式: {config.use_mock}")
    logger.info("="*60)

    # 首次启动时获取数据
    try:
        logger.info("首次启动，正在获取实时数据...")
        success = execute_data_update()
        if success:
            logger.info("初始实时数据获取成功")
        else:
            logger.warning("初始数据获取失败，但服务已启动")
    except Exception as e:
        logger.error(f"初始数据获取异常: {e}")

    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )