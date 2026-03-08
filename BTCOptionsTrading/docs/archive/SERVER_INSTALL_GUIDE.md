# 服务器端安装指南

## 🚀 快速安装（推荐）

### 方法1：从GitHub下载（如果代码已上传）

```bash
# SSH到服务器
ssh root@your_server_ip

# 克隆仓库
git clone https://github.com/your_username/BTCOptionsTrading.git
cd BTCOptionsTrading

# 运行安装脚本
chmod +x server_install.sh
./server_install.sh
```

### 方法2：手动上传文件

#### 在本地电脑上：

```bash
# 打包必要文件
cd BTCOptionsTrading
tar -czf sentiment_trading.tar.gz \
    backend/sentiment_trading_service.py \
    backend/sentiment_api.py \
    backend/test_sentiment_trading.py \
    backend/start_sentiment_trading.sh \
    backend/stop_sentiment_trading.sh \
    backend/manage_sentiment.sh \
    backend/quick_test_sentiment.sh \
    backend/sentiment_trading.service \
    backend/sentiment_api.service \
    backend/sentiment_dashboard.html \
    backend/src/ \
    server_install.sh \
    *.md

# 上传到服务器
scp sentiment_trading.tar.gz root@your_server_ip:/root/
```

#### 在服务器上：

```bash
# SSH到服务器
ssh root@your_server_ip

# 解压文件
cd /root
tar -xzf sentiment_trading.tar.gz

# 运行安装脚本
chmod +x server_install.sh
./server_install.sh
```

### 方法3：使用部署脚本（从本地推送）

如果你的本地电脑可以SSH到服务器：

```bash
# 在本地运行
cd BTCOptionsTrading
./deploy_sentiment_interactive.sh
```

## 📋 安装后配置

### 1. 配置API密钥

```bash
cd /root/BTCOptionsTrading/backend
nano .env
```

修改为：
```
DERIBIT_API_KEY=你的真实API密钥
DERIBIT_API_SECRET=你的真实API密钥密码
```

### 2. 测试系统

```bash
python3 test_sentiment_trading.py
```

### 3. 启动服务

#### 方式A：使用脚本

```bash
./start_sentiment_trading.sh
```

#### 方式B：使用systemd

```bash
systemctl start sentiment_trading.service
systemctl start sentiment_api.service

# 查看状态
systemctl status sentiment_trading.service
```

### 4. 配置防火墙

```bash
# Ubuntu/Debian
ufw allow 5002/tcp
ufw reload

# CentOS/RHEL
firewall-cmd --permanent --add-port=5002/tcp
firewall-cmd --reload
```

### 5. 验证安装

```bash
# 检查服务状态
curl http://localhost:5002/api/health

# 查看完整状态
curl http://localhost:5002/api/status
```

## 🔧 管理服务

使用管理脚本：

```bash
cd /root/BTCOptionsTrading/backend
./manage_sentiment.sh
```

或使用systemd命令：

```bash
# 查看状态
systemctl status sentiment_trading.service

# 重启服务
systemctl restart sentiment_trading.service

# 查看日志
journalctl -u sentiment_trading.service -f
```

## 📊 访问监控面板

### 方法1：修改本地dashboard

1. 下载dashboard到本地：
   ```bash
   scp root@your_server:/root/BTCOptionsTrading/backend/sentiment_dashboard.html .
   ```

2. 编辑文件，修改API地址：
   ```javascript
   const API_BASE = 'http://your_server_ip:5002';
   ```

3. 在浏览器中打开

### 方法2：配置Nginx（可选）

```bash
# 安装Nginx
apt-get install -y nginx

# 配置
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
    }
}
EOF

# 启用
ln -s /etc/nginx/sites-available/sentiment /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## 🐛 故障排查

### 服务无法启动

```bash
# 查看详细日志
journalctl -u sentiment_trading.service -n 50

# 检查Python环境
python3 --version
pip3 list | grep -E "aiohttp|fastapi"

# 检查.env配置
cat /root/BTCOptionsTrading/backend/.env
```

### API无法访问

```bash
# 检查服务状态
systemctl status sentiment_api.service

# 检查端口
netstat -tlnp | grep 5002

# 检查防火墙
ufw status
```

### 测试连接

```bash
# 测试情绪API
curl http://43.106.51.106:5001/api/sentiment

# 测试Deribit连接
curl -I https://test.deribit.com
```

## 📞 获取帮助

查看完整文档：
- `SENTIMENT_TRADING_README.md` - 系统使用文档
- `SENTIMENT_TRADING_QUICKSTART.md` - 快速开始
- `DEPLOYMENT_SENTIMENT.md` - 详细部署指南

## ✅ 安装检查清单

- [ ] Python 3.7+ 已安装
- [ ] 依赖包已安装
- [ ] .env文件已配置真实API密钥
- [ ] 服务已启动
- [ ] 防火墙已配置（开放5002端口）
- [ ] API可以访问
- [ ] 测试脚本通过

完成以上检查后，系统应该可以正常运行！
