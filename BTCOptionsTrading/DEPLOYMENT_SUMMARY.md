# BTC期权交易系统 - 部署总结

## 🎉 部署方案已完成

我已经为你创建了一套完整的服务器部署方案，包括自动化脚本和详细文档。

## 📦 部署文件清单

```
BTCOptionsTrading/deploy/
├── deploy.sh                  # 一键部署脚本（首次部署）
├── update.sh                  # 快速更新脚本
├── upload.sh                  # 本地上传脚本
├── monitor.sh                 # 系统监控脚本
├── check-requirements.sh      # 环境检查脚本
├── DEPLOYMENT_GUIDE.md        # 详细部署指南（必读）
└── README.md                  # 快速参考
```

## 🚀 部署步骤（3步完成）

### 步骤1: 上传代码到服务器

在你的本地Mac上执行：

```bash
cd BTCOptionsTrading/deploy
./upload.sh user@your-server-ip
```

例如：
```bash
./upload.sh root@123.45.67.89
```

### 步骤2: SSH登录服务器

```bash
ssh user@your-server-ip
```

### 步骤3: 运行部署脚本

在服务器上执行：

```bash
cd /opt/btc-options-trading/deploy
sudo ./deploy.sh prod
```

部署脚本会自动完成：
- ✅ 安装所有依赖（Python, Node.js, Nginx, Supervisor等）
- ✅ 配置后端服务
- ✅ 构建前端
- ✅ 配置Nginx反向代理
- ✅ 配置进程管理（Supervisor）
- ✅ 配置防火墙
- ✅ 启动所有服务

## 🔧 部署后配置

部署完成后，需要编辑配置文件：

### 1. 后端配置

```bash
sudo nano /opt/btc-options-trading/backend/.env
```

重要配置项：
```env
# 生产环境
ENVIRONMENT=production
API_DEBUG=false

# Deribit API（使用你的真实密钥）
DERIBIT_API_KEY=your_real_api_key
DERIBIT_API_SECRET=your_real_api_secret
DERIBIT_TEST_MODE=false  # 生产环境设为false
```

### 2. 前端配置

```bash
sudo nano /opt/btc-options-trading/frontend/.env
```

配置API地址：
```env
VITE_API_BASE_URL=http://your-server-ip/api
# 或使用域名
VITE_API_BASE_URL=https://your-domain.com/api
```

### 3. 重新构建和重启

```bash
# 重新构建前端
cd /opt/btc-options-trading/frontend
npm run build

# 重启服务
sudo supervisorctl restart btc-options-trading-backend
sudo systemctl reload nginx
```

## 🌐 访问系统

部署完成后，通过浏览器访问：

- **前端界面**: `http://your-server-ip`
- **API文档**: `http://your-server-ip/api/docs`

## 📊 常用管理命令

### 服务管理

```bash
# 查看服务状态
sudo supervisorctl status

# 重启后端
sudo supervisorctl restart btc-options-trading-backend

# 停止后端
sudo supervisorctl stop btc-options-trading-backend

# 启动后端
sudo supervisorctl start btc-options-trading-backend

# 重启Nginx
sudo systemctl restart nginx
```

### 查看日志

```bash
# 后端日志
sudo tail -f /var/log/btc-options-trading-backend.log

# Nginx访问日志
sudo tail -f /var/log/nginx/btc-options-trading_access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/btc-options-trading_error.log
```

### 系统监控

```bash
# 手动运行监控
cd /opt/btc-options-trading/deploy
sudo ./monitor.sh

# 设置自动监控（每5分钟）
sudo crontab -e
# 添加这一行：
*/5 * * * * /opt/btc-options-trading/deploy/monitor.sh
```

## 🔄 更新系统

当你需要更新代码时：

```bash
# 方法1: 使用更新脚本（推荐）
cd /opt/btc-options-trading/deploy
sudo ./update.sh

# 方法2: 手动更新
cd /opt/btc-options-trading
git pull  # 如果使用git
# 或重新上传代码
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo supervisorctl restart btc-options-trading-backend
```

## 🔒 安全建议

### 1. 配置HTTPS（强烈推荐）

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取SSL证书（需要域名）
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 2. 配置防火墙

```bash
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw status
```

### 3. 禁用SSH密码登录

```bash
# 先配置SSH密钥登录
# 然后编辑SSH配置
sudo nano /etc/ssh/sshd_config
# 设置: PasswordAuthentication no
sudo systemctl restart sshd
```

## 📋 服务器要求

### 最低配置
- Ubuntu 20.04 LTS
- 2核CPU
- 4GB RAM
- 20GB SSD
- 公网IP

### 推荐配置
- Ubuntu 22.04 LTS
- 4核CPU
- 8GB RAM
- 50GB SSD
- 公网IP + 域名

## 🆘 故障排查

### 问题1: 后端无法启动

```bash
# 查看日志
sudo tail -100 /var/log/btc-options-trading-backend.log

# 手动运行查看错误
cd /opt/btc-options-trading/backend
source venv/bin/activate
python run_api.py
```

### 问题2: 前端无法访问

```bash
# 检查Nginx
sudo systemctl status nginx
sudo nginx -t

# 检查前端构建
ls -la /opt/btc-options-trading/frontend/dist/

# 重新构建
cd /opt/btc-options-trading/frontend
npm run build
```

### 问题3: API请求失败

```bash
# 检查后端是否运行
curl http://localhost:8000/api/health

# 检查Nginx代理
sudo tail -f /var/log/nginx/btc-options-trading_error.log
```

## 📚 更多文档

- **详细部署指南**: `deploy/DEPLOYMENT_GUIDE.md`
- **快速参考**: `deploy/README.md`
- **项目文档**: `README.md`

## 💡 提示

1. **首次部署前**，建议先运行环境检查：
   ```bash
   sudo ./check-requirements.sh
   ```

2. **配置域名**后，记得更新前端的API地址

3. **定期备份**数据库文件：
   ```bash
   sudo cp /opt/btc-options-trading/backend/data/btc_options.db \
          /opt/backups/btc_options_$(date +%Y%m%d).db
   ```

4. **监控日志大小**，定期清理：
   ```bash
   sudo find /var/log -name "*.log" -mtime +30 -delete
   ```

## 🎯 下一步

1. ✅ 上传代码到服务器
2. ✅ 运行部署脚本
3. ✅ 配置环境变量
4. ✅ 访问系统测试
5. ✅ 配置HTTPS（如有域名）
6. ✅ 设置监控和备份

祝部署顺利！🚀
