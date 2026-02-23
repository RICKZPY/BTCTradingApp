# 系统验证清单

## 后端验证 ✅

### 1. API服务器状态
- [x] API服务器正在运行 (端口8000)
- [x] 健康检查端点响应正常
- [x] 使用正确的 `run_api.py` (非简化版)

### 2. Deribit连接
- [x] 配置正确（测试网模式）
- [x] 网络连接正常
- [x] 公开API访问正常
- [x] 期权链数据获取正常

### 3. 实时价格API
- [x] BTC价格获取: $68,012 ✅
- [x] ETH价格获取: $1,976 ✅
- [x] 响应格式正确
- [x] 时间戳正确

### 4. 期权数据
- [x] 期权链获取: 1006个合约 ✅
- [x] Greeks计算正常
- [x] 隐含波动率数据正常

## 前端验证 (待用户确认)

### 1. 启动前端服务
```bash
cd BTCOptionsTrading/frontend
npm run dev
```

### 2. 浏览器访问
- [ ] 打开 http://localhost:3000 或 http://localhost:5173
- [ ] 页面正常加载

### 3. 期权链页面
- [ ] 进入"期权链"标签
- [ ] 当前价格显示正常（不是$0）
- [ ] BTC价格约 $68,000
- [ ] 期权数据正常加载
- [ ] 可以切换BTC/ETH

### 4. 浏览器控制台 (F12)
- [ ] Console标签无错误
- [ ] Network标签中API请求返回200
- [ ] `/api/data/underlying-price/BTC` 请求成功

## 生产模式验证 (可选)

### 1. 启用生产模式
```bash
cd BTCOptionsTrading/backend
python enable_production_mode.py
```

### 2. 验证配置
```bash
python -c "from src.config.settings import Settings; s = Settings(); print(f'Production: {s.is_production}, Mock: {s.should_use_mock_data}, Strict: {s.is_strict_mode}')"
```

预期输出:
```
Production: True, Mock: False, Strict: True
```

### 3. 测试严格模式
- [ ] 数据获取失败时抛出错误（不降级到模拟数据）
- [ ] 回测自动使用历史数据
- [ ] 日志显示严格模式已启用

## 诊断工具

### 运行完整诊断
```bash
cd BTCOptionsTrading/backend
python diagnose_deribit_connection.py
```

预期结果:
- [x] 配置检查: ✅ 通过
- [x] 网络连接: ✅ 通过
- [x] 公开API: ✅ 通过
- [x] 期权链: ✅ 通过
- [x] 后端API: ✅ 通过

### 测试特定端点
```bash
# BTC价格
curl http://localhost:8000/api/data/underlying-price/BTC

# ETH价格
curl http://localhost:8000/api/data/underlying-price/ETH

# 健康检查
curl http://localhost:8000/health
```

## 常见问题排查

### 问题1: 前端仍显示$0
**检查**:
1. 后端API是否运行: `curl http://localhost:8000/health`
2. 浏览器控制台是否有错误
3. Network标签中API请求状态

**解决**:
```bash
# 重启后端
cd BTCOptionsTrading/backend
python run_api.py
```

### 问题2: CORS错误
**检查**: 浏览器控制台是否显示CORS错误

**解决**: 确认 `.env` 中的CORS配置:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 问题3: API返回500错误
**检查**: 后端日志
```bash
tail -f BTCOptionsTrading/backend/logs/app.log
```

**解决**: 根据日志错误信息修复

## 性能验证

### 1. 响应时间
- [ ] 价格API响应 < 1秒
- [ ] 期权链API响应 < 3秒
- [ ] 页面加载 < 2秒

### 2. 数据准确性
- [ ] 价格在合理范围内 (BTC: $10k-$200k)
- [ ] 期权数据完整（包含Greeks）
- [ ] 时间戳正确

### 3. 稳定性
- [ ] 连续刷新10次无错误
- [ ] 切换币种无问题
- [ ] 长时间运行无内存泄漏

## 部署前检查 (生产环境)

### 1. 配置
- [ ] 使用生产环境配置
- [ ] API密钥已设置（如需要）
- [ ] 数据库连接正确
- [ ] 日志级别设置为INFO

### 2. 安全
- [ ] CORS限制到特定域名
- [ ] JWT密钥已更改
- [ ] 敏感信息不在代码中
- [ ] HTTPS已启用

### 3. 监控
- [ ] 日志系统正常
- [ ] 错误告警已配置
- [ ] 性能监控已启用
- [ ] 健康检查端点可访问

## 文档参考

- [实时数据修复总结](REALTIME_DATA_FIX_SUMMARY.md)
- [实时数据问题分析](REALTIME_DATA_ISSUE_ANALYSIS.md)
- [价格显示问题排查](TROUBLESHOOTING_PRICE_DISPLAY.md)
- [生产模式实施](PRODUCTION_MODE_IMPLEMENTATION.md)
- [生产数据模式配置](PRODUCTION_DATA_MODE.md)
- [系统总结](SYSTEM_SUMMARY.md)
- [开发进度](PROGRESS.md)

## 下一步

### 立即验证
1. 确认前端显示正常
2. 测试所有功能
3. 记录任何问题

### 可选改进
1. 修复WebSocket功能
2. 更新前端组件支持生产模式
3. 添加更多监控和告警
4. 优化性能

### 准备部署
1. 完成所有验证
2. 准备生产环境配置
3. 设置监控和备份
4. 执行部署

---

**验证日期**: 2026-02-22  
**系统版本**: 1.0.0  
**后端状态**: ✅ 正常运行  
**前端状态**: 待验证
