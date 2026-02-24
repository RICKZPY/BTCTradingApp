# 定时交易保存功能修复

## 问题描述

定时交易功能无法保存定时策略配置。

## 根本原因

后端API路由 `/api/scheduled-trading/add-strategy` 的实现不完整：
1. 没有从数据库获取完整的策略对象
2. 没有调用 `ScheduledTradingManager.add_scheduled_strategy()` 方法来保存配置
3. 只是返回了成功消息，但实际上没有保存任何数据

## 修复内容

### 1. 更新 `scheduled_trading.py` API路由

**文件**: `BTCOptionsTrading/backend/src/api/routes/scheduled_trading.py`

**修改内容**:
- 添加数据库依赖注入 (`get_db`, `StrategyDAO`)
- 实现完整的策略获取和转换逻辑
- 调用 `ScheduledTradingManager.add_scheduled_strategy()` 保存配置

**关键代码**:
```python
@router.post("/add-strategy")
async def add_scheduled_strategy(
    request: ScheduledStrategyRequest,
    manager: ScheduledTradingManager = Depends(get_manager),
    db: Session = Depends(get_db)
):
    # 1. 从数据库获取策略
    strategy_uuid = UUID(request.strategy_id)
    strategy_model = StrategyDAO.get_by_id(db, strategy_uuid)
    
    # 2. 转换为Strategy对象（包含所有legs）
    legs = []
    for leg_model in strategy_model.legs:
        contract_model = leg_model.option_contract
        contract = OptionContract(...)
        leg = StrategyLeg(...)
        legs.append(leg)
    
    strategy = Strategy(...)
    
    # 3. 添加到定时交易管理器（这会保存到文件）
    added_strategy_id = manager.add_scheduled_strategy(
        strategy=strategy,
        schedule_time=request.schedule_time,
        timezone=request.timezone,
        use_market_order=request.use_market_order,
        auto_close=request.auto_close,
        close_time=request.close_time
    )
```

### 2. 数据流程

```
前端提交定时策略
    ↓
API接收请求 (strategy_id, schedule_time, etc.)
    ↓
从数据库读取策略 (StrategyDAO.get_by_id)
    ↓
转换为核心模型 (Strategy对象)
    ↓
调用ScheduledTradingManager.add_scheduled_strategy()
    ↓
保存到配置文件 (data/scheduled_trades.json)
    ↓
添加到调度器
```

### 3. 配置文件格式

**文件位置**: `BTCOptionsTrading/backend/data/scheduled_trades.json`

**格式**:
```json
{
  "scheduled_trades": [
    {
      "strategy_id": "uuid",
      "strategy_name": "策略名称",
      "enabled": true,
      "schedule_time": "05:00",
      "timezone": "Asia/Shanghai",
      "use_market_order": false,
      "auto_close": true,
      "close_time": "16:00"
    }
  ]
}
```

## 测试验证

### 测试脚本

1. **配置保存测试**: `test_scheduled_save.py`
   - 测试配置序列化/反序列化
   - 测试文件读写

2. **完整流程测试**: `test_scheduled_api.py`
   - 测试数据库策略保存
   - 测试策略读取和转换
   - 测试定时交易配置创建
   - 测试配置文件保存

### 运行测试

```bash
# 测试配置保存
python BTCOptionsTrading/backend/test_scheduled_save.py

# 测试完整API流程
python BTCOptionsTrading/backend/test_scheduled_api.py
```

## 使用说明

### 前端操作流程

1. 打开定时交易管理器
2. 如果未初始化，先配置Deribit API凭证
3. 点击"添加定时策略"
4. 选择已创建的策略
5. 设置执行时间、时区等参数
6. 点击"添加"按钮
7. 策略会被保存到配置文件并添加到调度器

### 后端处理流程

1. API接收请求
2. 验证策略是否存在
3. 从数据库读取完整策略信息
4. 转换为核心模型对象
5. 调用管理器保存配置
6. 配置持久化到JSON文件
7. 添加到APScheduler调度器

## 注意事项

1. **策略必须先创建**: 在添加定时交易之前，策略必须已经通过策略管理器创建并保存到数据库

2. **配置文件位置**: 配置文件默认保存在 `data/scheduled_trades.json`，确保该目录有写权限

3. **调度器启动**: 定时交易管理器初始化后会自动启动调度器，无需手动启动

4. **时区设置**: 支持多个时区，默认为"Asia/Shanghai"（北京时间）

5. **市价单 vs 限价单**: 
   - 市价单：立即以市场价格成交
   - 限价单：以指定价格或更好的价格成交

6. **自动平仓**: 如果启用，需要设置平仓时间，系统会在指定时间自动平仓

## 相关文件

- `BTCOptionsTrading/backend/src/api/routes/scheduled_trading.py` - API路由
- `BTCOptionsTrading/backend/src/trading/scheduled_trading.py` - 定时交易管理器
- `BTCOptionsTrading/frontend/src/components/strategy/ScheduledTradingManager.tsx` - 前端组件
- `BTCOptionsTrading/frontend/src/api/scheduledTrading.ts` - 前端API客户端

## 修复状态

✅ 已修复并测试通过

## 下一步

建议添加以下功能：
1. 定时策略执行历史记录
2. 策略执行失败重试机制
3. 邮件/短信通知功能
4. 策略执行前的风险检查
5. 批量导入/导出定时策略
