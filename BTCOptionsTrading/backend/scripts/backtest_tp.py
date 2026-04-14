#!/usr/bin/env python3
"""回测止盈策略效果"""
import json, sqlite3
from datetime import datetime, timezone

impact = json.loads(open('/root/BTCTradingApp/BTCOptionsTrading/backend/data/news_impact.json').read())
iv_db = '/root/BTCTradingApp/BTCOptionsTrading/backend/data/iv_history.db'
conn = sqlite3.connect(iv_db)

TP_IV_PCT = 0.50   # IV 相对涨幅 50%
TP_PNL_PCT = 0.10  # PnL 涨幅 10%

results = []
for key, item in impact.items():
    call_inst = item.get('call_instrument', '')
    trade_time = item.get('trade_time', '')[:16]
    spot_at_trade = item.get('spot_at_trade', 0)
    call_entry = item.get('call_entry_btc', 0) or 0
    put_entry = item.get('put_entry_btc', 0) or 0
    if not call_inst or not spot_at_trade or not call_entry:
        continue
    try:
        t0 = datetime.fromisoformat(trade_time).replace(tzinfo=timezone.utc)
        t0_ts = int(t0.timestamp())
    except:
        continue

    rows = conn.execute(
        "SELECT ts, mark_iv, mark_price FROM iv_snapshots WHERE instrument=? AND ts BETWEEN ? AND ? ORDER BY ts",
        (call_inst, t0_ts, t0_ts + 72*3600)
    ).fetchall()

    if len(rows) < 2:
        continue

    iv0 = rows[0][1]
    entry_cost = (call_entry + put_entry) * 0.1 * spot_at_trade

    tp_time = None
    tp_pnl = None
    tp_reason = None
    final_pnl = None

    for ts, iv, price in rows[1:]:
        if not iv or not price:
            continue
        current_value = price * 2 * 0.1 * spot_at_trade
        pnl_pct = (current_value - entry_cost) / entry_cost if entry_cost > 0 else 0
        iv_chg_pct = (iv - iv0) / iv0 if iv0 > 0 else 0
        final_pnl = pnl_pct

        if tp_time is None:
            if iv_chg_pct >= TP_IV_PCT:
                tp_time = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
                tp_pnl = pnl_pct
                tp_reason = 'IV+{:.0f}%'.format(iv_chg_pct*100)
                break
            if pnl_pct >= TP_PNL_PCT:
                tp_time = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
                tp_pnl = pnl_pct
                tp_reason = 'PnL+{:.0f}%'.format(pnl_pct*100)
                break

    if tp_time and final_pnl is not None:
        results.append({
            'inst': call_inst[:22],
            'tp_time': tp_time,
            'tp_pnl': tp_pnl,
            'tp_reason': tp_reason,
            'final_pnl': final_pnl,
            'saved': tp_pnl - final_pnl
        })

conn.close()

print('触发止盈的持仓: {} 条'.format(len(results)))
if results:
    saved_pos = [r['saved'] for r in results if r['saved'] > 0]
    print('止盈后比持有到底多赚（正值）: {} 条，平均 {:.1f}%'.format(
        len(saved_pos), sum(saved_pos)/len(saved_pos)*100 if saved_pos else 0))
    print()
    print('=== 止盈效果最显著的案例 ===')
    for r in sorted(results, key=lambda x: x['saved'], reverse=True)[:10]:
        print('  {} | @{} ({}) tp={:+.1f}% final={:+.1f}% saved={:+.1f}%'.format(
            r['inst'], r['tp_time'], r['tp_reason'],
            r['tp_pnl']*100, r['final_pnl']*100, r['saved']*100))
