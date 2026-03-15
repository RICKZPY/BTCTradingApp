#!/usr/bin/env python3
"""
持仓管理器
Dynamic Position Management

核心功能：
1. 实时监控所有持仓
2. 自动止盈/止损
3. 动态调整仓位
4. 风险控制

目标：保护利润，控制风险
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class Position:
    """持仓信息"""
    instrument_name: str
    option_type: str  # 'call' | 'put' | 'straddle'
    entry_price: float
    entry_iv: float
    entry_time: datetime
    quantity: float
    news_id: str
    news_score: int
    target_profit_pct: float = 0.30  # 目标收益 30%
    stop_loss_pct: float = -0.40  # 止损 -40%
    trailing_stop_pct: float = 0.15  # 移动止损 15%
    max_hold_days: int = 7  # 最长持仓 7 天


class PositionManager:
    """持仓管理器"""
    
    def __init__(self, deribit_trader):
        self.trader = deribit_trader
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Dict] = []
        self.highest_pnl: Dict[str, float] = {}  # 记录每个持仓的最高盈利
    
    async def add_position(self, position: Position):
        """添加新持仓"""
        self.positions[position.instrument_name] = position
        self.highest_pnl[position.instrument_name] = 0.0
        await self.save_positions()
    
    async def check_all_positions(self):
        """检查所有持仓，执行止盈/止损"""
        if not self.positions:
            return
        
        print(f"\n{'='*60}")
        print(f"持仓检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"当前持仓数: {len(self.positions)}")
        print(f"{'='*60}")
        
        positions_to_close = []
        
        for instrument_name, position in self.positions.items():
            try:
                # 获取当前价格和 PnL
                current_price = await self.get_current_price(instrument_name)
                current_iv = await self.get_current_iv(instrument_name)
                
                if current_price <= 0:
                    continue
                
                pnl_pct = (current_price - position.entry_price) / position.entry_price
                pnl_usd = (current_price - position.entry_price) * position.quantity
                
                # 更新最高盈利
                if pnl_pct > self.highest_pnl[instrument_name]:
                    self.highest_pnl[instrument_name] = pnl_pct
                
                # 计算持仓天数
                days_held = (datetime.now() - position.entry_time).days
                
                print(f"\n持仓: {instrument_name}")
                print(f"  类型: {position.option_type}")
                print(f"  入场价: {position.entry_price:.4f} BTC")
                print(f"  当前价: {current_price:.4f} BTC")
                print(f"  盈亏: {pnl_pct*100:+.2f}% (${pnl_usd:+.2f})")
                print(f"  入场IV: {position.entry_iv*100:.1f}%")
                print(f"  当前IV: {current_iv*100:.1f}%")
                print(f"  持仓天数: {days_held}")
                
                # 检查退出条件
                should_close, reason = await self.should_close_position(
                    position, current_price, current_iv, pnl_pct, days_held
                )
                
                if should_close:
                    print(f"  ⚠️  触发平仓: {reason}")
                    positions_to_close.append((instrument_name, position, reason, pnl_pct))
                else:
                    print(f"  ✓ 继续持有")
            
            except Exception as e:
                print(f"  ✗ 检查失败: {e}")
        
        # 执行平仓
        for instrument_name, position, reason, pnl_pct in positions_to_close:
            await self.close_position(instrument_name, position, reason, pnl_pct)
    
    async def should_close_position(
        self,
        position: Position,
        current_price: float,
        current_iv: float,
        pnl_pct: float,
        days_held: int
    ) -> tuple[bool, str]:
        """
        判断是否应该平仓
        
        Returns:
            (should_close, reason)
        """
        # 1. 止盈：达到目标收益
        if pnl_pct >= position.target_profit_pct:
            return True, f"止盈 ({pnl_pct*100:.1f}% >= {position.target_profit_pct*100:.1f}%)"
        
        # 2. 止损：达到止损线
        if pnl_pct <= position.stop_loss_pct:
            return True, f"止损 ({pnl_pct*100:.1f}% <= {position.stop_loss_pct*100:.1f}%)"
        
        # 3. 移动止损：从最高点回撤超过阈值
        highest_pnl = self.highest_pnl.get(position.instrument_name, 0.0)
        if highest_pnl > 0.10:  # 曾经盈利超过 10%
            drawdown = highest_pnl - pnl_pct
            if drawdown > position.trailing_stop_pct:
                return True, f"移动止损 (回撤 {drawdown*100:.1f}%)"
        
        # 4. IV 扩张止盈：IV 上涨 50% 且有盈利
        if current_iv > position.entry_iv * 1.5 and pnl_pct > 0.10:
            return True, f"IV 扩张止盈 (IV: {position.entry_iv*100:.1f}% → {current_iv*100:.1f}%)"
        
        # 5. 时间止损：持仓超过最大天数
        if days_held >= position.max_hold_days:
            if pnl_pct > 0:
                return True, f"时间止盈 ({days_held}天，盈利 {pnl_pct*100:.1f}%)"
            else:
                return True, f"时间止损 ({days_held}天，亏损 {pnl_pct*100:.1f}%)"
        
        # 6. 时间衰减止损：持仓 3 天以上且亏损
        if days_held >= 3 and pnl_pct < -0.10:
            return True, f"时间衰减止损 ({days_held}天，亏损 {pnl_pct*100:.1f}%)"
        
        return False, ""
    
    async def close_position(
        self,
        instrument_name: str,
        position: Position,
        reason: str,
        pnl_pct: float
    ):
        """平仓"""
        try:
            print(f"\n{'='*60}")
            print(f"执行平仓: {instrument_name}")
            print(f"原因: {reason}")
            print(f"{'='*60}")
            
            # 调用 Deribit API 平仓
            result = await self.trader.sell(
                instrument_name=instrument_name,
                amount=position.quantity,
                order_type="market"
            )
            
            if result:
                print(f"✓ 平仓成功")
                
                # 记录平仓信息
                close_record = {
                    'instrument_name': instrument_name,
                    'option_type': position.option_type,
                    'entry_price': position.entry_price,
                    'entry_time': position.entry_time.isoformat(),
                    'close_time': datetime.now().isoformat(),
                    'close_reason': reason,
                    'pnl_pct': pnl_pct,
                    'days_held': (datetime.now() - position.entry_time).days,
                    'news_id': position.news_id,
                    'news_score': position.news_score
                }
                
                self.closed_positions.append(close_record)
                
                # 从持仓列表移除
                del self.positions[instrument_name]
                del self.highest_pnl[instrument_name]
                
                # 保存状态
                await self.save_positions()
                await self.save_closed_positions()
            else:
                print(f"✗ 平仓失败")
        
        except Exception as e:
            print(f"✗ 平仓异常: {e}")
    
    async def get_current_price(self, instrument_name: str) -> float:
        """获取当前价格"""
        try:
            url = f"{self.trader.base_url}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    return data['result'].get('mark_price', 0.0)
        except:
            return 0.0
    
    async def get_current_iv(self, instrument_name: str) -> float:
        """获取当前 IV"""
        try:
            url = f"{self.trader.base_url}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    return data['result'].get('mark_iv', 0.0) / 100
        except:
            return 0.0
    
    async def save_positions(self):
        """保存持仓到文件"""
        from pathlib import Path
        data_dir = Path(__file__).parent.parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        positions_data = {
            name: {
                'instrument_name': pos.instrument_name,
                'option_type': pos.option_type,
                'entry_price': pos.entry_price,
                'entry_iv': pos.entry_iv,
                'entry_time': pos.entry_time.isoformat(),
                'quantity': pos.quantity,
                'news_id': pos.news_id,
                'news_score': pos.news_score
            }
            for name, pos in self.positions.items()
        }
        
        with open(data_dir / "active_positions.json", 'w') as f:
            json.dump(positions_data, f, indent=2)
    
    async def save_closed_positions(self):
        """保存已平仓记录"""
        from pathlib import Path
        data_dir = Path(__file__).parent.parent.parent / "data"
        
        with open(data_dir / "closed_positions.json", 'w') as f:
            json.dump(self.closed_positions, f, indent=2)
    
    async def load_positions(self):
        """从文件加载持仓"""
        from pathlib import Path
        data_dir = Path(__file__).parent.parent.parent / "data"
        positions_file = data_dir / "active_positions.json"
        
        if not positions_file.exists():
            return
        
        with open(positions_file, 'r') as f:
            positions_data = json.load(f)
        
        for name, data in positions_data.items():
            position = Position(
                instrument_name=data['instrument_name'],
                option_type=data['option_type'],
                entry_price=data['entry_price'],
                entry_iv=data['entry_iv'],
                entry_time=datetime.fromisoformat(data['entry_time']),
                quantity=data['quantity'],
                news_id=data['news_id'],
                news_score=data['news_score']
            )
            self.positions[name] = position
            self.highest_pnl[name] = 0.0
    
    def get_performance_stats(self) -> Dict:
        """获取绩效统计"""
        if not self.closed_positions:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_pnl': 0.0,
                'total_pnl': 0.0
            }
        
        total_trades = len(self.closed_positions)
        winning_trades = sum(1 for p in self.closed_positions if p['pnl_pct'] > 0)
        win_rate = winning_trades / total_trades
        
        pnls = [p['pnl_pct'] for p in self.closed_positions]
        avg_pnl = sum(pnls) / len(pnls)
        total_pnl = sum(pnls)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'best_trade': max(pnls),
            'worst_trade': min(pnls)
        }
