# 情绪交易系统部署指南

## 🚀 快速部署（推荐）

### 方法1：交互式部署

最简单的方式，脚本会引导你完成所有配置：

```bash
cd BTCOptionsTrading
./deploy_sentiment_interactive.sh
```

按提示输入：
- 服务器IP地址
- SSH用户名（默认root）
- SSH端口（默认22）
- 部署目录
- Deribit API密钥

脚本会自动完成所有部署步骤。

### 方法2：使用环境变量部署

如果你已经配置好SSH密钥：

```bash
cd BTCOptionsTrading

# 设置环境变量
export SERVER_HOST="43.106.51.106"
export SERVER_USER="root"
export SERVER_PORT="22"
export REMOTE_DIR="/root/BTCOptionsTrading"

# 执行部署
./deploy_sentiment_trading.sh
```

## 📋 部署前准备

### 1. 本地准备

确保你有：
- ✅ SSH访问服务器的权限
- ✅ Deribit API密钥（测试网）
- ✅ 本地已配置好的项目文件

### 2. 配置SSH密钥（推荐）

避免每次输入密码：

```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096

# 复制到服务器
ssh-copy-id -p 22 root@your_server_ip
```

### 3. 服务器要求

- 操作系统：Ubuntu 18.04+ / Debian 10+ / CentOS 7+
- Python 3.7+
- 至少512MB内存
- 至少1GB磁盘空间
- 开放端口：5002（API服务）

## 🔧 手动部署步骤

如果自动部署脚本遇到问题，可以手动部署：

### 1. 连接到服务器

```bash
ssh root@your_server_ip
```

### 2. 创建目录

```bash
mkdir -p /root/BTCOptionsTrading/backend/{data,logs,src}
cd /root/BTCOptionsTrading/backend
```

### 3. 上传文件

在本地执行：

```bash
# 上传主要文件
scp backend/sentiment_trading_service.py root@your_server:/root/BTCOptionsTrading/backend/
scp backend/sentiment_api.py root@your_server:/root/BTCOptionsTrading/backend/
scp backend/*.sh root@your_server:/root/BTCOptionsTrading/backend/
scp backend/*.service root@your_server:/root/BTCOptionsTrading/backend/

# 上传依赖模块
scp -r backend/src root@your_server:/root/BTCOptionsTrading/backend/
```

### 4. 配置环境

在服务器上：

```bash
cd /root/BTCOptionsTrading/backend

# 安装Python依赖
apt-get update
apt-get install -y python3 python3-pip
pip3 install aiohttp fastapi uvicorn python-dotenv

# 创建.env文件
cat > .env << 'EOF'
DERIBIT_API_KEY=your_api_key_here
DERIBIT_API_SECRET=your_api_secret_here
EOF

# 设置权限
chmod +x *.sh
```

### 5. 配置systemd服务

```bash
# 修改服务文件中的路径
sed -i 's|YOUR_USERNAME|root|g' sentiment_trading.service
sed -i 's|/path/to/BTCOptionsTrading/backend|/root/BTCOptionsTrading/backend|g' sentiment_trading.service

sed -i 's|YOUR_USERNAME|root|g' sentiment_api.service
sed -i 's|/path/to/BTCOptionsTrading/backend|/root/BTCOptionsTrading/backend|g' sentiment_api.service

# 安装服务
cp sentiment_trading.service /etc/systemd/system/
cp sentiment_api.service /etc/systemd/system/

# 启用并启动
systemctl daemon-reload
systemctl enable sentiment_trading.service sentiment_api.service
systemctl start sentiment_trading.service sentiment_api.service
```

### 6. 验证部署

```bash
# 检查服务状态
systemctl status sentiment_trading.service
systemctl status sentiment_api.service

# 查看日志
tail -f logs/sentiment_trading.log

# 测试API
curl http://localhost:5002/api/health
```

## 🔍 部署后检查

### 1. 检查服务状态

```bash
ssh root@your_server "systemctl status sentiment_trading.service"
```

应该看到 "active (running)"。

### 2. 测试API

```bash
curl http://your_server_ip:5002/api/status
```

应该返回JSON格式的状态信息。

### 3. 查看日志

```bash
ssh root@your_server "tail -f /root/BTCOptionsTrading/backend/logs/sentiment_trading.log"
```

### 4. 测试情绪API连接

```bash
ssh root@your_server "cd /root/BTCOptionsTrading/backend && python3 test_sentiment_trading.py"
```

## 🌐 配置防火墙

### Ubuntu/Debian (UFW)

```bash
ufw allow 5002/tcp
ufw reload
```

### CentOS/RHEL (firewalld)

```bash
firewall-cmd --permanent --add-port=5002/tcp
firewall-cmd --reload
```

### 云服务器安全组

如果使用阿里云、腾讯云等，需要在控制台添加安全组规则：
- 协议：TCP
- 端口：5002
- 来源：0.0.0.0/0（或指定IP）

## 📊 访问监控面板

### 方法1：修改本地dashboard

1. 编辑 `backend/sentiment_dashboard.html`
2. 修改 `API_BASE` 为你的服务器地址：
   ```javascript
   const API_BASE = 'http://your_server_ip:5002';
   ```
3. 在浏览器中打开

### 方法2：在服务器上配置Nginx

```bash
# 安装Nginx
apt-get install -y nginx

# 配置反向代理
cat > /etc/nginx/sites-available/sentiment << 'EOF'
server {
    listen 80;
    server_name your_domain_or_ip;
    
    location / {
        root /root/BTCOptionsTrading/backend;
        index sentiment_dashboard.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:5002/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/sentiment /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

然后访问 `http://your_server_ip`

## 🔧 常用管理命令

### 查看服务状态

```bash
ssh root@your_server "systemctl status sentiment_trading.service"
ssh root@your_server "systemctl status sentiment_api.service"
```

### 重启服务

```bash
ssh root@your_server "systemctl restart sentiment_trading.service"
ssh root@your_server "systemctl restart sentiment_api.service"
```

### 停止服务

```bash
ssh root@your_server "systemctl stop sentiment_trading.service sentiment_api.service"
```

### 查看日志

```bash
# 实时日志
ssh root@your_server "journalctl -u sentiment_trading.service -f"

# 最近100行
ssh root@your_server "journalctl -u sentiment_trading.service -n 100"

# 应用日志
ssh root@your_server "tail -f /root/BTCOptionsTrading/backend/logs/sentiment_trading.log"
```

### 更新代码

```bash
# 重新运行部署脚本
./deploy_sentiment_trading.sh

# 或手动上传并重启
scp backend/sentiment_trading_service.py root@your_server:/root/BTCOptionsTrading/backend/
ssh root@your_server "systemctl restart sentiment_trading.service"
```

## 🐛 故障排查

### 服务无法启动

1. 检查日志：
   ```bash
   journalctl -u sentiment_trading.service -n 50
   ```

2. 检查Python环境：
   ```bash
   ssh root@your_server "python3 --version"
   ssh root@your_server "pip3 list | grep -E 'aiohttp|fastapi'"
   ```

3. 检查.env配置：
   ```bash
   ssh root@your_server "cat /root/BTCOptionsTrading/backend/.env"
   ```

### API无法访问

1. 检查服务是否运行：
   ```bash
   ssh root@your_server "systemctl status sentiment_api.service"
   ```

2. 检查端口监听：
   ```bash
   ssh root@your_server "netstat -tlnp | grep 5002"
   ```

3. 检查防火墙：
   ```bash
   ssh root@your_server "ufw status"
   ```

### 无法连接Deribit

1. 检查API密钥：
   ```bash
   ssh root@your_server "grep DERIBIT /root/BTCOptionsTrading/backend/.env"
   ```

2. 测试网络连接：
   ```bash
   ssh root@your_server "curl -I https://test.deribit.com"
   ```

3. 运行测试脚本：
   ```bash
   ssh root@your_server "cd /root/BTCOptionsTrading/backend && python3 test_sentiment_trading.py"
   ```

### 情绪API无法访问

1. 测试连接：
   ```bash
   ssh root@your_server "curl http://43.106.51.106:5001/api/sentiment"
   ```

2. 检查时间：
   ```bash
   ssh root@your_server "date"
   ```

3. 查看服务日志中的错误信息

## 📈 监控建议

### 1. 设置日志轮转

```bash
cat > /etc/logrotate.d/sentiment-trading << 'EOF'
/root/BTCOptionsTrading/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

### 2. 设置告警

可以使用cron定期检查服务状态：

```bash
# 添加到crontab
crontab -e

# 每小时检查一次
0 * * * * systemctl is-active --quiet sentiment_trading.service || echo "情绪交易服务已停止" | mail -s "服务告警" your@email.com
```

### 3. 监控磁盘空间

```bash
# 定期清理旧日志
find /root/BTCOptionsTrading/backend/logs -name "*.log" -mtime +30 -delete
```

## 🔄 更新和维护

### 更新服务

```bash
# 1. 停止服务
ssh root@your_server "systemctl stop sentiment_trading.service sentiment_api.service"

# 2. 备份数据
ssh root@your_server "tar -czf /root/sentiment_backup_$(date +%Y%m%d).tar.gz /root/BTCOptionsTrading/backend/data"

# 3. 更新代码
./deploy_sentiment_trading.sh

# 4. 启动服务
ssh root@your_server "systemctl start sentiment_trading.service sentiment_api.service"
```

### 备份数据

```bash
# 下载交易历史
scp root@your_server:/root/BTCOptionsTrading/backend/data/sentiment_trading_history.json ./backup/

# 下载持仓快照
scp root@your_server:/root/BTCOptionsTrading/backend/data/current_positions.json ./backup/
```

## 📞 获取帮助

如果遇到问题：

1. 查看完整文档：`SENTIMENT_TRADING_README.md`
2. 检查日志文件
3. 运行测试脚本
4. 检查服务状态

## ✅ 部署检查清单

- [ ] SSH连接正常
- [ ] Python 3.7+已安装
- [ ] 依赖包已安装
- [ ] .env文件已配置
- [ ] 服务文件已安装
- [ ] 服务已启动并运行
- [ ] API可以访问
- [ ] 防火墙已配置
- [ ] 日志正常输出
- [ ] 测试脚本通过

完成以上检查后，系统应该可以正常运行了！
