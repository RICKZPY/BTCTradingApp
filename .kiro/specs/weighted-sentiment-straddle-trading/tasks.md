# 实现计划：加权情绪跨式期权交易

## 概述

基于现有 Sentiment_Trading_Quickstart 系统，实现一个使用加权情绪新闻 API 的自动化跨式期权交易服务。系统每小时检查新闻 API，识别高重要性评分（≥7分）的新闻，自动买入 ATM Straddle 期权组合。

## 任务

- [x] 1. 创建数据模型和验证逻辑
  - [x] 1.1 实现 WeightedNews 数据类
    - 创建 dataclass 包含所有必需字段（news_id、content、sentiment、importance_score、timestamp、source）
    - 实现验证方法：importance_score 范围 1-10，sentiment 为有效值，news_id 非空
    - _需求：8.1, 8.2, 8.3_
  
  - [x] 1.2 为 WeightedNews 编写属性测试
    - **属性 6: 数据验证完整性**
    - **验证需求：8.1, 8.2, 8.3**
  
  - [x] 1.3 实现 OptionTrade 数据类
    - 创建 dataclass 包含期权交易详情（instrument_name、option_type、strike_price、expiry_date、premium、quantity、order_id）
    - 实现验证方法：strike_price/premium/quantity 为正数，expiry_date 在未来，option_type 为 "call" 或 "put"
    - _需求：8.4, 8.5_
  
  - [x] 1.4 为 OptionTrade 编写属性测试
    - **属性 7: 期权交易验证**
    - **验证需求：8.4, 8.5**
  
  - [x] 1.5 实现 StraddleTradeResult 和 TradeRecord 数据类
    - 创建 StraddleTradeResult 包含交易结果信息
    - 创建 TradeRecord 包含完整的交易记录信息
    - _需求：4.6, 5.2_

- [x] 2. 实现 NewsAPIClient 组件
  - [x] 2.1 创建 NewsAPIClient 类
    - 实现 fetch_weighted_news() 异步方法
    - 配置 HTTP 客户端（aiohttp）使用 HTTPS、SSL 验证、超时设置
    - 解析 JSON 响应并转换为 WeightedNews 对象列表
    - 处理网络错误、超时和 API 错误，返回空列表
    - _需求：1.1, 1.2, 1.3, 1.4, 1.5, 12.3, 12.4, 12.5_
  
  - [x] 2.2 为 NewsAPIClient 编写单元测试
    - 使用 mock 测试 API 响应解析
    - 测试错误处理（超时、网络错误、无效响应）
    - _需求：1.4, 7.1_

- [x] 3. 实现 NewsTracker 组件
  - [x] 3.1 创建 NewsTracker 类和数据库初始化
    - 创建 SQLite 数据库连接（weighted_news_history.db）
    - 创建新闻历史表（news_id、timestamp、importance_score）
    - 在 news_id 和 timestamp 字段上创建索引
    - _需求：2.1, 11.3_
  
  - [x] 3.2 实现新闻去重和筛选逻辑
    - 实现 identify_new_news() 方法：查询数据库识别未处理的新闻
    - 筛选 importance_score >= 7 的新闻
    - 实现 is_news_processed() 方法：检查 news_id 是否存在
    - _需求：2.1, 2.2, 2.3_
  
  - [x] 3.3 实现新闻历史更新
    - 实现 update_history() 方法：保存新闻 news_id 和 timestamp 到数据库
    - 使用事务确保数据一致性
    - _需求：2.4_
  
  - [x] 3.4 为 NewsTracker 编写属性测试
    - **属性 1: 无重复交易**
    - **属性 2: 评分阈值强制执行**
    - **属性 14: 新闻历史持久化**
    - **验证需求：2.2, 2.3, 2.4, 2.5**
  
  - [x] 3.5 为 NewsTracker 编写单元测试
    - 测试边界情况（评分 6、7、8）
    - 测试数据库操作（插入、查询、去重）
    - _需求：2.5_

- [x] 4. 实现 StraddleExecutor 组件
  - [x] 4.1 创建 StraddleExecutor 类
    - 初始化 DeribitTrader 连接（复用现有代码）
    - 从环境变量读取独立的 Deribit 凭证（WEIGHTED_SENTIMENT_DERIBIT_API_KEY 和 WEIGHTED_SENTIMENT_DERIBIT_API_SECRET）
    - 确保使用与现有 sentiment_trading_service 不同的账户
    - _需求：4.1, 12.1, 12.2_
  
  - [x] 4.2 实现 ATM 期权查找逻辑
    - 实现 find_atm_options() 方法：获取 BTC 指数价格
    - 查询 Deribit API 获取可用期权列表
    - 筛选到期日在 7 天后（±1天）的期权
    - 选择执行价格最接近现货价格的看涨和看跌期权
    - 确保两个期权执行价格相同
    - 如果找不到合适期权，抛出 NoSuitableOptionsError
    - _需求：3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.3 为 find_atm_options 编写属性测试
    - **属性 13: ATM 期权选择最优性**
    - **验证需求：3.3**
  
  - [x] 4.4 实现跨式期权交易执行逻辑
    - 实现 execute_straddle() 方法：获取现货价格
    - 调用 find_atm_options() 查找期权
    - 买入看涨期权（数量 0.1 BTC）
    - 买入看跌期权（数量 0.1 BTC）
    - 如果看跌期权失败，尝试平仓看涨期权
    - 计算总成本（call_premium + put_premium）
    - 返回 StraddleTradeResult 对象
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [x] 4.5 为 execute_straddle 编写属性测试
    - **属性 3: 跨式完整性**
    - **属性 15: 跨式成本计算**
    - **验证需求：3.4, 4.5**
  
  - [x] 4.6 为 StraddleExecutor 编写单元测试
    - 测试部分执行失败的回滚逻辑
    - 测试找不到合适期权的错误处理
    - _需求：3.5, 7.2, 7.3_

- [x] 5. 实现 TradeLogger 组件
  - [x] 5.1 创建 TradeLogger 类和数据库初始化
    - 创建 SQLite 数据库连接（weighted_trade_records.db）
    - 创建交易记录表（包含新闻信息、期权详情、交易结果）
    - 在 trade_time 字段上创建索引
    - _需求：5.1, 11.3_
  
  - [x] 5.2 实现交易记录保存逻辑
    - 实现 log_trade() 方法：保存新闻完整信息（news_id、content、sentiment、importance_score）
    - 保存期权详情（instrument_name、strike_price、premium、expiry_date）
    - 保存交易时的现货价格和时间戳
    - 保存成功/失败状态和错误信息
    - 使用事务确保数据一致性
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 5.3 实现交易历史查询逻辑
    - 实现 get_trade_history() 方法：支持按日期范围查询
    - 返回 TradeRecord 对象列表
    - 按交易时间降序排列结果
    - 未指定日期范围时返回所有记录
    - 查询结果为空时返回空列表
    - _需求：9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 5.4 为 TradeLogger 编写属性测试
    - **属性 4: 交易-新闻关联**
    - **属性 8: 交易记录持久化往返**
    - **属性 9: 查询结果排序**
    - **验证需求：5.2, 5.6, 9.5**
  
  - [x] 5.5 为 TradeLogger 编写单元测试
    - 测试数据库事务和错误处理
    - 测试查询边界情况（空结果、日期范围）
    - _需求：5.6, 9.4_

- [x] 6. 实现 WeightedSentimentService 主服务
  - [x] 6.1 创建 WeightedSentimentService 类
    - 初始化所有组件（NewsAPIClient、NewsTracker、StraddleExecutor、TradeLogger）
    - 从环境变量读取独立的 Deribit 凭证（WEIGHTED_SENTIMENT_DERIBIT_API_KEY 和 WEIGHTED_SENTIMENT_DERIBIT_API_SECRET）
    - 配置日志记录器（文件路径、格式、级别）
    - 验证所有必需配置项（API 端点、数据库路径、独立的 Deribit 凭证）
    - 如果凭证缺失，记录错误并拒绝启动
    - _需求：6.1, 10.3, 10.4, 10.5, 13.3, 13.4, 13.5_
  
  - [x] 6.2 实现每小时检查逻辑
    - 实现 hourly_check() 方法：调用 NewsAPIClient 获取新闻
    - 调用 NewsTracker 识别新增高分新闻
    - 对每条新闻调用 StraddleExecutor 执行交易
    - 调用 TradeLogger 记录交易结果
    - 调用 NewsTracker 更新新闻历史
    - 记录所有关键操作到日志
    - _需求：6.2, 6.3, 10.3_
  
  - [x] 6.3 实现定时任务调度
    - 实现 run() 方法：使用 asyncio 创建定时任务
    - 每小时触发一次 hourly_check()
    - 确保执行间隔误差不超过 ±5 秒
    - 记录每次触发时间到日志
    - _需求：6.1, 6.2, 6.3, 6.4_
  
  - [x] 6.4 实现错误处理和恢复逻辑
    - 捕获 API 不可用错误，记录并跳过本次周期
    - 捕获找不到期权错误，记录警告并继续下一条新闻
    - 捕获数据库错误，暂停交易并尝试重连
    - 捕获 Deribit 认证错误，停止交易并发送告警
    - 记录详细错误堆栈到日志
    - 确保单个错误不会导致服务停止
    - _需求：7.1, 7.2, 7.3, 7.4, 7.5, 10.3_
  
  - [x] 6.5 为 WeightedSentimentService 编写属性测试
    - **属性 5: 每小时执行频率**
    - **验证需求：6.2, 6.4**

- [x] 7. 检查点 - 确保核心功能测试通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 8. 实现服务状态监控 API
  - [x] 8.1 创建 HTTP API 服务
    - 使用 aiohttp 创建 HTTP 服务器（端口 5003）
    - 实现 /api/status 端点
    - 返回最后检查时间、处理的新闻数量、执行的交易数量
    - _需求：10.1, 10.2_
  
  - [x] 8.2 实现日志安全性检查
    - 确保日志不包含 API 密钥或敏感信息
    - 实现日志消息过滤器
    - _需求：12.2_
  
  - [x] 8.3 为监控 API 编写属性测试
    - **属性 10: 日志完整性**
    - **属性 11: 敏感信息保护**
    - **验证需求：10.3, 10.4, 12.2**

- [x] 9. 创建部署脚本和配置文件
  - [x] 9.1 创建启动和停止脚本
    - 创建 start_weighted_sentiment.sh：启动服务脚本
    - 创建 stop_weighted_sentiment.sh：停止服务脚本
    - 添加执行权限
    - _需求：13.2_
  
  - [x] 9.2 创建 systemd 服务配置
    - 创建 weighted_sentiment.service 文件
    - 配置服务自动重启和日志管理
    - _需求：13.1_
  
  - [x] 9.3 创建数据目录和日志目录
    - 创建 data/ 目录用于存储数据库文件
    - 创建 logs/ 目录用于存储日志文件
    - 设置适当的文件权限
    - _需求：10.5_

- [x] 10. 集成测试和文档
  - [x] 10.1 编写端到端集成测试
    - 使用 mock API 测试完整工作流程
    - 使用 Deribit testnet 测试真实交易
    - 测试数据库持久化和服务重启
    - _需求：所有需求_
  
  - [x] 10.2 创建快速入门文档
    - 编写部署步骤说明
    - 编写配置说明（环境变量、API 端点）
    - 明确说明需要配置独立的 Deribit Test 账户凭证：
      - WEIGHTED_SENTIMENT_DERIBIT_API_KEY
      - WEIGHTED_SENTIMENT_DERIBIT_API_SECRET
    - 编写监控和故障排查指南
    - _需求：13.2, 13.3, 13.4_

- [x] 11. 最终检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

## 注意事项

- 标记 `*` 的任务为可选任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号以确保可追溯性
- 检查点任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证特定示例和边界情况
- 使用 Python 3.7+ 和 asyncio 实现所有异步操作
- 复用现有 DeribitTrader 和日志基础设施
- 遵循现有 sentiment_trading_service.py 的代码风格和模式
