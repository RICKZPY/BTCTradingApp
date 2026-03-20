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
import aiohttp
import importlib.util
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
load_dotenv()

from weighted_sentiment_api_client import NewsAPIClient
from weighted_sentiment_news_tracker import NewsTracker
from weighted_sentiment_models import WeightedNews, StraddleTradeResult, OptionTrade

# 直接导入 DeribitTrader，避免触发包的 __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "deribit_trader",
    Path(__file__).parent / "src" / "trading" / "deribit_trader.py"
)
deribit_trader_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deribit_trader_module)
DeribitTrader = deribit_trader_module.DeribitTrader


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


class StraddleExecutor:
    """跨式期权执行器 - 集成 Deribit 实际交易
    
    使用 DeribitTrader 在 Deribit Test 环境下单
    """
    
    def __init__(self):
        """初始化执行器"""
        self.api_key = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_KEY')
        self.api_secret = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            logger.error(
                "未配置 Deribit 凭证。请设置环境变量：\n"
                "  WEIGHTED_SENTIMENT_DERIBIT_API_KEY\n"
                "  WEIGHTED_SENTIMENT_DERIBIT_API_SECRET"
            )
            raise ValueError("缺少 Deribit API 凭证")
        
        # 初始化 DeribitTrader（测试网，仅用于下单）
        self.trader = DeribitTrader(self.api_key, self.api_secret, testnet=True)
        self.authenticated = False
        
        # 主网公开API（无需认证，用于获取真实行情和IV）
        self.mainnet_url = "https://www.deribit.com/api/v2"
    
    async def authenticate(self) -> bool:
        """认证 Deribit API
        
        Returns:
            是否认证成功
        """
        if self.authenticated:
            return True
        
        try:
            success = await self.trader.authenticate()
            if success:
                self.authenticated = True
                logger.info("Deribit 认证成功")
            else:
                logger.error("Deribit 认证失败")
            return success
        except Exception as e:
            logger.error(f"Deribit 认证异常: {e}")
            return False
    
    async def get_spot_price(self) -> float:
        """获取 BTC 现货价格（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/get_index_price"
            params = {"index_name": "btc_usd"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data and 'index_price' in data['result']:
                        price = data['result']['index_price']
                        logger.info(f"获取 BTC 现货价格: ${price:.2f}")
                        return price
                    else:
                        logger.error(f"获取现货价格失败: {data}")
                        return 0.0
        except Exception as e:
            logger.error(f"获取现货价格异常: {e}")
            return 0.0
    
    async def find_atm_options(self, spot_price: float) -> tuple[Optional[str], Optional[str]]:
        """查找 ATM（平值）期权合约（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/get_instruments"
            params = {"currency": "BTC", "kind": "option", "expired": "false"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' not in data:
                        logger.error(f"获取合约列表失败: {data}")
                        return None, None
                    
                    instruments = data['result']
                    logger.info(f"获取到 {len(instruments)} 个期权合约")
                    
                    # 找到最接近现货价格的执行价格
                    # 筛选出最近到期的合约（通常流动性更好）
                    from datetime import datetime, timedelta
                    
                    # 目标：找距今最接近 3 天后到期的合约（保证每笔信号期权长度一致）
                    # 由于 Deribit 不是每天都有合约，取所有到期日中最接近 +3 天的那个
                    now = datetime.now()
                    target_expiry = now + timedelta(days=3)

                    # 先收集所有未来合约的到期日（去重）
                    all_expiries = set()
                    for inst in instruments:
                        exp_ts = inst.get('expiration_timestamp')
                        if exp_ts:
                            all_expiries.add(datetime.fromtimestamp(exp_ts / 1000))

                    # 只保留未来的到期日，找最接近 target_expiry 的
                    future_expiries = sorted(e for e in all_expiries if e > now)
                    if not future_expiries:
                        logger.error("未找到任何未来到期合约")
                        return None, None

                    chosen_expiry = min(future_expiries, key=lambda e: abs((e - target_expiry).total_seconds()))
                    logger.info(f"目标到期日: {target_expiry.strftime('%Y-%m-%d')}，"
                                f"实际选用: {chosen_expiry.strftime('%Y-%m-%d')} "
                                f"(距今 {(chosen_expiry - now).days} 天)")

                    call_options = []
                    put_options = []

                    for inst in instruments:
                        try:
                            exp_ts = inst.get('expiration_timestamp')
                            if not exp_ts:
                                continue

                            expiry_dt = datetime.fromtimestamp(exp_ts / 1000)

                            # 只取 chosen_expiry 当天的合约
                            if expiry_dt.date() != chosen_expiry.date():
                                continue

                            strike = inst.get('strike')
                            option_type = inst.get('option_type')
                            instrument_name = inst.get('instrument_name')

                            if not all([strike, option_type, instrument_name]):
                                continue

                            price_diff = abs(strike - spot_price)

                            if option_type == 'call':
                                call_options.append((instrument_name, strike, price_diff, expiry_dt))
                            elif option_type == 'put':
                                put_options.append((instrument_name, strike, price_diff, expiry_dt))

                        except Exception as e:
                            logger.debug(f"解析合约失败: {e}")
                            continue

                    if not call_options or not put_options:
                        logger.error(f"在 {chosen_expiry.strftime('%Y-%m-%d')} 未找到合适的期权合约")
                        return None, None

                    # 按与现货价差排序，选 ATM
                    call_options.sort(key=lambda x: x[2])
                    put_options.sort(key=lambda x: x[2])

                    # 优先选同一执行价的 call/put（真正的 ATM straddle）
                    best_call = call_options[0]
                    same_strike_puts = [p for p in put_options if p[1] == best_call[1]]
                    best_put = same_strike_puts[0] if same_strike_puts else put_options[0]

                    call_instrument = best_call[0]
                    put_instrument = best_put[0]

                    logger.info(f"选择 ATM 期权:")
                    logger.info(f"  看涨: {call_instrument} (执行价: {best_call[1]}, 价差: {best_call[2]:.0f})")
                    logger.info(f"  看跌: {put_instrument} (执行价: {best_put[1]}, 价差: {best_put[2]:.0f})")
                    
                    return call_instrument, put_instrument
        
        except Exception as e:
            logger.error(f"查找 ATM 期权异常: {e}")
            return None, None
    
    async def get_option_price(self, instrument_name: str) -> float:
        """获取期权价格（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data and 'mark_price' in data['result']:
                        price = data['result']['mark_price']
                        logger.info(f"{instrument_name} 价格: {price}")
                        return price
                    else:
                        logger.error(f"获取期权价格失败: {data}")
                        return 0.0
        except Exception as e:
            logger.error(f"获取期权价格异常: {e}")
            return 0.0
    
    async def get_option_iv(self, instrument_name: str) -> float:
        """获取期权隐含波动率（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data and 'mark_iv' in data['result']:
                        iv = data['result']['mark_iv']
                        logger.info(f"{instrument_name} IV: {iv:.2f}%")
                        return iv
                    else:
                        logger.warning(f"获取 IV 失败: {data}")
                        return 0.0
        except Exception as e:
            logger.error(f"获取 IV 异常: {e}")
            return 0.0
    
    async def execute_straddle(self, news: WeightedNews) -> StraddleTradeResult:
        """执行跨式期权交易
        
        Args:
            news: 触发交易的新闻
        
        Returns:
            交易结果
        """
        logger.info(f"执行跨式交易，触发新闻: {news.news_id}")
        logger.info(f"  内容: {news.content[:80]}...")
        logger.info(f"  情绪: {news.sentiment}")
        logger.info(f"  评分: {news.importance_score}/10")
        
        try:
            # 1. 认证
            if not await self.authenticate():
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=0.0,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="Deribit 认证失败"
                )
            
            # 2. 获取现货价格
            spot_price = await self.get_spot_price()
            if spot_price <= 0:
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=0.0,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="无法获取现货价格"
                )
            
            # 3. 查找 ATM 期权
            call_instrument, put_instrument = await self.find_atm_options(spot_price)
            if not call_instrument or not put_instrument:
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=spot_price,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="未找到合适的 ATM 期权"
                )
            
            # 4. 获取期权价格和IV（主网真实数据，无论下单是否成功都会记录）
            call_price = await self.get_option_price(call_instrument)
            put_price = await self.get_option_price(put_instrument)
            call_iv = await self.get_option_iv(call_instrument)
            put_iv = await self.get_option_iv(put_instrument)
            
            if call_price <= 0 or put_price <= 0:
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=spot_price,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="无法获取期权价格"
                )
            
            # 5. 解析合约信息 + 下单（使用市价单，数量为 0.1 BTC）
            trade_amount = 0.1
            import re
            call_match = re.search(r'BTC-(\d+[A-Z]{3}\d+)-(\d+)-C', call_instrument)
            call_strike = float(call_match.group(2)) if call_match else spot_price
            put_match = re.search(r'BTC-(\d+[A-Z]{3}\d+)-(\d+)-P', put_instrument)
            put_strike = float(put_match.group(2)) if put_match else spot_price
            expiry_date = datetime.now() + timedelta(days=14)
            total_cost = (call_price + put_price) * trade_amount * spot_price
            avg_iv = (call_iv + put_iv) / 2
            
            logger.info(f"下单买入看涨期权: {call_instrument}, 数量: {trade_amount}")
            call_order = await self.trader.buy(
                instrument_name=call_instrument,
                amount=trade_amount,
                order_type="market"
            )
            
            if not call_order:
                logger.warning(f"看涨期权下单失败，记录为虚拟交易")
                return self._build_virtual_result(
                    news, spot_price, call_instrument, put_instrument,
                    call_price, put_price, call_strike, put_strike,
                    expiry_date, trade_amount, total_cost, call_iv, put_iv,
                    "看涨期权下单失败（测试网不可用）"
                )
            
            logger.info(f"下单买入看跌期权: {put_instrument}, 数量: {trade_amount}")
            put_order = await self.trader.buy(
                instrument_name=put_instrument,
                amount=trade_amount,
                order_type="market"
            )
            
            if not put_order:
                logger.warning(f"看跌期权下单失败，记录为虚拟交易")
                return self._build_virtual_result(
                    news, spot_price, call_instrument, put_instrument,
                    call_price, put_price, call_strike, put_strike,
                    expiry_date, trade_amount, total_cost, call_iv, put_iv,
                    "看跌期权下单失败（测试网不可用）"
                )
            
            # 6. 构建真实交易结果（复用已解析的数据）
            call_option = OptionTrade(
                instrument_name=call_instrument,
                option_type="call",
                strike_price=call_strike,
                expiry_date=expiry_date,
                premium=call_price,
                quantity=trade_amount,
                order_id=call_order.get('order', {}).get('order_id')
            )
            
            put_option = OptionTrade(
                instrument_name=put_instrument,
                option_type="put",
                strike_price=put_strike,
                expiry_date=expiry_date,
                premium=put_price,
                quantity=trade_amount,
                order_id=put_order.get('order', {}).get('order_id')
            )
            
            logger.info(f"✓ 跨式交易执行成功")
            logger.info(f"  看涨订单 ID: {call_option.order_id}")
            logger.info(f"  看跌订单 ID: {put_option.order_id}")
            logger.info(f"  平均 IV: {avg_iv:.2f}%")
            logger.info(f"  总成本: ${total_cost:.2f}")
            
            return StraddleTradeResult(
                success=True,
                news_id=news.news_id,
                trade_time=datetime.now(),
                spot_price=spot_price,
                call_option=call_option,
                put_option=put_option,
                total_cost=total_cost,
                error_message=None
            )
        
        except Exception as e:
            logger.error(f"执行跨式交易异常: {e}", exc_info=True)
            return StraddleTradeResult(
                success=False,
                news_id=news.news_id,
                trade_time=datetime.now(),
                spot_price=0.0,
                call_option=None,
                put_option=None,
                total_cost=0.0,
                error_message=f"交易异常: {str(e)}"
            )
    def _build_virtual_result(
        self, news, spot_price, call_instrument, put_instrument,
        call_price, put_price, call_strike, put_strike,
        expiry_date, trade_amount, total_cost, call_iv, put_iv, reason
    ) -> StraddleTradeResult:
        """构建虚拟交易结果（测试网不可用时，用主网行情数据模拟）"""
        call_option = OptionTrade(
            instrument_name=call_instrument,
            option_type="call",
            strike_price=call_strike,
            expiry_date=expiry_date,
            premium=call_price,
            quantity=trade_amount,
            order_id="VIRTUAL"
        )
        put_option = OptionTrade(
            instrument_name=put_instrument,
            option_type="put",
            strike_price=put_strike,
            expiry_date=expiry_date,
            premium=put_price,
            quantity=trade_amount,
            order_id="VIRTUAL"
        )
        avg_iv = (call_iv + put_iv) / 2
        logger.info(f"✓ 虚拟交易记录（主网行情）: IV={avg_iv:.2f}%, 成本=${total_cost:.2f}, 原因: {reason}")
        return StraddleTradeResult(
            success=True,
            news_id=news.news_id,
            trade_time=datetime.now(),
            spot_price=spot_price,
            call_option=call_option,
            put_option=put_option,
            total_cost=total_cost,
            error_message=None
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
    
    async def log_trade(self, news: WeightedNews, result: StraddleTradeResult, call_iv: float = 0.0, put_iv: float = 0.0):
        """记录交易
        
        Args:
            news: 触发交易的新闻
            result: 交易结果
            call_iv: 看涨期权IV
            put_iv: 看跌期权IV
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
            avg_iv = (call_iv + put_iv) / 2 if call_iv > 0 and put_iv > 0 else 0.0
            is_virtual = (
                result.call_option and result.call_option.order_id == "VIRTUAL"
            )
            # 主网入场价格（BTC单位，用于PnL计算）
            call_entry_btc = result.call_option.premium
            put_entry_btc = result.put_option.premium
            log_entry += (
                f"虚拟交易: {'True' if is_virtual else 'False'}\n"
                f"现货价格: ${result.spot_price:.2f}\n"
                f"看涨期权: {result.call_option.instrument_name}\n"
                f"  执行价: ${result.call_option.strike_price:.2f}\n"
                f"  入场价(BTC): {call_entry_btc:.6f}\n"
                f"  权利金: {result.call_option.premium:.4f} BTC\n"
                f"  IV: {call_iv:.2f}%\n"
                f"  订单 ID: {result.call_option.order_id}\n"
                f"看跌期权: {result.put_option.instrument_name}\n"
                f"  执行价: ${result.put_option.strike_price:.2f}\n"
                f"  入场价(BTC): {put_entry_btc:.6f}\n"
                f"  权利金: {result.put_option.premium:.4f} BTC\n"
                f"  IV: {put_iv:.2f}%\n"
                f"  订单 ID: {result.put_option.order_id}\n"
                f"平均 IV: {avg_iv:.2f}%\n"
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
        executor = StraddleExecutor()
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
                
                # 获取IV数据（从日志中提取或重新获取）
                call_iv = 0.0
                put_iv = 0.0
                if result.success and result.call_option and result.put_option:
                    # 重新获取IV
                    call_iv = await executor.get_option_iv(result.call_option.instrument_name)
                    put_iv = await executor.get_option_iv(result.put_option.instrument_name)
                
                # 记录交易（包含IV）
                await trade_logger.log_trade(news, result, call_iv, put_iv)
                
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
