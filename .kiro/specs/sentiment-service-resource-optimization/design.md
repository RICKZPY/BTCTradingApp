# Sentiment Service Resource Optimization Bugfix Design

## Overview

当前的情绪交易服务采用持续运行模式，通过while True循环每分钟检查时间，在每天早上5点执行交易。这种实现在2核vCPU服务器上造成不必要的资源浪费，因为服务需要24小时保持Python进程和WebSocket连接，但实际上每天只执行一次交易操作。

本次修复将把持续运行的服务模式改为按需执行的cron job模式。核心策略是：移除while True循环和时间检查逻辑，将daily_check()方法改为脚本的主入口点，由操作系统的cron调度器在每天早上5点触发执行。这样可以将资源占用从24小时降低到每天几分钟，同时保持所有交易逻辑、情绪分析和错误处理完全不变。

## Glossary

- **Bug_Condition (C)**: 服务采用持续运行模式（while True循环 + 时间检查）导致24小时占用资源
- **Property (P)**: 服务应该按需执行（cron触发 + 单次执行 + 自动退出）以最小化资源占用
- **Preservation**: 所有交易逻辑、情绪分析、错误处理、日志记录、配置兼容性必须保持不变
- **sentiment_trading_service.py**: 位于`BTCOptionsTrading/backend/`的情绪驱动交易服务脚本
- **daily_check()**: SentimentTradingService类中的方法，执行每日交易检查和策略执行
- **run()**: SentimentTradingService类中的方法，包含while True循环和时间检查逻辑（需要移除）
- **cron job**: Linux/Unix系统的定时任务调度机制，可以在指定时间自动执行脚本

## Bug Details

### Bug Condition

当sentiment_trading_service.py以持续运行模式部署时，会造成资源浪费。具体表现为：服务通过while True循环每60秒检查一次当前时间，只有在早上5点时才执行交易，其余23小时59分钟都在空转。同时，服务需要持续维护到Deribit的WebSocket连接（测试网和可选的主网连接），即使不在交易时间也保持连接状态。

**Formal Specification:**
```
FUNCTION isBugCondition(deployment)
  INPUT: deployment of type ServiceDeployment
  OUTPUT: boolean
  
  RETURN deployment.hasWhileTrueLoop == true
         AND deployment.hasTimeCheckingLogic == true
         AND deployment.maintainsPersistentConnection == true
         AND deployment.executionFrequency == "once per day"
         AND deployment.serverResources == "limited (2-core vCPU)"
END FUNCTION
```

### Examples

- **Example 1**: 在早上6点到次日早上4点59分之间，服务每分钟执行一次时间检查，但不执行任何交易操作，Python进程和WebSocket连接持续占用CPU和内存资源
  - Expected: 在这段时间内，不应该有任何Python进程运行
  - Actual: Python进程持续运行，每分钟执行sleep(60)和时间检查

- **Example 2**: 在2核vCPU服务器上，sentiment_trading_service.py持续占用一个Python进程，即使在不交易的时间段
  - Expected: 仅在早上5点左右短暂占用资源（约2-5分钟）
  - Actual: 24小时持续占用资源

- **Example 3**: 当服务器需要重启或维护时，需要手动停止和启动sentiment_trading_service.py进程
  - Expected: cron job自动管理，无需手动干预
  - Actual: 需要手动管理进程生命周期

- **Edge Case**: 如果服务在早上5点00分到5点01分之间崩溃，当天的交易会被跳过（因为last_check_date机制）
  - Expected: cron job会在指定时间重新触发，不依赖进程状态

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 情绪数据获取逻辑（fetch_sentiment_data方法）必须保持不变
- 情绪分析逻辑（analyze_sentiment方法）必须保持不变
- 策略执行逻辑（execute_sentiment_strategy方法）必须保持不变
- 交易历史记录格式和保存机制必须保持不变
- 持仓和订单查询逻辑（get_positions_and_orders方法）必须保持不变
- 错误处理和日志记录格式必须保持不变
- .env配置文件的兼容性必须保持不变（支持主网/测试网混合配置）
- 数据文件路径和格式必须保持不变（sentiment_trading_history.json, current_positions.json）

**Scope:**
所有不涉及服务运行模式（while True循环、时间检查、持久连接管理）的代码都应该完全不受影响。这包括：
- 所有交易相关的业务逻辑
- 所有API调用和数据处理
- 所有文件I/O操作
- 所有配置加载和环境变量处理
- 所有日志记录语句

## Hypothesized Root Cause

基于bug描述和代码分析，资源浪费的根本原因是：

1. **不必要的持续运行模式**: run()方法中的while True循环导致进程永不退出，即使在不需要执行任何操作的时间段也持续运行

2. **低效的时间检查机制**: 每60秒检查一次时间（current_time.hour == CHECK_TIME.hour），这种轮询方式在24小时内执行1440次检查，但只有1次真正执行交易

3. **持久连接的过度维护**: 在run()方法开始时建立WebSocket连接（await self.trader.authenticate()），连接在整个服务生命周期内保持，即使在不交易的23小时内也不释放

4. **缺乏任务调度机制**: 代码没有利用操作系统级别的任务调度（cron），而是在应用层实现调度逻辑，导致资源利用效率低下

## Correctness Properties

Property 1: Bug Condition - Cron-Based Execution Model

_For any_ deployment where the service needs to execute once daily at a specific time, the fixed implementation SHALL use cron job scheduling instead of continuous process execution, establishing connections only when needed, executing the trading logic, and then exiting cleanly to release all resources.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Trading Logic and Configuration Compatibility

_For any_ trading execution triggered by the fixed cron-based service, the system SHALL produce exactly the same trading behavior, sentiment analysis results, error handling, logging output, and data file formats as the original continuous service, preserving all business logic and configuration compatibility.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

## Fix Implementation

### Changes Required

假设我们的根本原因分析是正确的，需要进行以下修改：

**File**: `BTCOptionsTrading/backend/sentiment_trading_service.py`

**Function**: `SentimentTradingService.run()` 和 `main()`

**Specific Changes**:

1. **移除持续运行循环**: 删除run()方法中的while True循环和时间检查逻辑
   - 移除`while True:`循环体
   - 移除`if current_time.hour == CHECK_TIME.hour`时间检查
   - 移除`await asyncio.sleep(60)`轮询延迟
   - 保留连接认证逻辑，但移到新的执行入口点

2. **重构为单次执行模式**: 将daily_check()改为脚本的主要执行逻辑
   - 移除`last_check_date`重复执行检查（cron保证不会重复）
   - 创建新的execute_once()方法作为主入口点
   - 在execute_once()中：建立连接 -> 执行daily_check() -> 关闭连接

3. **添加连接生命周期管理**: 确保连接在执行完成后正确关闭
   - 在execute_once()开始时调用authenticate()
   - 在execute_once()结束时调用close()或cleanup()方法
   - 使用try-finally确保连接总是被关闭

4. **修改main()函数**: 改为调用单次执行逻辑而不是持续运行
   - 将`await service.run()`改为`await service.execute_once()`
   - 添加执行完成的日志记录

5. **保持所有业务逻辑不变**: 
   - daily_check()方法保持完全不变
   - 所有helper方法（fetch_sentiment_data, analyze_sentiment等）保持不变
   - 所有配置加载和初始化逻辑保持不变

**Additional File**: 创建cron配置文档或脚本

**File**: `BTCOptionsTrading/backend/setup_cron.sh` (新文件)

**Purpose**: 提供cron job配置脚本，自动化部署过程

**Content**:
- 检测Python解释器路径
- 检测脚本绝对路径
- 生成cron表达式（0 5 * * *）
- 配置日志重定向
- 提供安装和卸载命令

## Testing Strategy

### Validation Approach

测试策略采用两阶段方法：首先在未修复的代码上运行探索性测试，观察持续运行模式的资源占用特征；然后验证修复后的代码能够正确执行单次任务并释放资源，同时保持所有交易逻辑不变。

### Exploratory Bug Condition Checking

**Goal**: 在实施修复之前，通过测试证明当前实现确实存在资源浪费问题。确认或反驳根本原因分析。如果反驳，需要重新假设。

**Test Plan**: 编写测试脚本监控sentiment_trading_service.py的进程状态、内存占用和连接状态。在非交易时间（如早上6点）运行服务，观察资源占用情况。在未修复的代码上运行这些测试，预期会观察到持续的资源占用。

**Test Cases**:
1. **Continuous Process Test**: 启动服务后，在非交易时间检查进程是否持续运行（will fail on unfixed code - 进程应该不存在但实际存在）
2. **Resource Monitoring Test**: 监控服务在1小时内的CPU和内存使用情况（will fail on unfixed code - 应该为0但实际持续占用）
3. **Connection Persistence Test**: 检查WebSocket连接是否在非交易时间保持打开（will fail on unfixed code - 连接应该关闭但实际保持打开）
4. **Time Check Frequency Test**: 统计时间检查逻辑的执行次数（will fail on unfixed code - 应该为0但实际每分钟执行一次）

**Expected Counterexamples**:
- 进程在非交易时间持续运行，ps命令可以看到sentiment_trading_service.py进程
- 内存占用持续存在（约50-100MB），CPU使用率虽低但非零
- 可能的原因：while True循环、每分钟的sleep和时间检查、持久WebSocket连接

### Fix Checking

**Goal**: 验证对于所有需要按需执行的部署场景，修复后的函数能够产生预期的行为（单次执行、资源释放）。

**Pseudocode:**
```
FOR ALL deployment WHERE isBugCondition(deployment) DO
  result := execute_fixed_service()
  ASSERT result.processExitsAfterExecution == true
  ASSERT result.connectionsClosedAfterExecution == true
  ASSERT result.resourcesReleasedAfterExecution == true
  ASSERT result.canBeScheduledByCron == true
END FOR
```

**Test Plan**: 
1. 手动运行修复后的脚本，验证它能够执行完成后退出
2. 配置cron job在测试时间运行，验证cron能够正确触发
3. 监控执行前后的进程状态，确认进程在执行完成后不存在
4. 检查日志文件，确认执行逻辑正确完成

### Preservation Checking

**Goal**: 验证对于所有交易执行场景，修复后的函数产生与原始函数完全相同的结果（交易逻辑、数据格式、错误处理）。

**Pseudocode:**
```
FOR ALL trading_scenario WHERE NOT isBugCondition(trading_scenario) DO
  ASSERT execute_original(trading_scenario) = execute_fixed(trading_scenario)
END FOR
```

**Testing Approach**: 属性测试（Property-based testing）强烈推荐用于保留性检查，因为：
- 它可以自动生成多种测试场景（不同的情绪数据、市场条件、配置）
- 它能捕获手动单元测试可能遗漏的边缘情况
- 它提供强有力的保证，确保所有非bug相关的输入行为保持不变

**Test Plan**: 首先在未修复的代码上观察各种交易场景的行为（情绪分析、策略选择、订单执行、日志记录），然后编写属性测试捕获这些行为，在修复后的代码上运行验证。

**Test Cases**:
1. **Sentiment Analysis Preservation**: 观察未修复代码对不同情绪数据的分析结果，验证修复后产生相同的策略选择（bearish_news/bullish_news/mixed_news）
2. **Trading Execution Preservation**: 观察未修复代码的交易执行流程，验证修复后产生相同的订单、相同的历史记录格式
3. **Error Handling Preservation**: 观察未修复代码在API失败、网络错误等情况下的行为，验证修复后产生相同的错误日志和恢复机制
4. **Configuration Compatibility Preservation**: 观察未修复代码对主网/测试网混合配置的处理，验证修复后保持相同的配置加载逻辑

### Unit Tests

- 测试execute_once()方法能够正确建立连接、执行交易、关闭连接
- 测试连接失败时的错误处理（认证失败、网络超时）
- 测试脚本在各种情绪数据输入下的执行结果
- 测试日志文件和数据文件的正确生成
- 测试边缘情况：API返回空数据、没有合适的期权、订单执行失败

### Property-Based Tests

- 生成随机的情绪数据（不同的positive_count和negative_count组合），验证策略选择逻辑在修复前后保持一致
- 生成随机的市场条件（不同的BTC价格、期权合约可用性），验证交易执行逻辑在修复前后保持一致
- 生成随机的配置组合（仅测试网、主网+测试网），验证配置加载和连接管理在修复前后保持一致
- 测试多次执行的幂等性：连续运行脚本多次，验证每次都能正确执行和退出

### Integration Tests

- 完整的端到端测试：配置cron job -> 等待触发时间 -> 验证执行结果 -> 检查进程已退出
- 测试cron环境下的日志记录：验证stdout/stderr正确重定向到日志文件
- 测试服务器重启后cron job的持久性：重启服务器 -> 验证cron job仍然存在并能正常触发
- 测试与其他服务的资源竞争：在资源受限的环境下运行，验证不会因为资源不足而失败
