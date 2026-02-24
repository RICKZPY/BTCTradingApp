# 低内存服务器部署指南（1GB RAM）

针对 2核1GB 配置的优化方案。

## ⚠️ 重要提示

1GB 内存对于同时运行前后端比较紧张，建议：
- **临时方案**：在本地构建前端，上传到服务器
- **长期方案**：升级到 2GB 或更高内存

---

## 🎯 方案一：本地构建，服务器部署（推荐）

### 在本地电脑构建前端

```bash
# 在本地电脑上
cd BTCOptionsTrading/frontend
npm install
npm run build

# 将 build 目录打包
tar -czf build.tar.gz build/

# 上传到服务器
scp build.tar.gz root@your_server_ip:/root/BTCTradingApp/BTCOptionsTrading/frontend/
```

### 在服务器上部署

```bash
# 在服务器上
cd /root/BTCTradingApp/BTCOptionsTrading/frontend

# 解压
tar -xzf build.tar.gz

# 使用 PM2 启动（只需要 serve，不需要构建）
pm2 serve build 3000 --name btc-frontend --spa
```

---

## 🎯 方案二：添加 Swap 空间（临时增加内存）

### 创建 2GB Swap

```bash
# 1. 创建 swap 文件
sudo fallocate -l 2G /swapfile

# 或使用 dd
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048

# 2. 设置权限
sudo chmod 600 /swapfile

# 3. 设置为 swap
sudo mkswap /swapfile

# 4. 启用 swap
sudo swapon /swapfile

# 5. 验证
free -h

# 6. 永久启用（添加到 /etc/fstab）
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 7. 优化 swap 使用
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

添加 swap 后，可以正常构建：

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/frontend
npm run build
```

---

## 🎯 方案三：限制 Node.js 内存使用

### 构建时限制内存

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/frontend

# 限制 Node.js 使用 512MB 内存
NODE_OPTIONS="--max-old-space-size=512" npm run build
```

### 修改 package.json

```json
{
  "scripts": {
    "build": "NODE_OPTIONS='--max-old-space-size=512' tsc && vite build",
    "build:low-mem": "NODE_OPTIONS='--max-old-space-size=384' tsc && vite build --minify false"
  }
}
```

---

## 🎯 方案四：分步构建

### 先构建 TypeScript，再构建 Vite

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/frontend

# 1. 先编译 TypeScript
npx tsc

# 2. 等待完成后，再运行 Vite
npx vite build

# 3. 如果还是内存不足，禁用压缩
npx vite build --minify false
```

---

## 🎯 方案五：只运行后端，前端在本地

### 服务器只运行后端

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
python run_api.py
```

### 本地运行前端

在本地电脑上：

```bash
cd BTCOptionsTrading/frontend

# 修改 .env 文件，指向服务器 API
echo "REACT_APP_API_URL=http://your_server_ip:8000" > .env

# 启动前端
npm start
```

然后在本地浏览器访问 `http://localhost:3000`

---

## 🎯 方案六：使用 Docker（推荐生产环境）

### 创建优化的 Dockerfile

```dockerfile
# 多阶段构建，减少最终镜像大小
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.9-slim
WORKDIR /app

# 安装 Python 依赖
COPY backend/requirements-minimal.txt ./
RUN pip install --no-cache-dir -r requirements-minimal.txt

# 复制后端代码
COPY backend/ ./

# 复制前端构建结果
COPY --from=frontend-builder /app/frontend/build ./static

# 安装 serve
RUN npm install -g serve

# 启动脚本
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000 3000
CMD ["./start.sh"]
```

---

## 📊 内存使用监控

### 实时监控内存

```bash
# 查看内存使用
free -h

# 实时监控
watch -n 1 free -h

# 查看进程内存使用
ps aux --sort=-%mem | head -10

# 使用 htop（更直观）
sudo apt install htop
htop
```

### 设置内存告警

```bash
# 创建监控脚本
cat > /root/check_memory.sh << 'EOF'
#!/bin/bash
THRESHOLD=90
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')

if [ $MEMORY_USAGE -gt $THRESHOLD ]; then
    echo "警告: 内存使用率 ${MEMORY_USAGE}% 超过阈值 ${THRESHOLD}%"
    # 可以添加重启服务的逻辑
    pm2 restart all
fi
EOF

chmod +x /root/check_memory.sh

# 添加到 crontab，每 5 分钟检查一次
crontab -e
# 添加: */5 * * * * /root/check_memory.sh
```

---

## 🔧 优化运行时内存

### 1. 使用生产模式

```bash
# 后端
export PYTHONOPTIMIZE=1
python run_api.py

# 前端使用构建版本，不要用 npm start
pm2 serve build 3000 --name btc-frontend --spa
```

### 2. 限制 PM2 内存

```bash
# 限制每个进程最大内存
pm2 start run_api.py --name btc-backend --interpreter python3 --max-memory-restart 300M
pm2 serve build 3000 --name btc-frontend --spa --max-memory-restart 200M
```

### 3. 关闭不必要的服务

```bash
# 查看运行的服务
systemctl list-units --type=service --state=running

# 停止不必要的服务（示例）
sudo systemctl stop apache2
sudo systemctl stop mysql
```

---

## 📈 性能优化建议

### 1. 使用轻量级数据库

SQLite（已使用）比 PostgreSQL/MySQL 占用更少内存。

### 2. 减少日志输出

```python
# 在 backend/.env 中
LOG_LEVEL=WARNING  # 而不是 DEBUG
```

### 3. 禁用不必要的功能

如果暂时不需要某些功能，可以注释掉：

```python
# 在 backend/src/api/app.py 中
# 注释掉不需要的路由
# app.include_router(websocket.router)  # WebSocket 比较占内存
```

---

## 🚀 推荐部署流程（1GB 内存）

### 步骤 1: 添加 Swap

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 步骤 2: 在本地构建前端

```bash
# 本地电脑
cd BTCOptionsTrading/frontend
npm run build
tar -czf build.tar.gz build/
scp build.tar.gz root@your_server_ip:/tmp/
```

### 步骤 3: 在服务器部署

```bash
# 服务器
cd /root/BTCTradingApp/BTCOptionsTrading

# 拉取代码
git pull origin main

# 解压前端构建
cd frontend
tar -xzf /tmp/build.tar.gz

# 启动后端
cd ../backend
pm2 start run_api.py --name btc-backend --interpreter python3 --max-memory-restart 400M

# 启动前端
cd ../frontend
pm2 serve build 3000 --name btc-frontend --spa --max-memory-restart 200M

# 保存配置
pm2 save
```

---

## 💡 长期建议

### 1. 升级服务器配置

建议升级到：
- **2核2GB**：可以正常运行（约 $10-15/月）
- **2核4GB**：流畅运行（约 $20-30/月）

### 2. 使用 CDN

将前端部署到 CDN（如 Vercel、Netlify），免费且性能更好：

```bash
# 在 Vercel 部署前端
cd frontend
vercel deploy --prod

# 服务器只运行后端
```

### 3. 使用无服务器方案

- 前端：Vercel/Netlify（免费）
- 后端：保持在当前服务器
- 数据库：SQLite 或云数据库

---

## 🔍 故障排查

### 内存不足症状

- npm build 卡住或失败
- 进程被 OOM Killer 杀死
- 系统响应缓慢

### 检查日志

```bash
# 查看系统日志
dmesg | grep -i "out of memory"
dmesg | grep -i "killed process"

# 查看 PM2 日志
pm2 logs --err
```

### 紧急恢复

```bash
# 重启服务器
sudo reboot

# 或清理内存
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches
```

---

## 📞 需要帮助？

如果遇到问题：
1. 检查内存使用：`free -h`
2. 查看进程：`pm2 list`
3. 查看日志：`pm2 logs`
4. 考虑升级配置或使用上述优化方案
