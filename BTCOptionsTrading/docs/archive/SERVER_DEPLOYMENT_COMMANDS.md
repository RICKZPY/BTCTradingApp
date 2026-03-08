# 服务器部署命令清单

## 步骤1：连接到服务器

打开终端（Terminal），然后执行：

```bash
ssh root@your_server_ip
```

如果使用特定端口：
```bash
ssh -p 端口号 root@your_server_ip
```

输入密码后即可登录。

---

## 步骤2：下载代码

### 方式A：如果服务器上还没有代码

```bash
# 克隆仓库
git clone https://github.com/RICKZPY/BTCTradingApp.git

# 进入目录
cd BTCTradingApp/BTCOptionsTrading
```

### 方式B：如果已经有代码，更新到最新版本

```bash
# 进入目录
cd BTCTradingApp/BTCOptionsTrading

# 拉取最新代码
git pull origin main
```

---

## 步骤3：运行安装脚本

### 如果服务器内存充足（>1GB）

```bash
chmod +x server_install.sh
./server_install.sh
```

### 如果服务器内存较少（<1GB）- 推荐

```bash
chmod +x server_install_low_memory.sh
./server_install_low_memory.sh
```

安装脚本会自动：
- 检查Python环境
- 安装依赖包
- 创建必要目录
- 配置.env模板

---

## 步骤4：配置API密钥

```bash
cd backend

# 编辑.env文件
nano .env
```

修改以下内容：
```
DERIBIT_API_KEY=你的真实API密钥
DERIBIT_API_SECRET=你的真实API密钥密码
```

保存并退出：
- 按 `Ctrl + O` 保存
- 按 `Enter` 确认
- 按 `Ctrl + X` 退出

---

## 步骤5：测试系统

```bash
# 确保在backend目录
cd ~/BTCTradingApp/BTCOptionsTrading/backend

# 运行测试
python3 test_sentiment_trading.py
```

如果看到测试通过，说明配置正确。

---

## 步骤6：启动服务

### 方式A：使用脚本启动（推荐）

```bash
./start_sentiment_trading.sh
```

### 方式B：使用systemd启动

```bash
sudo systemctl start sentiment_trading.service
sudo systemctl start sentiment_api.service

# 查看状态
sudo systemctl status sentiment_trading.service
```

---

## 步骤7：配置防火墙

### Ubuntu/Debian

```bash
sudo ufw allow 5002/tcp
sudo ufw reload
sudo ufw status
```

### CentOS/RHEL

```bash
sudo firewall-cmd --permanent --add-port=5002/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

### 云服务器

如果使用阿里云、腾讯云等，还需要在控制台添加安全组规则：
- 协议：TCP
- 端口：5002
- 来源：0.0.0.0/0

---

## 步骤8：验证部署

### 在服务器上测试

```bash
curl http://localhost:5002/api/health
```

应该返回：
```json
{
  "status": "healthy",
  "timestamp": "...",
  "trader_initialized": true
}
```

### 从本地电脑测试

打开新的终端窗口，执行：
```bash
curl http://your_server_ip:5002/api/health
```

---

## 常用管理命令

### 查看服务状态

```bash
cd ~/BTCTradingApp/BTCOptionsTrading/backend
./manage_sentiment.sh
```

或使用systemctl：
```bash
sudo systemctl status sentiment_trading.service
```

### 查看日志

```bash
# 实时日志
tail -f ~/BTCTradingApp/BTCOptionsTrading/backend/logs/sentiment_trading.log

# 或使用journalctl
sudo journalctl -u sentiment_trading.service -f
```

### 重启服务

```bash
# 使用脚本
cd ~/BTCTradingApp/BTCOptionsTrading/backend
./stop_sentiment_trading.sh
./start_sentiment_trading.sh

# 或使用systemd
sudo systemctl restart sentiment_trading.service
sudo systemctl restart sentiment_api.service
```

### 停止服务

```bash
# 使用脚本
./stop_sentiment_trading.sh

# 或使用systemd
sudo systemctl stop sentiment_trading.service
sudo systemctl stop sentiment_api.service
```

---

## 故障排查

### 如果安装时卡住

1. 按 `Ctrl + C` 中断
2. 增加swap空间：
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   free -h
   ```
3. 重新运行安装脚本

### 如果服务无法启动

```bash
# 查看详细错误
sudo journalctl -u sentiment_trading.service -n 50

# 检查Python环境
python3 --version
pip3 list | grep -E "aiohttp|fastapi"

# 检查.env配置
cat ~/BTCTradingApp/BTCOptionsTrading/backend/.env
```

### 如果API无法访问

```bash
# 检查服务是否运行
ps aux | grep sentiment

# 检查端口
netstat -tlnp | grep 5002

# 检查防火墙
sudo ufw status
```

---

## 完整部署流程（复制粘贴版）

```bash
# 1. 连接服务器
ssh root@your_server_ip

# 2. 下载代码
git clone https://github.com/RICKZPY/BTCTradingApp.git
cd BTCTradingApp/BTCOptionsTrading

# 3. 运行安装（低内存版本）
chmod +x server_install_low_memory.sh
./server_install_low_memory.sh

# 4. 配置API密钥
cd backend
nano .env
# 修改API密钥后保存退出

# 5. 测试
python3 test_sentiment_trading.py

# 6. 启动服务
./start_sentiment_trading.sh

# 7. 配置防火墙
sudo ufw allow 5002/tcp
sudo ufw reload

# 8. 验证
curl http://localhost:5002/api/health
```

---

## 下一步

部署成功后：

1. **配置监控面板**
   - 下载 `sentiment_dashboard.html` 到本地
   - 修改API地址为你的服务器IP
   - 在浏览器中打开

2. **设置定时任务**（可选）
   - 系统会自动在每天早上5点执行交易
   - 无需额外配置

3. **监控运行状态**
   - 定期查看日志
   - 使用管理脚本检查状态
   - 访问API查看交易历史

---

## 需要帮助？

- 查看完整文档：`SENTIMENT_TRADING_README.md`
- 低资源安装：`LOW_RESOURCE_INSTALL.md`
- 详细部署指南：`DEPLOYMENT_SENTIMENT.md`
