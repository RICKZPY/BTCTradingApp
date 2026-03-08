# 项目结构说明

## 目录结构

```
BTCOptionsTrading/
├── README.md                          # 项目主文档
├── PROJECT_STRUCTURE.md               # 本文件 - 项目结构说明
│
├── backend/                           # 后端代码
│   ├── src/                          # 源代码
│   │   ├── trading/                  # 交易模块
│   │   ├── strategy/                 # 策略模块
│   │   ├── connectors/               # 连接器模块
│   │   └── ...
│   ├── data/                         # 数据文件
│   ├── logs/                         # 日志文件
│   ├── sentiment_trading_service.py  # 情绪交易主服务
│   ├── sentiment_api.py              # API服务
│   ├── test_manual_trade.py          # 手动交易测试
│   ├── start_api_service.sh          # 启动API服务
│   ├── diagnose_api.sh               # API诊断脚本
│   ├── check_env_config.sh           # 配置检查脚本
│   └── quick_test_trade.sh           # 快速测试脚本
│
├── frontend/                          # 前端代码
│   └── ...
│
├── docs/                              # 文档目录
│   ├── guides/                       # 使用指南
│   │   ├── API_ACCESS_GUIDE.md       # API访问指南
│   │   ├── MONITORING_GUIDE.md       # 监控指南
│   │   ├── DERIBIT_CONFIG_GUIDE.md   # Deribit配置指南
│   │   ├── SENTIMENT_TRADING_QUICKSTART.md  # 快速开始
│   │   └── MANUAL_TRADING_TEST.md    # 手动交易测试指南
│   ├── deployment/                   # 部署文档
│   │   ├── DEPLOYMENT_GUIDE.md       # 部署指南
│   │   ├── SERVER_QUICKSTART.md      # 服务器快速设置
│   │   └── LOW_RESOURCE_INSTALL.md   # 低资源安装指南
│   └── troubleshooting/              # 故障排查
│       ├── SERVER_TROUBLESHOOTING.md # 服务器故障排查
│       └── BUGFIX_GUIDE.md           # Bug修复指南
│
└── scripts/                           # 脚本目录
    ├── deployment/                   # 部署脚本
    │   ├── deploy_sentiment_trading.sh
    │   └── server_install_low_memory.sh
    ├── testing/                      # 测试脚本
    │   ├── test_remote_api.sh
    │   └── test_all_endpoints.sh
    └── monitoring/                   # 监控脚本
        └── monitor_api.py
```

## 核心模块

### 后端服务 (backend/)

#### 主要服务
- `sentiment_trading_service.py` - 情绪驱动自动交易服务
  - 每天5:00 AM自动执行
  - 读取情绪API数据
  - 根据情绪选择策略并执行交易

- `sentiment_api.py` - REST API服务 (端口5002)
  - 提供持仓、订单、历史查询
  - 健康检查和状态监控

#### 测试工具
- `test_manual_trade.py` - 手动交易测试脚本
- `quick_test_trade.sh` - 快速测试包装脚本

#### 管理脚本
- `start_api_service.sh` - 启动API服务
- `diagnose_api.sh` - 全面诊断API服务
- `check_env_config.sh` - 检查环境配置

### 文档 (docs/)

#### 使用指南 (docs/guides/)
- **API_ACCESS_GUIDE.md** - 如何从本地访问服务器API
- **MONITORING_GUIDE.md** - 监控系统使用指南
- **DERIBIT_CONFIG_GUIDE.md** - Deribit API配置说明
- **SENTIMENT_TRADING_QUICKSTART.md** - 快速开始指南
- **MANUAL_TRADING_TEST.md** - 手动测试交易流程

#### 部署文档 (docs/deployment/)
- **DEPLOYMENT_GUIDE.md** - 完整部署指南
- **SERVER_QUICKSTART.md** - 服务器快速设置
- **LOW_RESOURCE_INSTALL.md** - 低资源服务器安装

#### 故障排查 (docs/troubleshooting/)
- **SERVER_TROUBLESHOOTING.md** - 服务器问题诊断
- **BUGFIX_GUIDE.md** - 常见问题修复

### 脚本 (scripts/)

#### 部署脚本 (scripts/deployment/)
- `deploy_sentiment_trading.sh` - 部署情绪交易系统
- `server_install_low_memory.sh` - 低内存服务器安装

#### 测试脚本 (scripts/testing/)
- `test_remote_api.sh` - 测试远程API连接
- `test_all_endpoints.sh` - 测试所有API端点

#### 监控脚本 (scripts/monitoring/)
- `monitor_api.py` - Python监控工具（持续监控）

## 快速导航

### 新用户开始
1. 阅读 `README.md` - 了解项目概述
2. 阅读 `docs/guides/SENTIMENT_TRADING_QUICKSTART.md` - 快速开始
3. 阅读 `docs/deployment/SERVER_QUICKSTART.md` - 部署到服务器

### 配置系统
1. `docs/guides/DERIBIT_CONFIG_GUIDE.md` - 配置Deribit API
2. `backend/.env.example` - 环境变量模板

### 测试交易
1. `docs/guides/MANUAL_TRADING_TEST.md` - 手动测试指南
2. `backend/quick_test_trade.sh` - 运行测试

### 监控系统
1. `docs/guides/MONITORING_GUIDE.md` - 监控指南
2. `docs/guides/API_ACCESS_GUIDE.md` - API访问方法
3. `scripts/monitoring/monitor_api.py` - 监控工具

### 故障排查
1. `docs/troubleshooting/SERVER_TROUBLESHOOTING.md` - 服务器问题
2. `backend/diagnose_api.sh` - 运行诊断

## 数据文件

### backend/data/
- `sentiment_trading_history.json` - 交易历史记录
- `current_positions.json` - 当前持仓和订单
- `scheduled_trades.json` - 计划交易
- `downloads/` - 下载的市场数据
- `exports/` - 导出的数据文件

### backend/logs/
- `sentiment_trading.log` - 交易服务日志
- `sentiment_api.log` - API服务日志
- `api_startup.log` - API启动日志

## 配置文件

- `backend/.env` - 环境变量配置（包含API密钥）
- `backend/.env.example` - 配置模板

## 常用命令

### 服务器上
```bash
# 启动API服务
cd /root/BTCTradingApp/BTCOptionsTrading/backend
./start_api_service.sh

# 诊断问题
./diagnose_api.sh

# 测试交易
./quick_test_trade.sh

# 查看日志
tail -f logs/sentiment_api.log
```

### 本地
```bash
# 监控API
python3 scripts/monitoring/monitor_api.py

# 测试API连接
./scripts/testing/test_remote_api.sh

# 测试所有端点
./scripts/testing/test_all_endpoints.sh
```

## 开发指南

### 添加新功能
1. 在 `backend/src/` 中添加代码
2. 在 `docs/guides/` 中添加文档
3. 在 `scripts/testing/` 中添加测试

### 添加新文档
- 使用指南 → `docs/guides/`
- 部署文档 → `docs/deployment/`
- 故障排查 → `docs/troubleshooting/`

### 添加新脚本
- 部署脚本 → `scripts/deployment/`
- 测试脚本 → `scripts/testing/`
- 监控脚本 → `scripts/monitoring/`

## 版本控制

### 重要文件（需要提交）
- 所有 `.py` 文件
- 所有 `.sh` 脚本
- 所有 `.md` 文档
- `.env.example` 配置模板

### 忽略文件（不提交）
- `.env` - 包含密钥
- `data/` - 运行时数据
- `logs/` - 日志文件
- `__pycache__/` - Python缓存
- `venv/` - 虚拟环境

---

**项目**: BTC Options Trading System  
**版本**: 1.0.0  
**最后更新**: 2026-03-08
