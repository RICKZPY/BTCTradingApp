# BTC Options Trading - Backend

## 📋 项目概述

BTC 期权交易系统后端，包含两个独立的交易系统：
1. **情绪交易系统** - 基于新闻情绪的策略交易
2. **加权情绪跨式交易系统** - 基于加权情绪评分的跨式期权交易

---

## 🗂️ 目录结构（2026-03-12 整理后）

```
backend/
├── 📁 src/                    # 源代码
│   ├── connectors/           # 交易所连接器
│   ├── strategy/             # 交易策略
│   ├── trading/              # 交易执行
│   └── ...
│
├── 📁 scripts/                # 脚本工具
│   ├── deployment/           # 部署脚本
│   ├── monitoring/           # 监控脚本
│   └── setup/                # 设置脚本
│
├── 📁 docs/                   # 文档
│   ├── deployment/           # 部署文档
│   ├── api/                  # API 文档
│   └── guides/               # 使用指南
│
├── 📁 tests/                  # 测试文件
├── 📁 config/                 # 配置文件
├── 📁 data/                   # 数据文件
├── 📁 logs/                   # 日志文件
├── 📁 examples_archive/       # 归档示例
│
└── 🐍 核心服务文件（根目录）
    ├── sentiment_api.py                    # 情绪交易 API
    ├── sentiment_trading_service.py        # 情绪交易服务
    ├── weighted_sentiment_api.py           # 加权情绪 API
    ├── weighted_sentiment_cron.py          # 加权情绪 Cron
    └── ...
```

详细结构请查看: [PROJECT_STRUCTURE_CLEAN.md](PROJECT_STRUCTURE_CLEAN.md)

---

## 🚀 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 2. 安装依赖

```bash
pip install -r config/requirements.txt
```

### 3. 启动服务

#### 情绪交易 API (端口 5002)
```bash
./scripts/setup/start_sentiment_api.sh
```

#### 加权情绪交易 API (端口 5004)
```bash
./scripts/setup/start_weighted_sentiment_api.sh
```

---

## 📡 服务端口

| 服务 | 端口 | 账户 | 说明 |
|------|------|------|------|
| sentiment_api.py | 5002 | vXkaBDto | 情绪交易状态 API |
| weighted_sentiment_api.py | 5004 | 0366QIa2 | 加权情绪状态 API |

---

## 🔧 核心服务

### 1. 情绪交易系统

**服务文件:**
- `sentiment_trading_service.py` - 主服务
- `sentiment_api.py` - 状态查询 API

**特点:**
- 账户: vXkaBDto (Deribit Test)
- 执行频率: 每天 5:00 (Cron)
- 数据源: http://43.106.51.106:5001/api/sentiment
- 策略: 多种预定义策略模板

**启动:**
```bash
./scripts/setup/start_sentiment_trading.sh
```

**API 访问:**
```bash
curl http://localhost:5002/api/status
```

---

### 2. 加权情绪跨式交易系统

**服务文件:**
- `weighted_sentiment_cron.py` - Cron 任务
- `weighted_sentiment_api.py` - 状态查询 API
- `weighted_sentiment_models.py` - 数据模型
- `weighted_sentiment_news_tracker.py` - 新闻追踪
- `weighted_sentiment_api_client.py` - API 客户端

**特点:**
- 账户: 0366QIa2 (Deribit Test)
- 执行频率: 每小时 (Cron)
- 数据源: http://43.106.51.106:5002/api/weighted-sentiment
- 策略: ATM 跨式期权（评分 >= 7 触发）

**启动 API:**
```bash
./scripts/setup/start_weighted_sentiment_api.sh
```

**API 访问:**
```bash
curl http://localhost:5004/api/status
```

---

## 📚 文档

### 部署文档
- [部署检查清单](docs/deployment/DEPLOYMENT_CHECKLIST.md)
- [部署说明](docs/deployment/DEPLOYMENT_README.md)
- [加权情绪部署 V2](docs/deployment/WEIGHTED_SENTIMENT_DEPLOYMENT_V2.md)
- [集成文档](docs/deployment/WEIGHTED_SENTIMENT_TRADING_INTEGRATION.md)

### API 文档
- [加权情绪 API 指南](docs/api/WEIGHTED_SENTIMENT_API_GUIDE.md)
- [新闻 API 客户端](docs/api/NEWS_API_CLIENT_README.md)

### 快速参考
- [快速参考 V2](docs/QUICK_REFERENCE_V2.md)
- [实现文档](docs/WEIGHTED_SENTIMENT_IMPLEMENTATION.md)

### 清理文档
- [项目结构（整理后）](PROJECT_STRUCTURE_CLEAN.md)
- [清理总结](CLEANUP_SUMMARY.md)

---

## 🛠️ 常用脚本

### 部署
```bash
# 部署情绪交易系统
./scripts/deployment/deploy_to_server.sh

# 部署加权情绪系统
./scripts/deployment/deploy_weighted_sentiment.sh

# 部署加权情绪 API
./scripts/deployment/deploy_weighted_sentiment_api.sh

# 验证部署
./scripts/deployment/verify_deployment_v2.sh
```

### 监控
```bash
# 检查环境配置
./scripts/monitoring/check_env_config.sh

# 检查加权情绪状态
./scripts/monitoring/check_weighted_sentiment_status.sh

# 诊断 API
./scripts/monitoring/diagnose_api.sh
```

### 管理
```bash
# 启动情绪 API
./scripts/setup/start_sentiment_api.sh

# 停止情绪 API
./scripts/setup/stop_sentiment_api.sh

# 快速测试
./scripts/setup/quick_test_sentiment.sh
```

---

## 🧪 测试

### 运行测试
```bash
cd tests

# 运行所有测试
pytest

# 运行特定测试
pytest test_weighted_sentiment_models.py

# 运行属性测试
pytest test_weighted_news_properties.py
```

### 测试文件
- `test_weighted_sentiment_models.py` - 数据模型测试
- `test_news_tracker.py` - 新闻追踪器测试
- `test_weighted_news_properties.py` - 属性测试
- `test_option_trade_properties.py` - 期权交易属性测试
- `test_bug_condition_exploration.py` - Bug 条件探索
- `test_preservation_properties.py` - 保留属性测试

---

## 📊 数据收集

### Orderbook 数据收集
```bash
./scripts/setup/simple_orderbook_collector.py
```

### 每日数据收集
```bash
./scripts/setup/daily_data_collector.py
```

---

## 🔐 环境变量

### 必需配置

```bash
# 情绪交易系统
DERIBIT_API_KEY="vXkaBDto"
DERIBIT_API_SECRET="..."

# 加权情绪交易系统
WEIGHTED_SENTIMENT_DERIBIT_API_KEY="0366QIa2"
WEIGHTED_SENTIMENT_DERIBIT_API_SECRET="..."
```

详细配置请查看 `.env.example`

---

## 🚨 故障排查

### API 无法访问
```bash
# 检查服务状态
systemctl status weighted-sentiment-api

# 查看日志
tail -f logs/weighted_sentiment_api.log
```

### Cron 任务未执行
```bash
# 检查 cron 配置
crontab -l | grep weighted_sentiment

# 查看 cron 日志
tail -f logs/weighted_sentiment_cron.log
```

### 依赖问题
```bash
# 修复依赖
./fix_dependencies.sh
```

---

## 📞 支持

- 查看文档: `docs/`
- 查看日志: `logs/`
- 运行诊断: `./scripts/monitoring/diagnose_api.sh`

---

## 📝 更新日志

### 2026-03-12
- ✅ 项目目录结构整理
- ✅ 文件分类到子目录
- ✅ 创建清理文档
- ✅ 更新 README

### 2026-03-12 (早期)
- ✅ 加权情绪 API V2.0 部署
- ✅ 实际 Deribit 交易集成
- ✅ 独立账户隔离

---

*最后更新: 2026-03-12*  
*项目: BTC Options Trading System*
