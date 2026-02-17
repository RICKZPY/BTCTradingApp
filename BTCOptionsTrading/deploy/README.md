# 部署脚本说明

这个目录包含了将BTC期权交易系统部署到云端服务器的所有脚本和文档。

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `deploy.sh` | 一键部署脚本（首次部署使用） |
| `update.sh` | 快速更新脚本（更新已部署的系统） |
| `upload.sh` | 从本地上传代码到服务器 |
| `monitor.sh` | 系统监控脚本 |
| `DEPLOYMENT_GUIDE.md` | 详细部署指南 |

## 🚀 快速开始

### 1. 首次部署

```bash
# 在本地执行 - 上传代码
cd BTCOptionsTrading/deploy
./upload.sh user@your-server-ip

# SSH登录服务器
ssh user@your-server-ip

# 在服务器上执行 - 部署系统
cd /opt/btc-options-trading/deploy
sudo ./deploy.sh prod
```

### 2. 更新系统

```bash
# SSH登录服务器
ssh user@your-server-ip

# 运行更新脚本
cd /opt/btc-options-trading/deploy
sudo ./update.sh
```

### 3. 监控系统

```bash
# 手动运行监控
sudo ./monitor.sh

# 或设置定时任务
sudo crontab -e
# 添加: */5 * * * * /opt/btc-options-trading/deploy/monitor.sh
```

## 📋 常用命令

### 服务管理

```bash
# 查看服务状态
sudo supervisorctl status

# 重启后端
sudo supervisorctl restart btc-options-trading-backend

# 重启Nginx
sudo systemctl restart nginx

# 查看日志
sudo tail -f /var/log/btc-options-trading-backend.log
```

### 系统检查

```bash
# 检查端口
sudo netstat -tlnp | grep -E ':(80|8000)'

# 检查进程
ps aux | grep python
ps aux | grep nginx

# 检查磁盘
df -h

# 检查内存
free -m
```

## 🔧 配置文件位置

- 后端配置: `/opt/btc-options-trading/backend/.env`
- 前端配置: `/opt/btc-options-trading/frontend/.env`
- Nginx配置: `/etc/nginx/sites-available/btc-options-trading`
- Supervisor配置: `/etc/supervisor/conf.d/btc-options-trading-backend.conf`

## 📝 日志位置

- 后端日志: `/var/log/btc-options-trading-backend.log`
- Nginx访问日志: `/var/log/nginx/btc-options-trading_access.log`
- Nginx错误日志: `/var/log/nginx/btc-options-trading_error.log`

## 🆘 故障排查

如果遇到问题，请查看 `DEPLOYMENT_GUIDE.md` 中的故障排查章节。

常见问题：
1. 后端无法启动 → 检查日志和Python环境
2. 前端无法访问 → 检查Nginx配置和构建文件
3. API请求失败 → 检查后端运行状态和Nginx代理
4. 数据库错误 → 检查数据库文件和权限

## 📞 获取帮助

详细文档请参考：
- [完整部署指南](./DEPLOYMENT_GUIDE.md)
- [项目README](../README.md)
