# 服务器API故障排查指南

## 快速诊断

在服务器上运行诊断脚本：

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
./diagnose_api.sh
```

## 常见问题和解决方案

### 问题1: API服务未运行

**症状**: 无法访问 http://47.86.62.200:5002/api/health

**检查**:
```bash
# 检查进程
ps aux | grep sentiment_api.py

# 检查端口
netstat -tlnp | grep 5002
# 或
ss -tlnp | grep 5002
```

**解决方案**:
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend

# 方法1: 使用启动脚本
./start_api_service.sh

# 方法2: 手动启动
nohup python3 sentiment_api.py > logs/api.log 2>&1 &

# 方法3: 使用systemd服务（如果已配置）
sudo systemctl start sentiment-api
```

### 问题2: 防火墙阻止访问

**检查防火墙状态**:

```bash
# Ubuntu/Debian (UFW)
sudo ufw status

# CentOS/RHEL (Firewalld)
sudo firewall-cmd --list-ports
```

**解决方案**:

```bash
# Ubuntu/Debian
sudo ufw allow 5002/tcp
sudo ufw reload
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5002/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

### 问题3: 云服务商安全组未配置

**阿里云/腾讯云/AWS等**:

1. 登录云服务商控制台
2. 找到ECS/云服务器实例
3. 进入"安全组"设置
4. 添加入站规则：
   - 协议: TCP
   - 端口: 5002
   - 来源: 0.0.0.0/0 (或指定IP)
   - 动作: 允许

### 问题4: API服务启动失败

**查看日志**:
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend

# 查看API日志
tail -50 logs/sentiment_api.log

# 查看启动日志
cat logs/api_startup.log
```

**常见错误**:

1. **缺少.env配置**:
   ```bash
   cp .env.example .env
   nano .env  # 配置API密钥
   ```

2. **Python依赖缺失**:
   ```bash
   pip3 install -r requirements-sentiment.txt
   ```

3. **端口被占用**:
   ```bash
   # 查找占用5002端口的进程
   lsof -i :5002
   # 或
   netstat -tlnp | grep 5002
   
   # 杀死进程
   kill -9 <PID>
   ```

### 问题5: 服务运行但无法连接

**测试本地连接**:
```bash
# 在服务器上测试
curl http://localhost:5002/api/health
curl http://127.0.0.1:5002/api/health
```

如果本地可以访问但外部不行，问题在于防火墙或安全组。

## 完整检查清单

### 步骤1: 拉取最新代码
```bash
cd /root/BTCTradingApp
git pull
```

### 步骤2: 运行诊断脚本
```bash
cd BTCOptionsTrading/backend
./diagnose_api.sh
```

### 步骤3: 启动API服务
```bash
./start_api_service.sh
```

### 步骤4: 配置防火墙
```bash
# Ubuntu/Debian
sudo ufw allow 5002/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5002/tcp
sudo firewall-cmd --reload
```

### 步骤5: 配置云安全组
在云服务商控制台添加5002端口的入站规则

### 步骤6: 测试连接
```bash
# 在服务器上测试
curl http://localhost:5002/api/health

# 从本地测试
curl http://47.86.62.200:5002/api/health
```

## 监控和维护

### 查看服务状态
```bash
# 检查进程
ps aux | grep sentiment_api

# 查看日志
tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/sentiment_api.log
```

### 重启服务
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend

# 停止服务
pkill -f sentiment_api.py

# 启动服务
./start_api_service.sh
```

### 设置开机自启（可选）
```bash
# 创建systemd服务
sudo nano /etc/systemd/system/sentiment-api.service
```

内容：
```ini
[Unit]
Description=Sentiment Trading API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/BTCTradingApp/BTCOptionsTrading/backend
ExecStart=/usr/bin/python3 /root/BTCTradingApp/BTCOptionsTrading/backend/sentiment_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable sentiment-api
sudo systemctl start sentiment-api
sudo systemctl status sentiment-api
```

## 获取帮助

如果问题仍未解决：

1. 查看完整日志：`cat logs/sentiment_api.log`
2. 检查Python错误：`python3 sentiment_api.py`（前台运行查看错误）
3. 确认网络连接：`ping 47.86.62.200`
4. 检查DNS解析：`nslookup 47.86.62.200`

---

**服务器**: 47.86.62.200  
**端口**: 5002  
**诊断脚本**: `./diagnose_api.sh`  
**启动脚本**: `./start_api_service.sh`
