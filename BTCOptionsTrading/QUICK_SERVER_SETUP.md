# 🚀 服务器快速安装

## 一键安装命令

SSH到你的服务器，然后运行：

```bash
# 克隆仓库
git clone https://github.com/RICKZPY/BTCTradingApp.git
cd BTCTradingApp/BTCOptionsTrading

# 运行安装脚本
chmod +x server_install.sh
./server_install.sh
```

## 安装后配置

### 1. 配置API密钥

```bash
cd backend
nano .env
```

修改为你的真实API密钥：
```
DERIBIT_API_KEY=你的API密钥
DERIBIT_API_SECRET=你的API密钥密码
```

### 2. 测试系统

```bash
python3 test_sentiment_trading.py
```

### 3. 启动服务

```bash
# 方式A: 使用脚本
./start_sentiment_trading.sh

# 方式B: 使用systemd
sudo systemctl start sentiment_trading.service
sudo systemctl start sentiment_api.service
```

### 4. 配置防火墙

```bash
# Ubuntu/Debian
ufw allow 5002/tcp
ufw reload
```

### 5. 验证安装

```bash
curl http://localhost:5002/api/health
```

## 管理服务

```bash
cd backend
./manage_sentiment.sh
```

## 访问API

从你的电脑访问（替换为你的服务器IP）：

```bash
curl http://your_server_ip:5002/api/status
```

## 监控面板

1. 下载dashboard：
   ```bash
   scp root@your_server:/root/BTCTradingApp/BTCOptionsTrading/backend/sentiment_dashboard.html .
   ```

2. 编辑文件，修改API地址为你的服务器IP

3. 在浏览器中打开

---

完整文档：`SERVER_INSTALL_GUIDE.md`
