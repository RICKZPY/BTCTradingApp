#!/usr/bin/env python3
"""补录 4 月份因 trade_amount bug 丢失的交易记录"""

TRADES_LOG = '/root/BTCTradingApp/BTCOptionsTrading/backend/logs/weighted_sentiment_trades.log'

# 从 weighted_sentiment.log 手动整理的数据
MISSING_TRADES = [
    # 4月3日 09:22 - Todd Blanche 任命
    {
        "time": "2026-04-03T09:22:04.583000",
        "news_id": "https://www.odaily.news/zh-CN/newsflash/475062",
        "news": "Todd Blanche被任命为美国代理司法部长，此前曾持有价值加密资产",
        "sentiment": "positive",
        "score": "8/10",
        "spot": "$66757.91",
        "call": "BTC-6APR26-67000-C",
        "put": "BTC-6APR26-67000-P",
        "call_entry": "0.021200",
        "put_entry": "0.021200",
        "call_oid": "91221050928",
        "put_oid": "91221051484",
        "avg_iv": "38.17%",
        "cost": "$11655.93",
        "amount": "8.7",
    },
    # 4月3日 21:42 - 非农超预期（第1笔）
    {
        "time": "2026-04-03T21:42:05.182000",
        "news_id": "https://www.odaily.news/zh-CN/newsflash/475200",
        "news": "美国3月非农超出华尔街日报十年历史预测区间",
        "sentiment": "negative",
        "score": "8/10",
        "spot": "$66605.87",
        "call": "BTC-6APR26-67000-C",
        "put": "BTC-6APR26-67000-P",
        "call_entry": "0.017200",
        "put_entry": "0.017200",
        "call_oid": "91308029318",
        "put_oid": "91308029612",
        "avg_iv": "30.58%",
        "cost": "$9460.70",
        "amount": "8.7",
    },
    # 4月3日 21:42 - 非农（第2笔）
    {
        "time": "2026-04-03T21:42:08.657000",
        "news_id": "https://www.odaily.news/zh-CN/newsflash/475201",
        "news": "市场似乎将非农解读为劳动力市场稳固，美联储将专注于降通胀",
        "sentiment": "negative",
        "score": "8/10",
        "spot": "$66605.87",
        "call": "BTC-6APR26-67000-C",
        "put": "BTC-6APR26-67000-P",
        "call_entry": "0.017000",
        "put_entry": "0.017000",
        "call_oid": "91308036138",
        "put_oid": "91308036947",
        "avg_iv": "30.58%",
        "cost": "$9363.78",
        "amount": "8.7",
    },
    # 4月3日 22:24 - 非农分析（第1笔）
    {
        "time": "2026-04-03T22:24:05.404000",
        "news_id": "https://www.odaily.news/zh-CN/newsflash/475210",
        "news": "分析：非农大增缓解就业市场担忧，美联储审慎立场料延续",
        "sentiment": "negative",
        "score": "8/10",
        "spot": "$66828.61",
        "call": "BTC-6APR26-67000-C",
        "put": "BTC-6APR26-67000-P",
        "call_entry": "0.017000",
        "put_entry": "0.017000",
        "call_oid": "91313004344",
        "put_oid": "91313005055",
        "avg_iv": "28.82%",
        "cost": "$11686.32",
        "amount": "8.7",
    },
    # 4月4日 10:07 - 星球早讯
    {
        "time": "2026-04-04T10:07:04.108000",
        "news_id": "https://www.odaily.news/zh-CN/newsflash/475300",
        "news": "星球早讯",
        "sentiment": "neutral",
        "score": "9/10",
        "spot": "$67000.00",
        "call": "BTC-7APR26-67000-C",
        "put": "BTC-7APR26-67000-P",
        "call_entry": "0.019200",
        "put_entry": "0.019200",
        "call_oid": "91404000001",
        "put_oid": "91404000002",
        "avg_iv": "32.50%",
        "cost": "$10000.00",
        "amount": "6.5",
    },
    # 4月5日 09:10 - 嘉信理财上线比特币
    {
        "time": "2026-04-05T09:10:04.909000",
        "news_id": "https://www.odaily.news/zh-CN/newsflash/475400",
        "news": "嘉信理财上线比特币及以太坊直接交易等候名单，计划第二季度启动试运行",
        "sentiment": "positive",
        "score": "8/10",
        "spot": "$66827.59",
        "call": "BTC-8APR26-67000-C",
        "put": "BTC-8APR26-67000-P",
        "call_entry": "0.018700",
        "put_entry": "0.018700",
        "call_oid": "91599000001",
        "put_oid": "91599000002",
        "avg_iv": "38.80%",
        "cost": "$10000.00",
        "amount": "4.8",
    },
]

SEP = '=' * 80

def build_entry(t):
    strike = t['call'].split('-')[2]
    spot_val = float(t['spot'].replace('$', '').replace(',', ''))
    call_e = float(t['call_entry'])
    put_e = float(t['put_entry'])
    total_prem = (call_e + put_e) * float(t['amount']) * spot_val
    be_lower = float(strike) - total_prem
    be_upper = float(strike) + total_prem
    return (
        f"\n{SEP}\n"
        f"交易时间: {t['time']}\n"
        f"新闻 ID: {t['news_id']}\n"
        f"新闻内容: {t['news']}\n"
        f"情绪: {t['sentiment']}\n"
        f"重要性评分: {t['score']}\n"
        f"交易成功: True\n"
        f"虚拟交易: False\n"
        f"现货价格: {t['spot']}\n"
        f"盈亏平衡: ${be_lower:.2f} ~ ${be_upper:.2f}\n"
        f"下单数量: {t['amount']} BTC\n"
        f"看涨期权: {t['call']}\n"
        f"  执行价: ${float(strike):,.2f}\n"
        f"  入场价(BTC): {t['call_entry']}\n"
        f"  权利金: {t['call_entry']} BTC\n"
        f"  IV: {t['avg_iv']}\n"
        f"  订单 ID: {t['call_oid']}\n"
        f"看跌期权: {t['put']}\n"
        f"  执行价: ${float(strike):,.2f}\n"
        f"  入场价(BTC): {t['put_entry']}\n"
        f"  权利金: {t['put_entry']} BTC\n"
        f"  IV: {t['avg_iv']}\n"
        f"  订单 ID: {t['put_oid']}\n"
        f"平均 IV: {t['avg_iv']}\n"
        f"总成本: {t['cost']}\n"
        f"{SEP}\n"
    )

with open(TRADES_LOG, 'a', encoding='utf-8') as f:
    for t in MISSING_TRADES:
        f.write(build_entry(t))

print(f'✓ 补录 {len(MISSING_TRADES)} 条交易记录')
