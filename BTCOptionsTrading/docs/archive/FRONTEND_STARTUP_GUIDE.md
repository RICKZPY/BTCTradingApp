# 前端启动和访问指南

## 方法一：开发模式启动（推荐用于测试）

### 在服务器上启动前端

```bash
# 1. 进入前端目录
cd /root/BTCTradingApp/BTCOptionsTrading/frontend

# 2. 安装依赖（首次运行或更新后）
npm install

# 3. 后台启动前端
nohup npm start > logs/frontend.log 2>&1 &

# 4. 查看日志确认启动成功
tail -f logs/frontend.log
```

看到 "webpack compiled successfully" 或 "Compiled successfully!" 表示启动成功。

### 从本地浏览器访问

有三种方法访问服务器上的前端：

#### 方法 1: 直接访问（需要开放端口）

```
http://your_server_ip:3000
```

**前提条件**：服务器防火墙需要开放 3000 端口

```bash
# 在服务器上开放端口
sudo ufw allow 3000
sudo ufw reload

# 或使用 firewalld
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

#### 方法 2: SSH 端口转发（推荐，无需开放端口）

在你的**本地电脑**上运行：

```bash
# 将服务器的 3000 端口转发到本地 3000 端口
ssh -L 3000:localhost:3000 root@your_server_ip

# 保持这个 SSH 连接打开
```

然后在本地浏览器访问：
```
http://localhost:3000
```

如果本地 3000 端口被占用，可以使用其他端口：
```bash
# 转发到本地 8080 端口
ssh -L 8080:localhost:3000 root@your_server_ip

# 访问 http://localhost:8080
```

#### 方法 3: 使用 Nginx 反向代理（生产环境推荐）

见下文"生产环境部署"部分。

---

## 方法二：生产模式启动（推荐用于生产环境）

### 构建生产版本

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/frontend

# 1. 构建生产版本
npm run build

# 2. 使用 serve 提供静态文件
npx serve -s build -l 3000

# 或后台运行
nohup npx serve -s build -l 3000 > logs/frontend.log 2>&1 &
```

---

## 方法三：使用 PM2 管理（最推荐）

### 安装 PM2

```bash
npm install -g pm2
```

### 启动前端

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/frontend

# 开发模式
pm2 start npm --name btc-frontend -- start

# 或生产模式（推荐）
npm run build
pm2 serve build 3000 --name btc-frontend --spa

# 查看状态
pm2 list

# 查看日志
pm2 logs btc-frontend

# 保存配置
pm2 save

# 设置开机自启
pm2 startup
```

### PM2 管理命令

```bash
pm2 restart btc-frontend    # 重启
pm2 stop btc-frontend        # 停止
pm2 delete btc-frontend      # 删除
pm2 logs btc-frontend        # 查看日志
pm2 monit                    # 实时监控
```

---

## 配置 Nginx 反向代理（生产环境）

### 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 配置 Nginx

创建配置文件：

```bash
sudo nano /etc/nginx/sites-available/btc-trading
```

粘贴以下配置：

```nginx
server {
    listen 80;
    server_name your_domain.com;  # 或使用服务器 IP

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

启用配置：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/btc-trading /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx

# 设置开机自启
sudo systemctl enable nginx
```

现在可以通过以下方式访问：
```
http://your_server_ip
```

### 配置 HTTPS（可选但推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书并自动配置
sudo certbot --nginx -d your_domain.com

# 证书会自动续期
```

---

## 完整启动流程

### 使用 PM2（推荐）

```bash
# 1. 启动后端
cd /root/BTCTradingApp/BTCOptionsTrading/backend
pm2 start run_api.py --name btc-backend --interpreter python3

# 2. 启动前端
cd ../frontend
npm run build
pm2 serve build 3000 --name btc-frontend --spa

# 3. 保存配置
pm2 save

# 4. 查看状态
pm2 list
```

### 使用 nohup

```bash
# 1. 启动后端
cd /root/BTCTradingApp/BTCOptionsTrading/backend
nohup python run_api.py > logs/api.log 2>&1 &

# 2. 启动前端
cd ../frontend
nohup npm start > logs/frontend.log 2>&1 &

# 3. 查看进程
ps aux | grep "run_api.py"
ps aux | grep "npm"
```

---

## 访问方式总结

| 方式 | 地址 | 优点 | 缺点 |
|------|------|------|------|
| 直接访问 | `http://server_ip:3000` | 简单直接 | 需要开放端口 |
| SSH 转发 | `http://localhost:3000` | 安全，无需开放端口 | 需要保持 SSH 连接 |
| Nginx 代理 | `http://server_ip` | 专业，支持 HTTPS | 需要配置 Nginx |

---

## 验证部署

### 检查服务状态

```bash
# 检查后端
curl http://localhost:8000/api/health

# 检查前端
curl http://localhost:3000

# 检查端口
netstat -tlnp | grep 8000
netstat -tlnp | grep 3000
```

### 在浏览器中测试

1. 访问前端地址
2. 应该能看到 BTC Options Trading 界面
3. 检查浏览器控制台是否有错误
4. 测试 API 连接（在设置页面）

---

## 常见问题

### 1. 前端无法连接后端

**检查后端 API 地址配置**：

```bash
cd frontend
cat .env
```

应该包含：
```
REACT_APP_API_URL=http://localhost:8000
```

如果使用域名或外部 IP，需要修改：
```
REACT_APP_API_URL=http://your_server_ip:8000
```

修改后重新构建：
```bash
npm run build
```

### 2. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :3000

# 停止进程
kill -9 <PID>
```

### 3. npm install 失败

```bash
# 清除缓存
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 4. 权限问题

```bash
# 给当前用户权限
sudo chown -R $USER:$USER /root/BTCTradingApp/BTCOptionsTrading/frontend
```

### 5. 内存不足

```bash
# 增加 Node.js 内存限制
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

---

## 停止服务

### PM2

```bash
pm2 stop btc-frontend
pm2 stop btc-backend
```

### nohup

```bash
pkill -f "npm.*start"
pkill -f "run_api.py"
```

---

## 更新前端

```bash
# 1. 拉取最新代码
cd /root/BTCTradingApp/BTCOptionsTrading
git pull origin main

# 2. 更新依赖
cd frontend
npm install

# 3. 重启服务
pm2 restart btc-frontend

# 或重新构建
npm run build
pm2 restart btc-frontend
```

---

## 监控和日志

### PM2 日志

```bash
pm2 logs btc-frontend        # 查看前端日志
pm2 logs btc-backend         # 查看后端日志
pm2 logs                     # 查看所有日志
pm2 flush                    # 清空日志
```

### 手动日志

```bash
tail -f frontend/logs/frontend.log
tail -f backend/logs/api.log
```

---

## 性能优化

### 1. 启用 Gzip 压缩（Nginx）

在 Nginx 配置中添加：

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
```

### 2. 缓存静态资源（Nginx）

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. 使用生产构建

始终在生产环境使用 `npm run build` 而不是 `npm start`。

---

## 安全建议

1. **使用 HTTPS**
   - 配置 SSL 证书
   - 强制 HTTPS 重定向

2. **限制访问**
   - 使用防火墙规则
   - 配置 IP 白名单（如果需要）

3. **定期更新**
   - 更新 Node.js 和 npm
   - 更新依赖包

4. **环境变量**
   - 不要在代码中硬编码敏感信息
   - 使用 `.env` 文件管理配置

---

## 快速命令参考

```bash
# 启动所有服务（PM2）
pm2 start all

# 重启所有服务
pm2 restart all

# 停止所有服务
pm2 stop all

# 查看状态
pm2 list

# 查看日志
pm2 logs

# 监控
pm2 monit
```
