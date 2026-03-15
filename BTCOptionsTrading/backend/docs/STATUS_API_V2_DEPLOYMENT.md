# 状态 API V2 部署说明

## 部署日期
2026-03-13

## 更新内容

### 问题修复
1. ✅ 修复中文乱码问题 - 使用 UTF-8 编码
2. ✅ 精简持仓信息 - 只显示关键数据
3. ✅ 关联新闻和仓位 - 显示触发交易的新闻内容

### 新功能
- 移动端友好的界面设计
- Emoji 图标增强可读性
- 简化的合约名称显示（例如：BTC-28MAR26-95000-C → 28MAR 95K C）

## API 端点

### 服务器地址
http://47.86.62.200:5004

### 可用端点

#### 1. 系统状态
```
GET http://47.86.62.200:5004/api/status
```

返回示例：
```json
{
  "服务": "加权情绪跨式交易",
  "状态": "运行中 ✓",
  "最后执行": "2026-03-13T08:00:02",
  "执行结果": "识别到 0 条新的高分新闻",
  "历史新闻总数": 93,
  "当前持仓数": 10,
  "查询时间": "2026-03-13 08:37:11"
}
```

#### 2. 持仓信息（精简版）
```
GET http://47.86.62.200:5004/api/positions
```

返回示例：
```json
{
  "持仓数量": 10,
  "持仓列表": [
    {
      "📅 时间": "2026-03-12T19:00",
      "📰 新闻": "国际能源署大幅下调石油供应增长预期...",
      "😊 情绪": "negative",
      "⭐ 评分": "10/10",
      "💰 现货": "$70413.42",
      "📈 看涨": "27MAR 70K C",
      "📉 看跌": "27MAR 70K P",
      "💵 成本": "$569.64"
    }
  ],
  "查询时间": "2026-03-13 08:37:11"
}
```

#### 3. 首页
```
GET http://47.86.62.200:5004/
```

显示可用端点的 HTML 页面，移动端友好。

## 部署步骤

### 1. 停止旧的 API
```bash
ssh root@47.86.62.200 "kill <旧进程PID>"
```

### 2. 上传新文件
```bash
scp weighted_sentiment_status_api_v2.py root@47.86.62.200:~/BTCOptionsTrading/backend/
scp start_status_api.sh root@47.86.62.200:~/BTCOptionsTrading/backend/
```

### 3. 启动新 API
```bash
ssh root@47.86.62.200 "cd ~/BTCOptionsTrading/backend && ./start_status_api.sh"
```

## 管理命令

### 启动服务
```bash
cd ~/BTCOptionsTrading/backend
./start_status_api.sh
```

### 停止服务
```bash
cd ~/BTCOptionsTrading/backend
./stop_status_api.sh
```

### 查看日志
```bash
tail -f ~/BTCOptionsTrading/backend/logs/status_api.log
```

### 检查进程
```bash
ps aux | grep weighted_sentiment_status_api_v2.py
```

### 检查端口
```bash
netstat -tlnp | grep 5004
```

## 移动端使用

### 苹果手机
1. 打开 Safari 浏览器
2. 访问：http://47.86.62.200:5004/api/positions
3. 中文显示正常，无乱码
4. 可以看到每个仓位对应的新闻内容

### 快捷方式
可以将以下链接添加到手机主屏幕：
- 持仓查询：http://47.86.62.200:5004/api/positions
- 系统状态：http://47.86.62.200:5004/api/status

## 数据说明

### 持仓信息字段
- 📅 时间：交易执行时间
- 📰 新闻：触发交易的新闻内容（前100字符）
- 😊 情绪：新闻情绪（positive/negative/neutral）
- ⭐ 评分：新闻重要性评分（1-10分）
- 💰 现货：交易时的 BTC 现货价格
- 📈 看涨：看涨期权合约（简化显示）
- 📉 看跌：看跌期权合约（简化显示）
- 💵 成本：跨式交易总成本（USD）

### 合约名称简化规则
- 原始：BTC-28MAR26-95000-C
- 简化：28MAR 95K C
- 格式：日期 执行价 类型

## 技术细节

### 文件位置
- API 程序：`~/BTCOptionsTrading/backend/weighted_sentiment_status_api_v2.py`
- 启动脚本：`~/BTCOptionsTrading/backend/start_status_api.sh`
- 停止脚本：`~/BTCOptionsTrading/backend/stop_status_api.sh`
- 日志文件：`~/BTCOptionsTrading/backend/logs/status_api.log`
- 交易日志：`~/BTCOptionsTrading/backend/logs/weighted_sentiment_trades.log`

### 端口使用
- 5002：加权情绪新闻 API
- 5004：状态查询 API（本服务）

### 编码设置
- 响应编码：UTF-8
- 日志编码：UTF-8
- 文件读取：UTF-8

## 故障排查

### 中文乱码
- 确认浏览器编码设置为 UTF-8
- 检查 API 响应头：`Content-Type: application/json; charset=utf-8`

### 无法访问
1. 检查服务是否运行：`ps aux | grep weighted_sentiment_status_api_v2.py`
2. 检查端口是否监听：`netstat -tlnp | grep 5004`
3. 检查防火墙：`ufw status`
4. 查看日志：`tail -f logs/status_api.log`

### 数据不更新
- 交易数据来自：`logs/weighted_sentiment_trades.log`
- 确认 cron job 正在执行：`tail -f logs/weighted_sentiment_cron.log`
- 检查新闻历史数据库：`ls -lh data/weighted_news_history.db`

## 后续优化建议

1. 添加持仓盈亏计算
2. 添加实时价格更新
3. 添加推送通知功能
4. 添加历史交易统计图表

## 部署状态

🟢 **已部署** - 服务运行在 http://47.86.62.200:5004
