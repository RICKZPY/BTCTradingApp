"""
回测引擎实现
执行期权策略的历史回测和绩效分析
"""

import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import uuid4

from src.core.interfaces import IBacktestEngine
from src.core.models import (
    Strategy, OptionContract, BacktestResult, Trade, DailyPnL,
    Position, Portfolio, TradeAction, ActionType, OptionType
)
from src.pricing.options_engine import OptionsEngine
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class BacktestEngine(IBacktestEngine):
    """回测引擎"""
    
    def __init__(self, options_engine: Optional[OptionsEngine] = None):
        """
        初始化回测引擎
        
        Args:
            options_engine: 期权定价引擎（可选，默认创建新实例）
        """
        self.options_engine = options_engine or OptionsEngine()
        logger.info("Backtest engine initialized")
    
    async def run_backtest(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        initial_capital: Decimal,
        underlying_symbol: str = "BTC"
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            strategy: 交易策略
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_capital: 初始资金
            
        Returns:
            BacktestResult对象，包含完整的回测结果
        """
        logger.info(f"Starting backtest for strategy: {strategy.name}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial capital: {initial_capital}")
        
        # 初始化组合
        portfolio = Portfolio(
            cash_balance=initial_capital,
            total_value=initial_capital
        )
        
        # 存储交易记录和每日盈亏
        trades: List[Trade] = []
        daily_pnl: List[DailyPnL] = []
        
        # 建立初始仓位
        entry_date = start_date
        entry_trades = self._open_strategy_positions(strategy, portfolio, entry_date)
        trades.extend(entry_trades)
        
        # 时间循环 - 每日更新
        current_date = start_date
        previous_portfolio_value = initial_capital
        cumulative_pnl = Decimal(0)
        
        while current_date <= end_date:
            # 更新期权价格和希腊字母
            self._update_option_prices(portfolio, current_date)
            
            # 计算时间价值衰减
            self._apply_time_decay(portfolio, current_date)
            
            # 检查期权是否到期
            expired_trades = self._check_and_handle_expiry(portfolio, current_date)
            trades.extend(expired_trades)
            
            # 更新组合价值
            portfolio.total_value = self._calculate_portfolio_value(portfolio)
            
            # 记录每日盈亏
            daily_change = portfolio.total_value - previous_portfolio_value
            cumulative_pnl += daily_change
            
            daily_pnl.append(DailyPnL(
                date=current_date,
                portfolio_value=portfolio.total_value,
                daily_pnl=daily_change,
                cumulative_pnl=cumulative_pnl,
                realized_pnl=sum(t.pnl for t in trades if t.action == TradeAction.CLOSE),
                unrealized_pnl=portfolio.total_unrealized_pnl
            ))
            
            previous_portfolio_value = portfolio.total_value
            current_date += timedelta(days=1)
        
        # 平仓所有剩余持仓
        closing_trades = self._close_all_positions(portfolio, end_date)
        trades.extend(closing_trades)
        
        # 计算最终资金
        final_capital = portfolio.cash_balance
        
        # 计算绩效指标
        total_return = float((final_capital - initial_capital) / initial_capital)
        sharpe_ratio = self._calculate_sharpe_ratio(daily_pnl)
        max_drawdown = self._calculate_max_drawdown(daily_pnl)
        win_rate = self._calculate_win_rate(trades)
        
        result = BacktestResult(
            strategy_name=strategy.name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(trades),
            trades=trades,
            daily_pnl=daily_pnl
        )
        
        logger.info(f"Backtest completed. Total return: {total_return:.2%}")
        logger.info(f"Sharpe ratio: {sharpe_ratio:.2f}, Max drawdown: {max_drawdown:.2%}")
        
        return result

    
    def _open_strategy_positions(
        self,
        strategy: Strategy,
        portfolio: Portfolio,
        entry_date: datetime
    ) -> List[Trade]:
        """
        建立策略仓位
        
        Args:
            strategy: 交易策略
            portfolio: 投资组合
            entry_date: 建仓日期
            
        Returns:
            交易记录列表
        """
        trades = []
        
        for leg in strategy.legs:
            option = leg.option_contract
            quantity = leg.quantity if leg.action == ActionType.BUY else -leg.quantity
            price = option.current_price
            
            # 创建持仓
            position = Position(
                option_contract=option,
                quantity=quantity,
                entry_price=price,
                entry_date=entry_date,
                current_value=price,
                unrealized_pnl=Decimal(0)
            )
            portfolio.positions.append(position)
            
            # 更新现金余额
            trade_value = price * Decimal(abs(quantity))
            if leg.action == ActionType.BUY:
                portfolio.cash_balance -= trade_value
            else:
                portfolio.cash_balance += trade_value
            
            # 记录交易
            trade = Trade(
                timestamp=entry_date,
                action=TradeAction.OPEN,
                option_contract=option,
                quantity=quantity,
                price=price,
                pnl=Decimal(0),
                portfolio_value=portfolio.total_value
            )
            trades.append(trade)
            
            logger.debug(f"Opened position: {option.instrument_name}, qty={quantity}, price={price}")
        
        return trades
    
    def _update_option_prices(self, portfolio: Portfolio, current_date: datetime):
        """
        更新期权价格和希腊字母
        
        Args:
            portfolio: 投资组合
            current_date: 当前日期
        """
        # 模拟标的价格变化（实际应从历史数据获取）
        # 这里使用简化的随机游走模型
        underlying_price = 50000.0  # BTC价格基准
        
        for position in portfolio.positions:
            option = position.option_contract
            
            # 计算到期时间（年）
            time_to_expiry = (option.expiration_date - current_date).days / 365.0
            
            if time_to_expiry > 0:
                # 使用Black-Scholes模型重新定价
                try:
                    new_price = self.options_engine.black_scholes_price(
                        S=underlying_price,
                        K=float(option.strike_price),
                        T=time_to_expiry,
                        r=0.05,  # 5%无风险利率
                        sigma=option.implied_volatility,
                        option_type=option.option_type
                    )
                    
                    # 更新期权价格
                    option.current_price = Decimal(str(new_price))
                    position.current_value = option.current_price
                    
                    # 计算未实现盈亏
                    if position.quantity > 0:
                        position.unrealized_pnl = (option.current_price - position.entry_price) * Decimal(position.quantity)
                    else:
                        position.unrealized_pnl = (position.entry_price - option.current_price) * Decimal(abs(position.quantity))
                    
                    # 更新希腊字母
                    greeks = self.options_engine.calculate_greeks(
                        S=underlying_price,
                        K=float(option.strike_price),
                        T=time_to_expiry,
                        r=0.05,
                        sigma=option.implied_volatility,
                        option_type=option.option_type
                    )
                    option.delta = greeks.delta
                    option.gamma = greeks.gamma
                    option.theta = greeks.theta
                    option.vega = greeks.vega
                    option.rho = greeks.rho
                    
                except Exception as e:
                    logger.warning(f"Failed to update option price: {str(e)}")
    
    def _apply_time_decay(self, portfolio: Portfolio, current_date: datetime):
        """
        应用时间价值衰减
        
        Args:
            portfolio: 投资组合
            current_date: 当前日期
        """
        for position in portfolio.positions:
            option = position.option_contract
            
            # Theta表示每日时间价值衰减
            # 对于多头持仓，时间衰减是负面的
            # 对于空头持仓，时间衰减是正面的
            if position.quantity > 0:
                decay = Decimal(str(option.theta)) * Decimal(position.quantity)
            else:
                decay = -Decimal(str(option.theta)) * Decimal(abs(position.quantity))
            
            # 更新期权价格（应用时间衰减）
            option.current_price = max(option.current_price + decay, Decimal(0))
            position.current_value = option.current_price
    
    def _check_and_handle_expiry(
        self,
        portfolio: Portfolio,
        current_date: datetime
    ) -> List[Trade]:
        """
        检查并处理期权到期
        
        Args:
            portfolio: 投资组合
            current_date: 当前日期
            
        Returns:
            到期交易记录列表
        """
        trades = []
        expired_positions = []
        
        for position in portfolio.positions:
            option = position.option_contract
            
            # 检查是否到期
            if option.expiration_date.date() == current_date.date():
                # 计算到期价值
                expiry_value = self.simulate_option_expiry(option, Decimal(50000))
                
                # 计算盈亏
                if position.quantity > 0:
                    pnl = (expiry_value - position.entry_price) * Decimal(position.quantity)
                else:
                    pnl = (position.entry_price - expiry_value) * Decimal(abs(position.quantity))
                
                # 更新现金余额
                portfolio.cash_balance += expiry_value * Decimal(abs(position.quantity))
                
                # 记录交易
                trade = Trade(
                    timestamp=current_date,
                    action=TradeAction.EXPIRE,
                    option_contract=option,
                    quantity=position.quantity,
                    price=expiry_value,
                    pnl=pnl,
                    portfolio_value=portfolio.total_value
                )
                trades.append(trade)
                expired_positions.append(position)
                
                logger.debug(f"Option expired: {option.instrument_name}, pnl={pnl}")
        
        # 移除到期持仓
        for position in expired_positions:
            portfolio.positions.remove(position)
        
        return trades
    
    def _close_all_positions(
        self,
        portfolio: Portfolio,
        close_date: datetime
    ) -> List[Trade]:
        """
        平仓所有持仓
        
        Args:
            portfolio: 投资组合
            close_date: 平仓日期
            
        Returns:
            平仓交易记录列表
        """
        trades = []
        
        for position in portfolio.positions[:]:  # 使用切片创建副本
            option = position.option_contract
            close_price = option.current_price
            
            # 计算盈亏
            if position.quantity > 0:
                pnl = (close_price - position.entry_price) * Decimal(position.quantity)
                portfolio.cash_balance += close_price * Decimal(position.quantity)
            else:
                pnl = (position.entry_price - close_price) * Decimal(abs(position.quantity))
                portfolio.cash_balance -= close_price * Decimal(abs(position.quantity))
            
            # 记录交易
            trade = Trade(
                timestamp=close_date,
                action=TradeAction.CLOSE,
                option_contract=option,
                quantity=position.quantity,
                price=close_price,
                pnl=pnl,
                portfolio_value=portfolio.total_value
            )
            trades.append(trade)
            
            logger.debug(f"Closed position: {option.instrument_name}, pnl={pnl}")
        
        # 清空所有持仓
        portfolio.positions.clear()
        
        return trades
    
    def _calculate_portfolio_value(self, portfolio: Portfolio) -> Decimal:
        """
        计算组合总价值
        
        Args:
            portfolio: 投资组合
            
        Returns:
            组合总价值
        """
        positions_value = sum(
            pos.current_value * Decimal(abs(pos.quantity))
            for pos in portfolio.positions
        )
        
        return portfolio.cash_balance + positions_value
    
    def simulate_option_expiry(
        self,
        option: OptionContract,
        underlying_price: Decimal
    ) -> Decimal:
        """
        模拟期权到期价值
        
        Args:
            option: 期权合约
            underlying_price: 标的资产价格
            
        Returns:
            期权到期价值
        """
        if option.option_type == OptionType.CALL:
            # 看涨期权到期价值 = max(S - K, 0)
            expiry_value = max(underlying_price - option.strike_price, Decimal(0))
        else:  # PUT
            # 看跌期权到期价值 = max(K - S, 0)
            expiry_value = max(option.strike_price - underlying_price, Decimal(0))
        
        return expiry_value
    
    def calculate_time_decay(
        self,
        option: OptionContract,
        days_passed: int
    ) -> Decimal:
        """
        计算时间价值衰减
        
        Args:
            option: 期权合约
            days_passed: 经过的天数
            
        Returns:
            时间价值衰减金额
        """
        # Theta表示每日时间价值衰减
        total_decay = Decimal(str(option.theta)) * Decimal(days_passed)
        return total_decay
    
    def handle_early_exercise(
        self,
        option: OptionContract,
        underlying_price: Decimal
    ) -> bool:
        """
        处理提前行权（美式期权）
        
        Args:
            option: 期权合约
            underlying_price: 标的资产价格
            
        Returns:
            是否应该提前行权
        """
        # 简化的提前行权逻辑
        # 实际应考虑更多因素，如股息、利率等
        
        intrinsic_value = self.simulate_option_expiry(option, underlying_price)
        
        # 如果内在价值显著高于时间价值，考虑提前行权
        time_value = option.current_price - intrinsic_value
        
        # 如果时间价值很小（小于内在价值的5%），可以考虑提前行权
        if intrinsic_value > 0 and time_value < intrinsic_value * Decimal("0.05"):
            return True
        
        return False
    
    def _calculate_sharpe_ratio(self, daily_pnl: List[DailyPnL]) -> float:
        """
        计算夏普比率
        
        Args:
            daily_pnl: 每日盈亏列表
            
        Returns:
            夏普比率
        """
        if len(daily_pnl) < 2:
            return 0.0
        
        # 计算每日收益率
        returns = []
        for i in range(1, len(daily_pnl)):
            prev_value = daily_pnl[i-1].portfolio_value
            curr_value = daily_pnl[i].portfolio_value
            if prev_value > 0:
                daily_return = float((curr_value - prev_value) / prev_value)
                returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        # 计算平均收益率和标准差
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 假设无风险利率为0（简化）
        # 年化夏普比率 = (平均日收益率 * 252) / (日收益率标准差 * sqrt(252))
        sharpe_ratio = (mean_return * np.sqrt(252)) / std_return
        
        return float(sharpe_ratio)
    
    def _calculate_max_drawdown(self, daily_pnl: List[DailyPnL]) -> float:
        """
        计算最大回撤
        
        Args:
            daily_pnl: 每日盈亏列表
            
        Returns:
            最大回撤（百分比）
        """
        if not daily_pnl:
            return 0.0
        
        portfolio_values = [float(pnl.portfolio_value) for pnl in daily_pnl]
        
        max_drawdown = 0.0
        peak = portfolio_values[0]
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def _calculate_win_rate(self, trades: List[Trade]) -> float:
        """
        计算胜率
        
        Args:
            trades: 交易记录列表
            
        Returns:
            胜率（百分比）
        """
        # 只统计平仓和到期的交易
        closed_trades = [t for t in trades if t.action in [TradeAction.CLOSE, TradeAction.EXPIRE]]
        
        if not closed_trades:
            return 0.0
        
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(closed_trades)
        
        return win_rate
