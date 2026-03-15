#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - 新闻 API 客户端
News API Client for weighted sentiment straddle trading system

该模块负责与加权情绪新闻 API 交互，获取新闻数据并转换为结构化对象。
"""

import logging
from typing import List
from datetime import datetime
import aiohttp
import ssl

from weighted_sentiment_models import WeightedNews


# 配置日志
logger = logging.getLogger(__name__)


class NewsAPIClient:
    """新闻 API 客户端
    
    负责从加权情绪 API 获取新闻数据，处理网络请求、解析响应和错误处理。
    
    Attributes:
        api_url: 加权情绪新闻 API 的完整 URL
        timeout: HTTP 请求超时时间（秒）
        ssl_context: SSL 上下文配置
    """
    
    def __init__(
        self,
        api_url: str = "http://43.106.51.106:5002/api/weighted-sentiment/news",
        timeout: int = 30
    ):
        """初始化新闻 API 客户端
        
        Args:
            api_url: 加权情绪新闻 API 的 URL
            timeout: HTTP 请求超时时间（秒），默认 30 秒
        """
        self.api_url = api_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # 配置 SSL 上下文：验证证书
        self.ssl_context = ssl.create_default_context()
        # 注意：如果 API 使用 HTTP 而非 HTTPS，SSL 验证不会生效
        # 但我们仍然配置它以符合安全要求
        
        logger.info(f"NewsAPIClient 初始化完成，API URL: {self.api_url}")
    
    async def fetch_weighted_news(self) -> List[WeightedNews]:
        """获取加权情绪新闻列表
        
        从加权情绪 API 获取新闻数据，解析 JSON 响应并转换为 WeightedNews 对象列表。
        
        Returns:
            WeightedNews 对象列表。如果发生错误，返回空列表。
        
        网络错误处理：
        - 超时错误：记录警告并返回空列表
        - 连接错误：记录错误并返回空列表
        - HTTP 错误：记录错误并返回空列表
        - JSON 解析错误：记录错误并返回空列表
        - 数据验证错误：记录警告并跳过无效新闻项
        """
        try:
            logger.info(f"开始获取新闻数据，API URL: {self.api_url}")
            
            # 创建 HTTP 客户端会话
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # 发送 GET 请求
                # 注意：由于 API 使用 HTTP，我们不强制 SSL 验证
                # 但如果 URL 是 HTTPS，SSL 验证会自动生效
                async with session.get(
                    self.api_url,
                    ssl=self.ssl_context if self.api_url.startswith('https') else False
                ) as response:
                    # 检查 HTTP 状态码
                    if response.status != 200:
                        logger.error(
                            f"API 返回错误状态码: {response.status}, "
                            f"响应内容: {await response.text()}"
                        )
                        return []
                    
                    # 解析 JSON 响应
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError as e:
                        logger.error(f"JSON 解析失败: {e}")
                        return []
                    
                    # 处理不同的响应格式
                    # 如果响应是字典，尝试提取 'data' 或 'news' 字段
                    if isinstance(data, dict):
                        if 'data' in data:
                            data = data['data']
                            logger.info(f"从响应字典中提取 'data' 字段")
                            # 如果 data 还是字典，继续提取 'news' 字段
                            if isinstance(data, dict) and 'news' in data:
                                data = data['news']
                                logger.info(f"从 data 字典中提取 'news' 字段")
                        elif 'news' in data:
                            data = data['news']
                            logger.info(f"从响应字典中提取 'news' 字段")
                        else:
                            logger.error(f"API 响应是字典但不包含 'data' 或 'news' 字段: {list(data.keys())}")
                            return []
                    
                    # 验证响应数据格式
                    if not isinstance(data, list):
                        logger.error(f"API 响应格式错误：期望列表，实际类型: {type(data)}")
                        return []
                    
                    logger.info(f"成功获取 {len(data)} 条新闻数据")
                    
                    # 转换为 WeightedNews 对象列表
                    news_list = []
                    for item in data:
                        try:
                            news = self._parse_news_item(item)
                            news_list.append(news)
                        except (ValueError, KeyError, TypeError) as e:
                            # 跳过无效的新闻项，但继续处理其他项
                            logger.warning(f"跳过无效新闻项: {e}, 数据: {item}")
                            continue
                    
                    logger.info(f"成功解析 {len(news_list)} 条有效新闻")
                    return news_list
        
        except aiohttp.ClientConnectorError as e:
            logger.error(f"连接 API 失败: {e}")
            return []
        
        except aiohttp.ServerTimeoutError as e:
            logger.warning(f"API 请求超时: {e}")
            return []
        
        except asyncio.TimeoutError as e:
            logger.warning(f"API 请求超时: {e}")
            return []
        
        except Exception as e:
            logger.error(f"获取新闻数据时发生未预期错误: {e}", exc_info=True)
            return []
    
    def _parse_news_item(self, item: dict) -> WeightedNews:
        """解析单条新闻数据
        
        将 API 返回的字典数据转换为 WeightedNews 对象。
        
        Args:
            item: API 返回的新闻数据字典
        
        Returns:
            WeightedNews 对象
        
        Raises:
            KeyError: 如果缺少必需字段
            ValueError: 如果数据验证失败
            TypeError: 如果数据类型不正确
        """
        # API 字段映射
        # API 使用 'guid' 作为唯一标识，'title' 作为内容，'published_at' 作为时间戳
        news_id = item.get('guid') or item.get('news_id')
        content = item.get('title') or item.get('content')
        sentiment_raw = item.get('sentiment')
        importance_score = item.get('importance_score')
        timestamp_value = item.get('published_at') or item.get('pubDate') or item.get('timestamp')
        source = item.get('source')
        
        # 验证必需字段
        if not news_id:
            raise KeyError("缺少必需字段: guid 或 news_id")
        if not content:
            raise KeyError("缺少必需字段: title 或 content")
        if not sentiment_raw:
            raise KeyError("缺少必需字段: sentiment")
        if importance_score is None:
            raise KeyError("缺少必需字段: importance_score")
        if not timestamp_value:
            raise KeyError("缺少必需字段: published_at, pubDate 或 timestamp")
        
        # 情绪值映射：中文 -> 英文
        sentiment_mapping = {
            '积极': 'positive',
            '正面': 'positive',
            '负面': 'negative',
            '消极': 'negative',
            '中立': 'neutral',
            '未知': 'neutral',  # 将未知映射为中立
            # 英文值直接通过
            'positive': 'positive',
            'negative': 'negative',
            'neutral': 'neutral'
        }
        
        sentiment = sentiment_mapping.get(str(sentiment_raw).strip())
        if not sentiment:
            # 如果映射失败，记录警告并使用中立
            logger.warning(f"未知的情绪值: {sentiment_raw}，使用 'neutral' 作为默认值")
            sentiment = 'neutral'
        
        # 解析时间戳
        timestamp = self._parse_timestamp(timestamp_value)
        
        # 创建 WeightedNews 对象（会自动触发验证）
        news = WeightedNews(
            news_id=str(news_id),
            content=str(content),
            sentiment=sentiment,
            importance_score=int(importance_score),
            timestamp=timestamp,
            source=source  # 可选字段
        )
        
        return news
    
    def _parse_timestamp(self, timestamp_value) -> datetime:
        """解析时间戳
        
        支持多种时间戳格式：
        - ISO 8601 字符串格式
        - Unix 时间戳（秒）
        - datetime 对象
        
        Args:
            timestamp_value: 时间戳值（字符串、整数或 datetime 对象）
        
        Returns:
            datetime 对象
        
        Raises:
            ValueError: 如果时间戳格式无效
        """
        # 如果已经是 datetime 对象，直接返回
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        
        # 如果是字符串，尝试解析 ISO 8601 格式
        if isinstance(timestamp_value, str):
            try:
                # 尝试解析 ISO 8601 格式（支持带时区和不带时区）
                return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
            except ValueError:
                pass
            
            try:
                # 尝试解析常见的日期时间格式
                return datetime.strptime(timestamp_value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        
        # 如果是数字，尝试解析为 Unix 时间戳
        if isinstance(timestamp_value, (int, float)):
            try:
                return datetime.fromtimestamp(timestamp_value)
            except (ValueError, OSError):
                pass
        
        raise ValueError(f"无法解析时间戳: {timestamp_value}")


# 导入 asyncio 用于超时处理
import asyncio
