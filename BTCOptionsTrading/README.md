# BTC Options Trading System

基于Deribit API的比特币期权自动交易系统，支持情绪驱动策略和智能交易。

## 🎯 核心功能

- **情绪驱动交易** - 根据市场情绪自动选择和执行交易策略
- **智能策略管理** - 预定义策略模板（看涨、看跌、中性）
- **实时监控API** - 查询持仓、订单和交易历史
- **自动化执行** - 每天定时自动交易
- **测试网支持** - 安全测试，无需真实资金

## 📖 快速导航

### 新用户开始
- 📘 [项目结构说明](PROJECT_STRUCTURE.md) - 了解项目组织
- 🚀 [快速开始指南](docs/guides/SENTIMENT_TRADING_QUICKSTART.md) - 5分钟上手
- ⚙️ [Deribit配置](docs/guides/DERIBIT_CONFIG_GUIDE.md) - 配置API密钥

### 部署和运行
- 🖥️ [服务器快速设置](docs/deployment/SERVER_QUICKSTART.md) - 部署到服务器
- 📦 [低资源安装](docs/deployment/LOW_RESOURCE_INSTALL.md) - 低内存服务器
- 🔧 [完整部署指南](docs/deployment/DEPLOYMENT_GUIDE.md) - 详细部署步骤

### 测试和监控
- 🧪 [手动交易测试](docs/guides/MANUAL_TRADING_TEST.md) - 测试交易功能
- 📊 [监控指南](docs/guides/MONITORING_GUIDE.md) - 监控系统状态
- 🔌 [API访问指南](docs/guides/API_ACCESS_GUIDE.md) - 远程访问API

### 故障排查
- 🔍 [服务器故障排查](docs/troubleshooting/SERVER_TROUBLESHOOTING.md) - 诊断问题
- 🐛 [Bug修复指南](docs/troubleshooting/BUGFIX_GUIDE.md) - 常见问题

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd BTCOptionsTrading
```

### 2. 配置环境
```bash
cd backend
cp .env.example .env
nano .env  # 配置Deribit API密钥
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 测试交易
```bash
# 手动测试一次交易
python3 test_manual_trade.py
```

### 5. 启动服务
```bash
# 启动API服务（监控用）
./start_api_service.sh

# 启动自动交易服务
python3 sentiment_trading_service.py
```

## 📊 系统架构

```
情绪API → 情绪分析 → 策略选择 → 交易执行 → Deribit测试网
                                    ↓
                            持仓/订单/历史
                                    ↓
                            监控API (端口5002)
```

## 🛠 核心组件

### 后端服务
- `sentiment_trading_service.py` - 自动交易主服务
- `sentiment_api.py` - 监控API服务
- `test_manual_trade.py` - 手动测试工具

### 脚本工具
- `scripts/monitoring/monitor_api.py` - 监控工具
- `scripts/testing/test_remote_api.sh` - API测试
- `scripts/deployment/` - 部署脚本

### 文档
- `docs/guides/` - 使用指南
- `docs/deployment/` - 部署文档
- `docs/troubleshooting/` - 故障排查

## 📈 交易策略

系统根据情绪API数据自动选择策略：

| 市场情绪 | 策略类型 | 期权组合 |
|---------|---------|---------|
| 负面 > 正面 | bearish_news | 看跌期权 |
| 正面 > 负面 | bullish_news | 看涨期权 |
| 正面 = 负面 | mixed_news | 跨式组合 |

## 🔧 配置说明

### 环境变量 (.env)

```bash
# 测试网配置（用于交易）
DERIBIT_TESTNET_API_KEY=your_testnet_key
DERIBIT_TESTNET_API_SECRET=your_testnet_secret

# 主网配置（可选，用于数据收集）
DERIBIT_MAINNET_API_KEY=your_mainnet_key
DERIBIT_MAINNET_API_SECRET=your_mainnet_secret
```

## 📡 API端点

监控API运行在端口5002：

- `GET /api/health` - 健康检查
- `GET /api/status` - 完整状态
- `GET /api/positions` - 持仓信息
- `GET /api/orders` - 订单信息
- `GET /api/history` - 交易历史
- `GET /api/live/positions` - 实时持仓
- `GET /api/live/orders` - 实时订单

## 🧪 测试

### 手动测试交易
```bash
cd backend
./quick_test_trade.sh
```

### 测试API连接
```bash
# 从本地测试
./scripts/testing/test_remote_api.sh

# 测试所有端点
./scripts/testing/test_all_endpoints.sh
```

### 持续监控
```bash
python3 scripts/monitoring/monitor_api.py
```

## 📦 部署

### 服务器部署
```bash
# 1. 在服务器上克隆项目
git clone <repository-url>
cd BTCOptionsTrading/backend

# 2. 配置环境
cp .env.example .env
nano .env

# 3. 安装依赖
pip3 install -r requirements.txt

# 4. 启动服务
./start_api_service.sh
python3 sentiment_trading_service.py &
```

详细部署步骤请参考 [服务器快速设置](docs/deployment/SERVER_QUICKSTART.md)

## 🔍 监控

### 从本地监控服务器

```bash
# 方法1: Python监控脚本（推荐）
python3 scripts/monitoring/monitor_api.py

# 方法2: 浏览器访问
open http://your-server-ip:5002/api/status

# 方法3: curl命令
curl http://your-server-ip:5002/api/status | python3 -m json.tool
```

## 🐛 故障排查

### 服务器上运行诊断
```bash
cd backend
./diagnose_api.sh
```

### 检查配置
```bash
./check_env_config.sh
```

### 查看日志
```bash
tail -f logs/sentiment_api.log
tail -f logs/sentiment_trading.log
```

更多故障排查信息请参考 [服务器故障排查指南](docs/troubleshooting/SERVER_TROUBLESHOOTING.md)

## 📁 项目结构

```
BTCOptionsTrading/
├── backend/              # 后端代码
│   ├── src/             # 源代码
│   ├── data/            # 数据文件
│   ├── logs/            # 日志文件
│   └── *.py             # 主要服务
├── docs/                # 文档
│   ├── guides/          # 使用指南
│   ├── deployment/      # 部署文档
│   └── troubleshooting/ # 故障排查
└── scripts/             # 脚本工具
    ├── deployment/      # 部署脚本
    ├── testing/         # 测试脚本
    └── monitoring/      # 监控脚本
```

详细结构说明请参考 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🔐 安全提示

- ✅ 默认使用Deribit测试网，不会使用真实资金
- ✅ API密钥存储在 `.env` 文件中（不会提交到git）
- ✅ 支持主网和测试网分离配置
- ⚠️ 切换到主网前请充分测试

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Deribit API文档](https://docs.deribit.com/)
- [Deribit测试网](https://test.deribit.com/)
- [情绪API](http://43.106.51.106:5001/api/sentiment)

---

**版本**: 1.0.0  
**最后更新**: 2026-03-08  
**状态**: ✅ 生产就绪
