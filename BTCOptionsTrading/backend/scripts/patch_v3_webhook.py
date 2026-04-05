#!/usr/bin/env python3
"""在情绪服务器上运行：给 weight_extractor_v3 加 webhook 推送"""
import ast

f = '/root/odaily-news/weight_extractor_v3.py'
content = open(f, encoding='utf-8').read()

# 找到 save_results 末尾的 except 块
old = '        except Exception as e:\n            logger.error(f"保存结果失败 ({output_file}): {e}")\n    \n    def process_day'

new = '''        except Exception as e:
            logger.error(f"保存结果失败 ({output_file}): {e}")

        # Webhook: 推送新增高分新闻到交易服务器 (vXkaBDto 账户)
        if new_items:
            self._push_webhook_v3(new_items)

    def _push_webhook_v3(self, items):
        WEBHOOK_URL = "http://47.86.62.200:5004/webhook/news-v3"
        MIN_SCORE = 6.0
        high = []
        for item in items:
            score = item.get("importance_score", 0)
            try:
                if float(score) >= MIN_SCORE:
                    high.append({
                        "guid": item.get("guid", ""),
                        "title": item.get("title", ""),
                        "published_at": item.get("published_at", item.get("pubDate", "")),
                        "sentiment": item.get("sentiment", ""),
                        "importance_score": float(score),
                        "capital_flow_directness": item.get("capital_flow_directness", ""),
                        "capital_flow_directness_score": item.get("capital_flow_directness_score", 0),
                        "market_expectation_gap": item.get("market_expectation_gap", ""),
                        "market_expectation_gap_score": item.get("market_expectation_gap_score", 0),
                        "time_urgency": item.get("time_urgency", ""),
                        "time_urgency_score": item.get("time_urgency_score", 0),
                        "event_category": item.get("event_category", ""),
                        "has_similar_high_scores": item.get("has_similar_high_scores", False),
                    })
            except Exception:
                pass
        if not high:
            return
        import urllib.request, json as _json
        try:
            body = _json.dumps({"news": high, "source": "v3"}).encode("utf-8")
            req = urllib.request.Request(WEBHOOK_URL, data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                logger.info(f"Webhook v3 推送: {len(high)} 条 -> {resp.status}")
        except Exception as e:
            logger.warning(f"Webhook v3 推送失败: {e}")

    def process_day'''

if old in content:
    content = content.replace(old, new)
    open(f, 'w', encoding='utf-8').write(content)
    print('✓ webhook 已加入 v3')
else:
    # 尝试找到实际的字符串
    idx = content.find('保存结果失败')
    if idx >= 0:
        print('找到"保存结果失败"，附近内容:')
        print(repr(content[idx-100:idx+150]))
    else:
        print('✗ 未找到目标字符串')
    exit(1)

try:
    ast.parse(content)
    print('✓ 语法正常')
except SyntaxError as e:
    print(f'语法错误 Line {e.lineno}: {e.msg}')
