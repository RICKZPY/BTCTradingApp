# 文档索引

快速找到你需要的文档。

## 📚 主要文档

| 文档 | 说明 | 位置 |
|------|------|------|
| **README.md** | 项目概述和快速开始 | 根目录 |
| **PROJECT_STRUCTURE.md** | 项目结构说明 | 根目录 |
| **DOCUMENTATION_INDEX.md** | 本文件 - 文档索引 | 根目录 |

## 🚀 使用指南

### 新手入门
| 文档 | 说明 |
|------|------|
| [快速开始](docs/guides/SENTIMENT_TRADING_QUICKSTART.md) | 5分钟快速上手 |
| [Deribit配置](docs/guides/DERIBIT_CONFIG_GUIDE.md) | 配置API密钥 |
| [手动交易测试](docs/guides/MANUAL_TRADING_TEST.md) | 测试交易功能 |

### 监控和管理
| 文档 | 说明 |
|------|------|
| [监控指南](docs/guides/MONITORING_GUIDE.md) | 监控系统状态 |
| [API访问指南](docs/guides/API_ACCESS_GUIDE.md) | 远程访问API |

## 🖥️ 部署文档

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [服务器快速设置](docs/deployment/SERVER_QUICKSTART.md) | 快速部署指南 | 标准服务器 |
| [完整部署指南](docs/deployment/DEPLOYMENT_GUIDE.md) | 详细部署步骤 | 生产环境 |
| [低资源安装](docs/deployment/LOW_RESOURCE_INSTALL.md) | 低内存服务器安装 | <512MB RAM |

## 🔧 故障排查

| 文档 | 说明 |
|------|------|
| [服务器故障排查](docs/troubleshooting/SERVER_TROUBLESHOOTING.md) | 诊断服务器问题 |
| [Bug修复指南](docs/troubleshooting/BUGFIX_GUIDE.md) | 常见问题修复 |

## 🛠️ 脚本工具

### 部署脚本
| 脚本 | 说明 | 位置 |
|------|------|------|
| `deploy_sentiment_trading.sh` | 部署情绪交易系统 | scripts/deployment/ |
| `server_install_low_memory.sh` | 低内存服务器安装 | scripts/deployment/ |

### 测试脚本
| 脚本 | 说明 | 位置 |
|------|------|------|
| `test_remote_api.sh` | 测试远程API | scripts/testing/ |
| `test_all_endpoints.sh` | 测试所有端点 | scripts/testing/ |
| `test_manual_trade.py` | 手动交易测试 | backend/ |
| `quick_test_trade.sh` | 快速测试包装 | backend/ |

### 监控脚本
| 脚本 | 说明 | 位置 |
|------|------|------|
| `monitor_api.py` | Python监控工具 | scripts/monitoring/ |

### 管理脚本
| 脚本 | 说明 | 位置 |
|------|------|------|
| `start_api_service.sh` | 启动API服务 | backend/ |
| `diagnose_api.sh` | API诊断 | backend/ |
| `check_env_config.sh` | 配置检查 | backend/ |

## 📖 按任务查找

### 我想开始使用系统
1. 阅读 [README.md](README.md)
2. 阅读 [快速开始](docs/guides/SENTIMENT_TRADING_QUICKSTART.md)
3. 配置 [Deribit API](docs/guides/DERIBIT_CONFIG_GUIDE.md)

### 我想部署到服务器
1. 阅读 [服务器快速设置](docs/deployment/SERVER_QUICKSTART.md)
2. 如果服务器资源有限，参考 [低资源安装](docs/deployment/LOW_RESOURCE_INSTALL.md)
3. 部署后参考 [监控指南](docs/guides/MONITORING_GUIDE.md)

### 我想测试交易功能
1. 阅读 [手动交易测试](docs/guides/MANUAL_TRADING_TEST.md)
2. 运行 `backend/quick_test_trade.sh`
3. 查看结果

### 我想监控系统
1. 阅读 [监控指南](docs/guides/MONITORING_GUIDE.md)
2. 阅读 [API访问指南](docs/guides/API_ACCESS_GUIDE.md)
3. 使用 `scripts/monitoring/monitor_api.py`

### 我遇到了问题
1. 运行 `backend/diagnose_api.sh`
2. 阅读 [服务器故障排查](docs/troubleshooting/SERVER_TROUBLESHOOTING.md)
3. 查看 [Bug修复指南](docs/troubleshooting/BUGFIX_GUIDE.md)

### 我想了解项目结构
1. 阅读 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. 查看各目录的README文件

## 🔍 按主题查找

### API相关
- [API访问指南](docs/guides/API_ACCESS_GUIDE.md)
- [Deribit配置](docs/guides/DERIBIT_CONFIG_GUIDE.md)

### 交易相关
- [快速开始](docs/guides/SENTIMENT_TRADING_QUICKSTART.md)
- [手动交易测试](docs/guides/MANUAL_TRADING_TEST.md)

### 部署相关
- [服务器快速设置](docs/deployment/SERVER_QUICKSTART.md)
- [完整部署指南](docs/deployment/DEPLOYMENT_GUIDE.md)
- [低资源安装](docs/deployment/LOW_RESOURCE_INSTALL.md)

### 监控相关
- [监控指南](docs/guides/MONITORING_GUIDE.md)
- [API访问指南](docs/guides/API_ACCESS_GUIDE.md)

### 故障排查
- [服务器故障排查](docs/troubleshooting/SERVER_TROUBLESHOOTING.md)
- [Bug修复指南](docs/troubleshooting/BUGFIX_GUIDE.md)

## 📝 文档贡献

如果你发现文档有误或需要补充，欢迎：
1. 提交Issue
2. 提交Pull Request
3. 联系维护者

## 🔄 文档更新

- **最后更新**: 2026-03-08
- **版本**: 1.0.0
- **维护者**: 项目团队

---

**提示**: 使用 Ctrl+F (或 Cmd+F) 在本页面搜索关键词快速定位文档。
