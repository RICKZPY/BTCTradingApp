# 需求文档：加权情绪跨式期权交易

## 简介

本系统基于加权情绪新闻 API，实现自动化的跨式期权交易策略。系统每小时检查新闻 API，识别高重要性评分（≥7分）的新闻，无论情绪方向如何，都自动买入 ATM（平值）Straddle 期权组合。核心假设是高分新闻会引发更大的市场波动，使得跨式期权策略更有可能盈利。

## 术语表

- **System**: 加权情绪跨式期权交易系统
- **NewsAPIClient**: 新闻 API 客户端组件
- **NewsTracker**: 新闻跟踪器组件
- **StraddleExecutor**: 跨式期权执行器组件
- **TradeLogger**: 交易日志记录器组件
- **WeightedNews**: 加权情绪新闻数据对象
- **StraddleTradeResult**: 跨式交易结果对象
- **ATM_Option**: 平值期权（执行价格接近当前市场价格的期权）
- **Straddle**: 跨式期权策略（同时买入相同执行价和到期日的看涨和看跌期权）
- **Importance_Score**: 新闻重要性评分（1-10分）
- **High_Score_News**: 重要性评分 ≥ 7 的新闻
- **Deribit_API**: Deribit 交易所 API 接口
- **News_History_Database**: 新闻历史记录数据库
- **Trade_Records_Database**: 交易记录数据库

## 需求

### 需求 1：新闻数据获取

**用户故事：** 作为系统，我需要定期从加权情绪 API 获取新闻数据，以便识别可能引发市场波动的重要新闻。

#### 验收标准

1. WHEN 系统启动时，THE NewsAPIClient SHALL 建立与加权情绪 API 的连接
2. WHEN 每小时触发检查时，THE NewsAPIClient SHALL 向 API 端点发送 HTTP GET 请求
3. WHEN API 返回响应时，THE NewsAPIClient SHALL 解析 JSON 数据并转换为 WeightedNews 对象列表
4. IF API 请求超时或返回错误，THEN THE NewsAPIClient SHALL 记录错误并返回空列表
5. WHEN 解析新闻数据时，THE NewsAPIClient SHALL 验证每条新闻包含必需字段（news_id、content、sentiment、importance_score、timestamp）

### 需求 2：新闻去重与筛选

**用户故事：** 作为系统，我需要识别新增的高分新闻并避免重复处理，以确保每条新闻只触发一次交易。

#### 验收标准

1. WHEN 接收到新闻列表时，THE NewsTracker SHALL 查询 News_History_Database 以识别未处理的新闻
2. WHEN 筛选新闻时，THE NewsTracker SHALL 仅保留 importance_score >= 7 的新闻
3. WHEN 检查新闻是否已处理时，THE NewsTracker SHALL 使用 news_id 作为唯一标识符
4. WHEN 完成新闻处理后，THE NewsTracker SHALL 将所有新闻的 news_id 和 timestamp 保存到 News_History_Database
5. THE NewsTracker SHALL 确保同一 news_id 不会被返回多次

### 需求 3：ATM 期权查找

**用户故事：** 作为交易执行器，我需要找到接近当前市场价格的期权合约，以便构建跨式期权组合。

#### 验收标准

1. WHEN 需要查找 ATM 期权时，THE StraddleExecutor SHALL 首先从 Deribit_API 获取当前 BTC 指数价格
2. WHEN 查询可用期权时，THE StraddleExecutor SHALL 筛选到期日在 7 天后（±1天）的期权合约
3. WHEN 选择期权时，THE StraddleExecutor SHALL 找到执行价格最接近当前指数价格的看涨和看跌期权
4. THE StraddleExecutor SHALL 确保选中的看涨和看跌期权具有相同的执行价格
5. IF 找不到符合条件的期权合约，THEN THE StraddleExecutor SHALL 抛出 NoSuitableOptionsError 异常

### 需求 4：跨式期权交易执行

**用户故事：** 作为系统，我需要为每条高分新闻执行跨式期权交易，以验证新闻评分与市场波动的关联性。

#### 验收标准

1. WHEN 识别到 High_Score_News 时，THE StraddleExecutor SHALL 执行跨式期权交易
2. WHEN 执行交易时，THE StraddleExecutor SHALL 首先买入看涨期权（数量 0.1 BTC）
3. WHEN 看涨期权买入成功后，THE StraddleExecutor SHALL 买入相同执行价和到期日的看跌期权（数量 0.1 BTC）
4. IF 看跌期权买入失败，THEN THE StraddleExecutor SHALL 尝试平仓已买入的看涨期权
5. WHEN 两个期权都买入成功时，THE StraddleExecutor SHALL 计算总成本（看涨期权费 + 看跌期权费）
6. THE StraddleExecutor SHALL 返回包含完整交易信息的 StraddleTradeResult 对象

### 需求 5：交易记录与关联

**用户故事：** 作为数据分析人员，我需要完整记录每笔交易与触发新闻的关联信息，以便后续分析新闻评分的准确性。

#### 验收标准

1. WHEN 交易执行完成时（无论成功或失败），THE TradeLogger SHALL 记录交易信息到 Trade_Records_Database
2. WHEN 记录交易时，THE TradeLogger SHALL 保存新闻的完整信息（news_id、content、sentiment、importance_score）
3. WHEN 记录交易时，THE TradeLogger SHALL 保存期权详情（instrument_name、strike_price、premium、expiry_date）
4. WHEN 记录交易时，THE TradeLogger SHALL 保存交易时的 BTC 现货价格和交易时间戳
5. IF 交易失败，THEN THE TradeLogger SHALL 记录错误信息到 error_message 字段
6. THE TradeLogger SHALL 确保数据库事务成功提交后才返回

### 需求 6：定时任务调度

**用户故事：** 作为系统运维人员，我需要系统每小时自动检查新闻并执行交易，无需人工干预。

#### 验收标准

1. WHEN 系统启动时，THE System SHALL 初始化定时任务调度器
2. THE System SHALL 每小时触发一次新闻检查和交易流程
3. WHEN 定时任务触发时，THE System SHALL 记录触发时间到日志
4. WHILE 系统运行中，THE System SHALL 确保定时任务的执行间隔误差不超过 ±5 秒
5. IF 某次定时任务执行失败，THEN THE System SHALL 记录错误但继续下一次调度

### 需求 7：错误处理与恢复

**用户故事：** 作为系统，我需要优雅地处理各种错误情况，确保单个错误不会导致整个服务停止。

#### 验收标准

1. IF 加权情绪 API 不可用或超时，THEN THE System SHALL 记录错误并跳过本次检查周期
2. IF 找不到合适的 ATM 期权，THEN THE System SHALL 记录警告并跳过该新闻的交易
3. IF 数据库连接失败，THEN THE System SHALL 暂停交易操作并尝试重新连接
4. IF Deribit_API 认证失败，THEN THE System SHALL 停止交易操作并发送告警通知
5. WHEN 发生异常时，THE System SHALL 记录详细的错误堆栈信息到日志文件

### 需求 8：数据验证与完整性

**用户故事：** 作为系统，我需要验证所有输入数据的有效性，确保数据完整性和一致性。

#### 验收标准

1. WHEN 解析 WeightedNews 对象时，THE System SHALL 验证 importance_score 在 1-10 范围内
2. WHEN 解析 WeightedNews 对象时，THE System SHALL 验证 sentiment 为 "positive"、"negative" 或 "neutral" 之一
3. WHEN 解析 WeightedNews 对象时，THE System SHALL 验证 news_id 非空且唯一
4. WHEN 创建 OptionTrade 对象时，THE System SHALL 验证 strike_price、premium 和 quantity 为正数
5. WHEN 创建 OptionTrade 对象时，THE System SHALL 验证 expiry_date 在未来时间

### 需求 9：交易历史查询

**用户故事：** 作为数据分析人员，我需要查询历史交易记录，以便分析策略表现和新闻评分的有效性。

#### 验收标准

1. THE TradeLogger SHALL 提供按日期范围查询交易记录的接口
2. WHEN 查询交易历史时，THE TradeLogger SHALL 返回包含完整新闻和交易信息的 TradeRecord 列表
3. WHERE 未指定日期范围，THE TradeLogger SHALL 返回所有历史记录
4. WHEN 查询结果为空时，THE TradeLogger SHALL 返回空列表而非抛出异常
5. THE TradeLogger SHALL 按交易时间降序排列查询结果

### 需求 10：服务状态监控

**用户故事：** 作为系统运维人员，我需要实时监控服务运行状态，以便及时发现和处理问题。

#### 验收标准

1. THE System SHALL 提供 HTTP API 端点用于查询服务状态
2. WHEN 查询服务状态时，THE System SHALL 返回最后一次检查时间、处理的新闻数量和执行的交易数量
3. THE System SHALL 记录所有关键操作到日志文件（包括 API 调用、交易执行、错误信息）
4. WHEN 记录日志时，THE System SHALL 包含时间戳、日志级别和详细消息
5. THE System SHALL 将日志文件保存到 logs/weighted_sentiment.log

### 需求 11：资源优化

**用户故事：** 作为系统运维人员，我需要系统在有限的服务器资源下高效运行，避免过度消耗 CPU 和内存。

#### 验收标准

1. THE System SHALL 使用异步 I/O（asyncio）处理所有网络请求
2. THE System SHALL 复用 HTTP 连接以减少连接开销
3. THE System SHALL 使用 SQLite 数据库索引优化查询性能（索引 news_id 和 timestamp 字段）
4. THE System SHALL 避免一次性加载所有历史数据到内存
5. WHILE 系统运行时，THE System SHALL 保持内存使用量低于 100 MB

### 需求 12：安全性

**用户故事：** 作为系统管理员，我需要确保敏感信息（如 API 密钥）得到妥善保护，避免泄露。

#### 验收标准

1. THE System SHALL 从环境变量或 .env 文件读取独立的 Deribit API 凭证（WEIGHTED_SENTIMENT_DERIBIT_API_KEY 和 WEIGHTED_SENTIMENT_DERIBIT_API_SECRET）
2. THE System SHALL 使用与现有 sentiment_trading_service 不同的 Deribit Test 账户
3. THE System SHALL 不在日志中记录 API 密钥或其他敏感信息
4. WHEN 与外部 API 通信时，THE System SHALL 使用 HTTPS 协议
5. WHEN 与外部 API 通信时，THE System SHALL 验证 SSL 证书
6. THE System SHALL 为所有 HTTP 请求设置超时时间（防止无限等待）

### 需求 13：部署与启动

**用户故事：** 作为系统运维人员，我需要简单的部署和启动流程，确保服务可以稳定运行。

#### 验收标准

1. THE System SHALL 提供 systemd 服务配置文件用于服务管理
2. THE System SHALL 提供启动脚本（start_weighted_sentiment.sh）和停止脚本（stop_weighted_sentiment.sh）
3. WHEN 系统启动时，THE System SHALL 验证所有必需的配置项（API 端点、数据库路径、独立的 Deribit 凭证）
4. THE System SHALL 验证 WEIGHTED_SENTIMENT_DERIBIT_API_KEY 和 WEIGHTED_SENTIMENT_DERIBIT_API_SECRET 环境变量存在
5. IF 配置项缺失或无效，THEN THE System SHALL 记录错误并拒绝启动
6. WHEN 系统正常启动后，THE System SHALL 在日志中记录启动成功消息（不包含凭证信息）
