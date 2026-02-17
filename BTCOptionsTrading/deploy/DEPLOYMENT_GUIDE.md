# BTC期权交易系统 - 服务器部署指南

## 目录
1. [服务器要求](#服务器要求)
2. [快速部署](#快速部署)
3. [详细步骤](#详细步骤)
4. [配置说明](#配置说明)
5. [日常维护](#日常维护)
6. [故障排查](#故障排查)

## 服务器要求

### 最低配置
- **操作系统**: Ubuntu 20.04 LTS 或更高版本
- **CPU**: 2核
- **内存**: 4GB RAM
- **存储**: 20GB SSD
- **网络**: 公网IP，开放80/443端口

### 推荐配置
- **操作系统**: Ubuntu 22.04 LTS
- **CPU**: 4核
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **网络**: 公网IP，开放80/443端口

## 快速部署

### 方法一：一键部署（推荐）

```bash
# 1. 从本地上传代码到服务器
cd BTCOptionsTrading/deploy
chmod +x upload.sh
./upload.sh user@your-server-ip

# 2. SSH登录服务器
ssh user@your-server-ip

# 3. 运行部署脚本
cd /opt/btc-options-trading/deploy
chmod +x deploy.sh
sudo ./deploy.sh prod
```

### 方法二：手动部署

参见下方[详细步骤](#详细步骤)

## 详细步骤

### 1. 准备服务器

```bash
# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 创建部署用户（可选）
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy
```

### 2. 上传代码

**选项A: 使用rsync（推荐）**
```bash
# 在本地执行
cd BTCOptionsTrading/deploy
./upload.sh user@your-server-ip
```

**选项B: 使用Git**
```bash
# 在服务器上执行
cd /opt
sudo git clone <your-repo-url> btc-options-trading
sudo chown -R $USER:$USER btc-options-trading
```

**选项C: 使用SCP**
```bash
# 在本地执行
cd BTCOptionsTrading
tar czf btc-options.tar.gz --exclude='node_modules' --exclude='venv' .
scp btc-options.tar.gz user@server:/tmp/
ssh user@server
sudo mkdir -p /opt/btc-options-trading
sudo tar xzf /tmp/btc-options.tar.gz -C /opt/btc-options-trading
```

### 3. 运行部署脚本

```bash
cd /opt/btc-options-trading/deploy
chmod +x deploy.sh
sudo ./deploy.sh prod
```

### 4. 配置环境变量

**后端配置** (`/opt/btc-options-trading/backend/.env`):
```bash
# 编辑配置文件
sudo nano /opt/btc-options-trading/backend/.env

# 重要配置项:
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Deribit API (使用你的真实密钥)
DERIBIT_API_KEY=your_api_key
DERIBIT_API_SECRET=your_api_secret
DERIBIT_TEST_MODE=false  # 生产环境设为false
```

**前端配置** (`/opt/btc-options-trading/frontend/.env`):
```bash
# 编辑配置文件
sudo nano /opt/btc-options-trading/frontend/.env

# API地址（使用服务器IP或域名）
VITE_API_BASE_URL=http://your-server-ip/api
```

### 5. 重新构建和启动

```bash
# 重新构建前端
cd /opt/btc-options-trading/frontend
npm run build

# 重启服务
sudo supervisorctl restart btc-options-trading-backend
sudo systemctl reload nginx
```

## 配置说明

### Nginx配置

配置文件位置: `/etc/nginx/sites-available/btc-options-trading`

**配置域名**:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名
    # ...
}
```

**启用HTTPS** (推荐):
```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### Supervisor配置

配置文件位置: `/etc/supervisor/conf.d/btc-options-trading-backend.conf`

**常用命令**:
```bash
# 查看状态
sudo supervisorctl status

# 启动服务
sudo supervisorctl start btc-options-trading-backend

# 停止服务
sudo supervisorctl stop btc-options-trading-backend

# 重启服务
sudo supervisorctl restart btc-options-trading-backend

# 查看日志
sudo supervisorctl tail -f btc-options-trading-backend
```

## 日常维护

### 更新系统

```bash
# 使用快速更新脚本
cd /opt/btc-options-trading/deploy
chmod +x update.sh
sudo ./update.sh
```

### 查看日志

```bash
# 后端日志
sudo tail -f /var/log/btc-options-trading-backend.log

# Nginx访问日志
sudo tail -f /var/log/nginx/btc-options-trading_access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/btc-options-trading_error.log

# 系统日志
sudo journalctl -u supervisor -f
```

### 备份数据

```bash
# 备份数据库
sudo cp /opt/btc-options-trading/backend/data/btc_options.db \
       /opt/backups/btc_options_$(date +%Y%m%d).db

# 备份配置
sudo tar czf /opt/backups/config_$(date +%Y%m%d).tar.gz \
       /opt/btc-options-trading/backend/.env \
       /opt/btc-options-trading/frontend/.env
```

### 监控服务

```bash
# 检查服务状态
sudo supervisorctl status
sudo systemctl status nginx

# 检查端口
sudo netstat -tlnp | grep -E ':(80|8000)'

# 检查进程
ps aux | grep python
ps aux | grep nginx
```

## 故障排查

### 后端无法启动

```bash
# 1. 查看日志
sudo tail -100 /var/log/btc-options-trading-backend.log

# 2. 检查Python环境
cd /opt/btc-options-trading/backend
source venv/bin/activate
python run_api.py  # 手动运行查看错误

# 3. 检查依赖
pip list
pip install -r requirements.txt

# 4. 检查配置
cat .env
```

### 前端无法访问

```bash
# 1. 检查Nginx状态
sudo systemctl status nginx
sudo nginx -t  # 测试配置

# 2. 检查前端构建
cd /opt/btc-options-trading/frontend
ls -la dist/  # 确认构建文件存在

# 3. 重新构建
npm run build

# 4. 检查权限
sudo chown -R www-data:www-data dist/
```

### API请求失败

```bash
# 1. 检查后端是否运行
curl http://localhost:8000/api/health

# 2. 检查Nginx代理
sudo tail -f /var/log/nginx/btc-options-trading_error.log

# 3. 检查防火墙
sudo ufw status
sudo ufw allow 80/tcp
```

### 数据库错误

```bash
# 1. 检查数据库文件
ls -la /opt/btc-options-trading/backend/data/

# 2. 重新初始化数据库
cd /opt/btc-options-trading/backend
source venv/bin/activate
python -c "from src.storage.database import init_db; init_db()"

# 3. 备份并重建
mv data/btc_options.db data/btc_options.db.backup
python run_api.py  # 会自动创建新数据库
```

### 性能问题

```bash
# 1. 检查系统资源
top
htop
df -h
free -m

# 2. 检查数据库大小
du -sh /opt/btc-options-trading/backend/data/

# 3. 清理日志
sudo find /var/log -name "*.log" -mtime +30 -delete
```

## 安全建议

1. **使用防火墙**
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

2. **配置SSH密钥登录**
   ```bash
   # 禁用密码登录
   sudo nano /etc/ssh/sshd_config
   # 设置: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

3. **定期更新系统**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

4. **使用HTTPS**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

5. **限制API访问**
   - 在Nginx中配置IP白名单
   - 使用JWT认证
   - 配置rate limiting

## 监控和告警

### 使用systemd监控

创建监控脚本 `/opt/scripts/monitor.sh`:
```bash
#!/bin/bash
if ! curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "Backend is down!" | mail -s "Alert: Backend Down" admin@example.com
    sudo supervisorctl restart btc-options-trading-backend
fi
```

添加到crontab:
```bash
crontab -e
# 每5分钟检查一次
*/5 * * * * /opt/scripts/monitor.sh
```

## 性能优化

1. **启用Nginx缓存**
2. **使用CDN加速静态资源**
3. **配置数据库连接池**
4. **启用Gzip压缩**
5. **使用Redis缓存**

## 联系支持

如有问题，请查看:
- 项目文档: `/opt/btc-options-trading/README.md`
- 日志文件: `/var/log/btc-options-trading-backend.log`
- GitHub Issues: (如果有的话)
