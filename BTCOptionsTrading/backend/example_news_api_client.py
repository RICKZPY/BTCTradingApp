#!/usr/bin/env python3
"""
示例：使用 NewsAPIClient 获取加权情绪新闻
Example: Using NewsAPIClient to fetch weighted sentiment news
"""

import asyncio
import logging
from weighted_sentiment_api_client import NewsAPIClient


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """主函数：演示如何使用 NewsAPIClient"""
    
    print("=" * 60)
    print("NewsAPIClient 使用示例")
    print("=" * 60)
    
    # 创建客户端实例
    client = NewsAPIClient()
    print(f"\n1. 创建客户端")
    print(f"   API URL: {client.api_url}")
    print(f"   超时时间: {client.timeout.total} 秒")
    
    # 获取新闻数据
    print(f"\n2. 获取新闻数据...")
    news_list = await client.fetch_weighted_news()
    
    # 显示结果
    print(f"\n3. 结果:")
    print(f"   获取到 {len(news_list)} 条新闻")
    
    if news_list:
        print(f"\n4. 新闻详情:")
        for i, news in enumerate(news_list[:5], 1):  # 只显示前5条
            print(f"\n   新闻 {i}:")
            print(f"   - ID: {news.news_id}")
            print(f"   - 内容: {news.content[:80]}...")
            print(f"   - 情绪: {news.sentiment}")
            print(f"   - 重要性评分: {news.importance_score}/10")
            print(f"   - 时间: {news.timestamp}")
            if news.source:
                print(f"   - 来源: {news.source}")
        
        if len(news_list) > 5:
            print(f"\n   ... 还有 {len(news_list) - 5} 条新闻")
        
        # 筛选高分新闻
        high_score_news = [n for n in news_list if n.importance_score >= 7]
        print(f"\n5. 高分新闻（评分 >= 7）:")
        print(f"   共 {len(high_score_news)} 条")
        
        for news in high_score_news:
            print(f"   - [{news.importance_score}分] {news.content[:60]}...")
    else:
        print("   API 返回空列表（可能暂时无数据）")
    
    print(f"\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == '__main__':
    # 运行示例
    asyncio.run(main())
