# 情绪交易系统部署总结

## 📦 已创建的部署文件

### 部署脚本
1. **deploy_sentiment_interactive.sh** - 交互式部署（推荐）
2. **deploy_sentiment_trading.sh** - 自动化部署脚本
3. **backend/manage_sentiment.sh** - 服务器端管理脚本

### 文档
4. **DEPLOY_NOW.md** - 快速部署指南
5. **DEPLOYMENT_SENTIMENT.md** - 完整部署文档
6. **SENTIMENT_TRADING_README.md** - 系统使用文档
7. **SENTIMENT_TRADING_QUICKSTART.md** - 快速开始指南

## 🚀 三种部署方式

### 方式1：交互式部署（最简单）

```bash
cd BTCOptionsTrading
./deploy_sentiment_interactive.sh
```

脚本会引导你输入所有必要信息并自动完成部署。

### 方式2：环境变量部署

```bash
export SERVER_HOST="your_server_ip"
export SERVER_USER="root"
export SERVER_PORT="22"
export REMOTE_DIR="/root/BTCOptionsTrading"

./deploy_sentiment_trading.sh
```

### 方式3：手动部署

参考 `DEPLOYMENT_SENTIMENT.md` 中的详细步骤。

## ✅ 部署后验证

### 1. 检查服务状态

```bash
ssh root@your_server "systemctl status sentiment_trading.service"
```

### 2. 测试API

```bash
curl http://your_server_ip:5002/api/health
curl http://your_server_ip:5002/api/status
```

### 3. 查看日志

```bash
ssh root@your_server "tail -f /root/BTCOptionsTrading/backend/logs/sentiment_trading.log"
```

## 🎮 服务器管理

SSH到服务器后：

```bash
cd /root/BTCOptionsTrading/backend
./manage_sentiment.sh
```

管理菜单提供：
- 查看服务状态
- 启动/停止/重启服务
- 查看实时日志
- 查看交易历史
- 查看当前持仓
- 运行测试
- 备份数据
- 清理日志

## 📊 监控面板

1. 编辑 `backend/sentiment_dashboard.html`
2. 修改 API_BASE 为你的服务器地址
3. 在浏览器中打开

或者在服务器上配置Nginx反向代理（参考完整文档）。

## 🔧 常用命令

### 本地操作

```bash
# 部署到服务器
./deploy_sentiment_interactive.sh

# 查看服务器状态
ssh root@your_server "systemctl status sentiment_trading.service"

# 查看日志
ssh root@your_server "journalctl -u sentiment_trading.service -f"

# 重启服务
ssh root@your_server "systemctl restart sentiment_trading.service"
```

### 服务器操作

```bash
# 使用管理脚本
./manage_sentiment.sh

# 或直接使用systemctl
systemctl status sentiment_trading.service
systemctl restart sentiment_trading.service
systemctl stop sentiment_trading.service

# 查看日志
tail -f logs/sentiment_trading.log
journalctl -u sentiment_trading.service -f
```

## 🔥 重要提醒

1. **防火墙配置** - 确保开放5002端口
2. **API密钥** - 确保.env文件配置正确
3. **时区设置** - 服务器时间影响定时执行
4. **日志监控** - 定期检查日志确保正常运行
5. **数据备份** - 定期备份交易历史数据

## 📞 获取帮助

- 快速开始：`DEPLOY_NOW.md`
- 完整部署：`DEPLOYMENT_SENTIMENT.md`
- 系统使用：`SENTIMENT_TRADING_README.md`
- 快速指南：`SENTIMENT_TRADING_QUICKSTART.md`

## 🎯 下一步

1. 运行部署脚本
2. 验证服务正常运行
3. 配置防火墙
4. 设置监控面板
5. 定期检查日志和交易记录

祝部署顺利！🎉
