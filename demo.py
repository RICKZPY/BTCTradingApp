#!/usr/bin/env python3
"""
Bitcoin Trading System - 演示脚本
展示系统的核心功能和架构
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

class DemoTradingSystem:
    """演示版比特币交易系统"""
    
    def __init__(self):
        self.portfolio = {
            "btc_balance": 0.5,
            "usdt_balance": 10000.0,
            "total_value": 0.0
        }
        self.current_price = 45000.0
        self.news_data = []
        self.technical_indicators = {}
        self.trading_history = []
        
    def simulate_market_data(self) -> Dict[str, Any]:
        """模拟市场数据"""
        # 模拟价格波动
        price_change = random.uniform(-0.02, 0.02)  # ±2%
        self.current_price *= (1 + price_change)
        
        return {
            "symbol": "BTCUSDT",
            "price": round(self.current_price, 2),
            "volume": random.randint(1000, 5000),
            "timestamp": datetime.now().isoformat(),
            "change_24h": round(price_change * 100, 2)
        }
    
    def simulate_news_sentiment(self) -> Dict[str, Any]:
        """模拟新闻情绪分析"""
        news_items = [
            {
                "title": "比特币ETF获得SEC批准，市场情绪乐观",
                "sentiment": 85,
                "impact": "positive",
                "confidence": 0.9
            },
            {
                "title": "美联储加息预期推高美元，加密货币承压",
                "sentiment": 35,
                "impact": "negative", 
                "confidence": 0.7
            },
            {
                "title": "机构投资者持续增持比特币",
                "sentiment": 75,
                "impact": "positive",
                "confidence": 0.8
            }
        ]
        
        selected_news = random.choice(news_items)
        return {
            "news_item": selected_news,
            "overall_sentiment": selected_news["sentiment"],
            "market_impact": selected_news["impact"],
            "analysis_time": datetime.now().isoformat()
        }
    
    def calculate_technical_indicators(self, prices: List[float]) -> Dict[str, float]:
        """计算技术指标"""
        if len(prices) < 14:
            prices.extend([self.current_price] * (14 - len(prices)))
        
        # 简化的RSI计算
        gains = [max(0, prices[i] - prices[i-1]) for i in range(1, len(prices))]
        losses = [max(0, prices[i-1] - prices[i]) for i in range(1, len(prices))]
        
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # 简化的MACD
        ema_12 = sum(prices[-12:]) / 12
        ema_26 = sum(prices[-26:]) / min(26, len(prices))
        macd = ema_12 - ema_26
        
        return {
            "rsi": round(rsi, 2),
            "macd": round(macd, 2),
            "sma_20": round(sum(prices[-20:]) / min(20, len(prices)), 2),
            "price": round(self.current_price, 2)
        }
    
    def generate_trading_decision(self, sentiment: Dict, technical: Dict) -> Dict[str, Any]:
        """生成交易决策"""
        # 综合分析
        sentiment_score = sentiment["overall_sentiment"] / 100
        
        # RSI信号
        rsi = technical["rsi"]
        if rsi > 70:
            rsi_signal = -0.5  # 超买
        elif rsi < 30:
            rsi_signal = 0.5   # 超卖
        else:
            rsi_signal = 0
        
        # MACD信号
        macd_signal = 0.3 if technical["macd"] > 0 else -0.3
        
        # 综合信号
        combined_signal = (sentiment_score - 0.5) * 0.4 + rsi_signal * 0.3 + macd_signal * 0.3
        
        # 决策逻辑
        if combined_signal > 0.3:
            action = "BUY"
            confidence = min(0.9, abs(combined_signal))
        elif combined_signal < -0.3:
            action = "SELL"
            confidence = min(0.9, abs(combined_signal))
        else:
            action = "HOLD"
            confidence = 0.5
        
        return {
            "action": action,
            "confidence": round(confidence, 2),
            "signal_strength": round(combined_signal, 3),
            "reasoning": f"情绪分析: {sentiment_score:.2f}, RSI: {rsi}, MACD: {technical['macd']:.2f}",
            "timestamp": datetime.now().isoformat()
        }
    
    def execute_trade(self, decision: Dict) -> Dict[str, Any]:
        """执行交易（模拟）"""
        if decision["action"] == "HOLD":
            return {"status": "no_action", "message": "持有当前仓位"}
        
        # 计算交易数量（基于置信度和风险管理）
        max_trade_amount = self.portfolio["usdt_balance"] * 0.1  # 最大10%仓位
        trade_amount = max_trade_amount * decision["confidence"]
        
        if decision["action"] == "BUY" and self.portfolio["usdt_balance"] >= trade_amount:
            btc_amount = trade_amount / self.current_price
            self.portfolio["btc_balance"] += btc_amount
            self.portfolio["usdt_balance"] -= trade_amount
            
            trade_record = {
                "action": "BUY",
                "amount": round(btc_amount, 6),
                "price": round(self.current_price, 2),
                "value": round(trade_amount, 2),
                "timestamp": datetime.now().isoformat()
            }
            
        elif decision["action"] == "SELL" and self.portfolio["btc_balance"] > 0:
            btc_to_sell = min(self.portfolio["btc_balance"], trade_amount / self.current_price)
            usdt_received = btc_to_sell * self.current_price
            
            self.portfolio["btc_balance"] -= btc_to_sell
            self.portfolio["usdt_balance"] += usdt_received
            
            trade_record = {
                "action": "SELL",
                "amount": round(btc_to_sell, 6),
                "price": round(self.current_price, 2),
                "value": round(usdt_received, 2),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"status": "insufficient_balance", "message": "余额不足"}
        
        self.trading_history.append(trade_record)
        return {"status": "executed", "trade": trade_record}
    
    def get_portfolio_status(self) -> Dict[str, Any]:
        """获取投资组合状态"""
        btc_value = self.portfolio["btc_balance"] * self.current_price
        total_value = btc_value + self.portfolio["usdt_balance"]
        
        return {
            "btc_balance": round(self.portfolio["btc_balance"], 6),
            "usdt_balance": round(self.portfolio["usdt_balance"], 2),
            "btc_value_usdt": round(btc_value, 2),
            "total_value": round(total_value, 2),
            "current_btc_price": round(self.current_price, 2)
        }
    
    def run_demo_cycle(self):
        """运行一个完整的演示周期"""
        print("🚀 比特币交易系统演示")
        print("=" * 50)
        
        # 模拟历史价格数据
        historical_prices = [self.current_price * (1 + random.uniform(-0.01, 0.01)) for _ in range(30)]
        
        for cycle in range(5):
            print(f"\n📊 第 {cycle + 1} 轮分析")
            print("-" * 30)
            
            # 1. 获取市场数据
            market_data = self.simulate_market_data()
            print(f"💰 当前价格: ${market_data['price']:,.2f} ({market_data['change_24h']:+.2f}%)")
            
            # 2. 新闻情绪分析
            sentiment = self.simulate_news_sentiment()
            print(f"📰 新闻: {sentiment['news_item']['title'][:40]}...")
            print(f"😊 情绪分数: {sentiment['overall_sentiment']}/100 ({sentiment['market_impact']})")
            
            # 3. 技术指标计算
            historical_prices.append(market_data['price'])
            technical = self.calculate_technical_indicators(historical_prices)
            print(f"📈 技术指标: RSI={technical['rsi']:.1f}, MACD={technical['macd']:.2f}")
            
            # 4. 生成交易决策
            decision = self.generate_trading_decision(sentiment, technical)
            print(f"🎯 交易决策: {decision['action']} (置信度: {decision['confidence']:.2f})")
            print(f"💭 决策理由: {decision['reasoning']}")
            
            # 5. 执行交易
            trade_result = self.execute_trade(decision)
            if trade_result["status"] == "executed":
                trade = trade_result["trade"]
                print(f"✅ 交易执行: {trade['action']} {trade['amount']} BTC @ ${trade['price']:,.2f}")
            else:
                print(f"⏸️  {trade_result['message']}")
            
            # 6. 显示投资组合状态
            portfolio = self.get_portfolio_status()
            print(f"💼 投资组合: {portfolio['btc_balance']} BTC + ${portfolio['usdt_balance']:,.2f} USDT")
            print(f"💎 总价值: ${portfolio['total_value']:,.2f}")
            
            time.sleep(2)  # 暂停2秒
        
        print("\n" + "=" * 50)
        print("📈 交易历史汇总")
        print("=" * 50)
        
        if self.trading_history:
            for i, trade in enumerate(self.trading_history, 1):
                print(f"{i}. {trade['action']} {trade['amount']} BTC @ ${trade['price']:,.2f} "
                      f"(价值: ${trade['value']:,.2f})")
        else:
            print("本次演示期间未执行任何交易")
        
        final_portfolio = self.get_portfolio_status()
        print(f"\n💰 最终投资组合价值: ${final_portfolio['total_value']:,.2f}")


def main():
    """主函数"""
    print("🎯 欢迎使用比特币交易系统演示")
    print("本演示将展示系统的核心功能：")
    print("• 实时市场数据收集")
    print("• AI驱动的新闻情绪分析") 
    print("• 技术指标计算")
    print("• 智能交易决策")
    print("• 风险管理和投资组合跟踪")
    print("\n按 Enter 开始演示...")
    input()
    
    # 创建演示系统实例
    demo_system = DemoTradingSystem()
    
    # 运行演示
    demo_system.run_demo_cycle()
    
    print("\n🎉 演示完成！")
    print("这只是一个简化的演示版本。")
    print("完整系统还包括：")
    print("• 真实的Binance API集成")
    print("• OpenAI GPT-4情绪分析")
    print("• 多源数据收集（Twitter、新闻网站）")
    print("• 高级风险管理")
    print("• 实时Web界面")
    print("• 历史数据回测")


if __name__ == "__main__":
    main()