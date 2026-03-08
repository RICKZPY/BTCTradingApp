# 手动交易测试指南

## 概述

这个指南帮助你手动测试情绪驱动交易系统，立即执行一次完整的交易流程。

## 测试流程

测试脚本会执行以下步骤：

1. ✓ 初始化交易服务
2. ✓ 连接Deribit测试网
3. ✓ 读取情绪API数据 (http://43.106.51.106:5001/api/sentiment)
4. ✓ 分析情绪并选择策略
5. ✓ 执行交易（需要确认）
6. ✓ 显示交易结果和持仓信息

## 快速开始

### 在服务器上执行

```bash
# 1. 连接到服务器
ssh root@47.86.62.200

# 2. 进入项目目录
cd /root/BTCTradingApp/BTCOptionsTrading/backend

# 3. 拉取最新代码
git pull

# 4. 运行测试脚本
./quick_test_trade.sh
```

### 或者直接运行Python脚本

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
python3 test_manual_trade.py
```

## 策略选择逻辑

脚本会根据情绪API返回的数据自动选择策略：

| 情绪条件 | 策略类型 | 说明 |
|---------|---------|------|
| 负面 > 正面 | bearish_news | 看跌策略（买入看跌期权） |
| 正面 > 负面 | bullish_news | 看涨策略（买入看涨期权） |
| 正面 = 负面 | mixed_news | 中性策略（跨式组合） |

## 示例输出

```
==========================================================
手动测试交易
==========================================================

1. 初始化交易服务...
✓ 服务初始化成功

2. 连接Deribit测试网...
✓ Deribit认证成功

3. 获取情绪数据...
✓ 成功获取情绪数据:
  - 负面消息: 17
  - 正面消息: 11
  - 中性消息: 0
  - 总消息数: 85

4. 分析情绪并选择策略...
✓ 选择策略: 负面消息策略（看跌）

==========================================================
准备执行交易
==========================================================
策略类型: 负面消息策略（看跌）
交易网络: 测试网 (Testnet)
资金规模: $1000 USD

确认执行交易？(yes/no): yes

5. 执行交易策略...

==========================================================
交易结果
==========================================================
✓ 交易执行成功！

执行详情:
  下单数量: 2

  订单 1:
    合约: BTC-13MAR26-66000-P
    方向: buy
    数量: 2.0
    价格: 0.0234
    状态: filled

  订单 2:
    合约: BTC-13MAR26-64000-P
    方向: buy
    数量: 1.0
    价格: 0.0156
    状态: filled

6. 获取最新持仓信息...
✓ 当前持仓数量: 4
✓ 未完成订单: 0

==========================================================
测试完成！
==========================================================

查看详细信息:
  - 交易历史: cat data/sentiment_trading_history.json
  - 持仓信息: cat data/current_positions.json
  - API查看: curl http://localhost:5002/api/status
```

## 验证交易结果

### 方法1: 查看本地文件

```bash
# 查看交易历史
cat data/sentiment_trading_history.json | python3 -m json.tool

# 查看当前持仓
cat data/current_positions.json | python3 -m json.tool
```

### 方法2: 通过API查看

```bash
# 在服务器上
curl http://localhost:5002/api/status | python3 -m json.tool

# 从本地
curl http://47.86.62.200:5002/api/status | python3 -m json.tool
```

### 方法3: 直接在Deribit查看

1. 登录 https://test.deribit.com
2. 进入 Portfolio → Positions
3. 查看新增的期权持仓

## 安全提示

### ✓ 测试网交易
- 使用的是Deribit测试网
- 不会使用真实资金
- 可以安全测试所有功能

### ⚠ 注意事项
- 确保使用的是测试网API密钥
- 检查.env配置中的 `DERIBIT_TESTNET_API_KEY`
- 测试网BTC余额可以从Deribit免费获取

## 获取测试网BTC

如果测试网账户余额不足：

1. 登录 https://test.deribit.com
2. 进入 Account → Deposit
3. 点击 "Get Test BTC" 按钮
4. 系统会自动充值测试BTC

## 故障排查

### 问题1: 认证失败

**检查配置**:
```bash
./check_env_config.sh
```

确保.env中有正确的测试网密钥。

### 问题2: 无法获取情绪数据

**测试情绪API**:
```bash
curl http://43.106.51.106:5001/api/sentiment
```

如果无法访问，可能是情绪API服务未运行。

### 问题3: 策略构建失败

**查看日志**:
```bash
tail -50 logs/sentiment_trading.log
```

可能原因：
- 主网/测试网配置问题
- 网络连接问题
- Deribit API限流

### 问题4: 下单失败

可能原因：
- 测试网余额不足
- 期权合约不存在
- 价格超出限制

**解决方案**:
1. 获取测试网BTC
2. 检查日志了解具体错误
3. 确认Deribit测试网正常运行

## 高级选项

### 修改交易参数

编辑 `sentiment_trading_service.py` 中的参数：

```python
# 修改资金规模（默认$1000）
capital = 1000  # USD

# 修改期权到期时间（默认7-14天）
days_to_expiry = 7
```

### 测试特定策略

直接在Python中测试：

```python
import asyncio
from sentiment_trading_service import SentimentTradingService

async def test_specific_strategy():
    service = SentimentTradingService()
    await service.trader.authenticate()
    
    # 强制使用特定策略
    sentiment_data = {"data": {"negative_count": 20, "positive_count": 10}}
    result = await service.execute_sentiment_strategy("bearish_news", sentiment_data)
    print(result)

asyncio.run(test_specific_strategy())
```

## 监控交易

测试交易后，使用监控工具查看结果：

```bash
# 从本地监控
python3 BTCOptionsTrading/monitor_api.py --once

# 或查看完整状态
curl http://47.86.62.200:5002/api/status | python3 -m json.tool
```

## 清理测试数据

如果需要清理测试交易记录：

```bash
# 备份现有数据
cp data/sentiment_trading_history.json data/sentiment_trading_history.json.bak

# 清空历史
echo "[]" > data/sentiment_trading_history.json
```

## 下一步

测试成功后，你可以：

1. 启动自动交易服务（每天5:00 AM自动执行）
   ```bash
   ./start_sentiment_trading.sh
   ```

2. 配置systemd服务实现开机自启

3. 设置监控告警

---

**测试网地址**: https://test.deribit.com  
**情绪API**: http://43.106.51.106:5001/api/sentiment  
**监控API**: http://47.86.62.200:5002/api/status
