# 情绪交易API服务 - 持续运行设置

## 概述

`sentiment_api.py`提供HTTP接口来查询交易状态、持仓和历史。本指南介绍如何让API服务在服务器上持续运行，即使关闭SSH也不会停止。

## 三种运行方式

### 方式1：使用nohup（最简单）

适合快速测试和临时使用。

#### 启动服务

```bash
cd ~/BTCOptionsTrading/backend
./start_sentiment_api.sh
```

输出：
```
✓ API服务已启动 (PID: 12345)

服务信息:
  PID: 12345
  端口: 5002
  日志: /root/BTCOptionsTrading/backend/logs/sentiment_api.log

测试访问:
  curl http://localhost:5002/api/health
```

#### 停止服务

```bash
./stop_sentiment_api.sh
```

#### 查看日志

```bash
tail -f logs/sentiment_api.log
```

#### 优点
- ✅ 简单快速
- ✅ 不需要root权限
- ✅ SSH断开后继续运行

#### 缺点
- ❌ 服务崩溃后不会自动重启
- ❌ 服务器重启后需要手动启动

---

### 方式2：使用systemd服务（推荐）

适合生产环境，自动重启和开机自启。

#### 安装服务

```bash
cd ~/BTCOptionsTrading/backend
sudo ./setup_api_service.sh
```

#### 管理服务

```bash
# 查看状态
sudo systemctl status sentiment_api

# 启动服务
sudo systemctl start sentiment_api

# 停止服务
sudo systemctl stop sentiment_api

# 重启服务
sudo systemctl restart sentiment_api

# 查看日志
sudo journalctl -u sentiment_api -f

# 查看最近50行日志
sudo journalctl -u sentiment_api -n 50
```

#### 优点
- ✅ 服务崩溃自动重启
- ✅ 开机自动启动
- ✅ 标准化管理
- ✅ 集成日志系统

#### 缺点
- ❌ 需要root权限
- ❌ 配置稍复杂

---

### 方式3：使用screen/tmux

适合开发和调试。

#### 使用screen

```bash
# 安装screen（如果没有）
sudo apt install screen  # Ubuntu/Debian
sudo yum install screen  # CentOS/RHEL

# 创建新session
screen -S sentiment_api

# 在screen中启动服务
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
python3 sentiment_api.py

# 按 Ctrl+A 然后按 D 来detach（服务继续运行）

# 重新连接
screen -r sentiment_api

# 列出所有session
screen -ls

# 关闭session（在session内）
exit
```

#### 使用tmux

```bash
# 安装tmux（如果没有）
sudo apt install tmux  # Ubuntu/Debian
sudo yum install tmux  # CentOS/RHEL

# 创建新session
tmux new -s sentiment_api

# 在tmux中启动服务
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
python3 sentiment_api.py

# 按 Ctrl+B 然后按 D 来detach

# 重新连接
tmux attach -t sentiment_api

# 列出所有session
tmux ls

# 关闭session
tmux kill-session -t sentiment_api
```

---

## 推荐配置

### 生产环境

使用**systemd服务**（方式2）：

```bash
cd ~/BTCOptionsTrading/backend
sudo ./setup_api_service.sh
```

### 开发/测试环境

使用**nohup**（方式1）：

```bash
cd ~/BTCOptionsTrading/backend
./start_sentiment_api.sh
```

---

## 验证服务运行

### 1. 检查进程

```bash
ps aux | grep sentiment_api
```

应该看到类似：
```
root     12345  0.5  2.1  123456  87654 ?  S    10:00   0:01 python3 sentiment_api.py
```

### 2. 测试API访问

```bash
# 健康检查
curl http://localhost:5002/api/health

# 查看状态
curl http://localhost:5002/api/status | python3 -m json.tool

# 查看持仓
curl http://localhost:5002/api/positions | python3 -m json.tool
```

### 3. 检查端口

```bash
netstat -tlnp | grep 5002
# 或
ss -tlnp | grep 5002
```

应该看到：
```
tcp  0  0  0.0.0.0:5002  0.0.0.0:*  LISTEN  12345/python3
```

---

## 远程访问配置

如果需要从外部访问API：

### 1. 配置防火墙

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5002/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=5002/tcp
sudo firewall-cmd --reload
```

### 2. 测试远程访问

```bash
# 从本地机器测试
curl http://your_server_ip:5002/api/health
```

### 3. 安全建议

如果API包含敏感信息，建议：

1. **使用反向代理（Nginx）**：
```nginx
server {
    listen 80;
    server_name your_domain.com;
    
    location /api/ {
        proxy_pass http://localhost:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **添加认证**：
   - 在API中添加token认证
   - 使用Nginx basic auth

3. **使用HTTPS**：
   - 配置SSL证书
   - 使用Let's Encrypt

---

## 故障排查

### API服务无法启动

1. **检查端口占用**：
```bash
netstat -tlnp | grep 5002
```

如果端口被占用：
```bash
# 找到占用进程
lsof -i :5002

# 停止占用进程
kill <PID>
```

2. **检查Python依赖**：
```bash
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
pip install -r requirements.txt
```

3. **查看错误日志**：
```bash
tail -50 logs/sentiment_api.log
```

### 服务运行但无法访问

1. **检查防火墙**：
```bash
sudo ufw status
# 或
sudo firewall-cmd --list-all
```

2. **检查服务监听地址**：
```bash
netstat -tlnp | grep 5002
```

确保监听`0.0.0.0:5002`而不是`127.0.0.1:5002`

3. **测试本地访问**：
```bash
curl http://localhost:5002/api/health
```

### SSH断开后服务停止

如果使用方式1（nohup）但服务仍然停止：

1. **确认使用了nohup**：
```bash
./start_sentiment_api.sh
```

2. **检查PID文件**：
```bash
cat sentiment_api.pid
ps -p $(cat sentiment_api.pid)
```

3. **改用systemd**（推荐）：
```bash
sudo ./setup_api_service.sh
```

---

## 监控和维护

### 查看资源使用

```bash
# 查看进程资源
top -p $(cat sentiment_api.pid)

# 或使用htop
htop -p $(cat sentiment_api.pid)
```

### 日志轮转

创建logrotate配置：

```bash
sudo nano /etc/logrotate.d/sentiment_api
```

内容：
```
/root/BTCOptionsTrading/backend/logs/sentiment_api.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

### 定期检查

创建监控脚本：

```bash
cat > ~/check_api.sh << 'EOF'
#!/bin/bash
if ! curl -s http://localhost:5002/api/health > /dev/null; then
    echo "API服务异常，尝试重启..."
    cd ~/BTCOptionsTrading/backend
    ./stop_sentiment_api.sh
    sleep 2
    ./start_sentiment_api.sh
fi
EOF

chmod +x ~/check_api.sh
```

添加到crontab（每5分钟检查）：
```bash
crontab -e
```

添加：
```
*/5 * * * * ~/check_api.sh
```

---

## 快速参考

### 启动服务（nohup方式）
```bash
cd ~/BTCOptionsTrading/backend
./start_sentiment_api.sh
```

### 停止服务（nohup方式）
```bash
./stop_sentiment_api.sh
```

### 启动服务（systemd方式）
```bash
sudo systemctl start sentiment_api
```

### 查看日志
```bash
tail -f logs/sentiment_api.log
# 或（systemd）
sudo journalctl -u sentiment_api -f
```

### 测试API
```bash
curl http://localhost:5002/api/health
```

---

## 总结

- ✅ **快速测试**：使用`./start_sentiment_api.sh`
- ✅ **生产环境**：使用`sudo ./setup_api_service.sh`
- ✅ **关闭SSH**：服务继续运行
- ✅ **自动重启**：systemd自动处理
- ✅ **开机自启**：systemd自动配置

选择适合你的方式，让API服务稳定运行！
