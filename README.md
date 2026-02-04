# BTC交易系统项目集合

本项目包含两个独立的比特币交易系统：

## 📈 现货交易系统 (SpotTradingSystem/)

基于Binance API的比特币现货交易系统，支持技术分析、策略回测和自动化交易。

**主要功能：**
- 实时市场数据获取和分析
- 技术指标计算（MACD、RSI、布林带等）
- 自定义策略编辑器
- 历史回测引擎
- 风险管理和监控
- Web界面和API接口

**技术栈：** Python + FastAPI + React + TypeScript

[查看详细文档](SpotTradingSystem/README.md)

## 📊 期权交易系统 (BTCOptionsTrading/)

基于Deribit API的比特币期权交易回测系统，专注于期权策略分析和风险管理。

**主要功能：**
- Deribit期权链数据集成
- Black-Scholes期权定价模型
- 希腊字母计算和风险分析
- 多种期权策略支持（跨式、宽跨式、铁鹰等）
- 波动率分析和预测
- 期权组合回测和绩效分析

**技术栈：** Python + QuantLib + FastAPI + React + TypeScript

[查看设计文档](.kiro/specs/btc-options-trading-system/)

## 🚀 快速开始

### 现货交易系统
```bash
cd SpotTradingSystem
# 查看安装和运行说明
cat README.md
```

### 期权交易系统
```bash
cd BTCOptionsTrading
# 系统正在开发中，请查看规格文档
```

## 📁 项目结构

```
.
├── SpotTradingSystem/          # 现货交易系统（已完成）
│   ├── backend/               # Python后端服务
│   ├── frontend/              # React前端应用
│   ├── web-demo/              # 演示页面
│   └── README.md              # 详细文档
├── BTCOptionsTrading/          # 期权交易系统（开发中）
└── .kiro/specs/               # 系统规格文档
    ├── bitcoin-trading-system/     # 现货系统规格
    └── btc-options-trading-system/ # 期权系统规格
```

## 📋 开发状态

- ✅ **现货交易系统**: 已完成，包含完整的前后端实现
- 🚧 **期权交易系统**: 需求和设计已完成，正在实施中

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这些系统。

## 📄 许可证

请查看各个子项目的许可证文件。