# 部署选项说明

根据不同的场景，选择合适的部署方式。

## 🚀 部署脚本对比

| 脚本 | 用途 | 耗时 | 何时使用 |
|------|------|------|----------|
| `deploy.sh` | 完整部署 | 5-15分钟 | 首次部署、依赖更新 |
| `quick_deploy.sh` | 快速部署 | 10-30秒 | 代码更新、无依赖变化 |
| `start_all.sh` | 启动服务 | 5-10秒 | 服务已停止，需要启动 |

---

## 📋 详细说明

### 1. deploy.sh - 完整部署

**执行步骤**：
1. 拉取最新代码
2. 安装/更新 Python 依赖（慢）
3. 安装/更新 npm 依赖（慢）
4. 停止旧进程
5. 启动新服务
6. 验证服务状态

**耗时原因**：
- Python 依赖安装：2-5分钟（numpy、pandas 等需要编译）
- npm 依赖安装：3-10分钟（几百个包需要下载）

**何时使用**：
- ✅ 首次部署
- ✅ requirements.txt 或 package.json 有更新
- ✅ 长时间未更新，不确定依赖是否变化
- ✅ 遇到依赖相关错误

**使用方法**：
```bash
./deploy.sh
```

---

### 2. quick_deploy.sh - 快速部署（推荐日常使用）

**执行步骤**：
1. 拉取最新代码
2. 停止旧进程
3. 启动新服务
4. 验证服务状态

**耗时**：10-30秒

**何时使用**：
- ✅ 只修改了代码，依赖没变
- ✅ 日常代码更新
- ✅ 快速修复 bug
- ✅ 频繁部署场景

**使用方法**：
```bash
./quick_deploy.sh
```

---

### 3. start_all.sh - 启动服务

**执行步骤**：
1. 选择启动方式（PM2/nohup/前台）
2. 启动后端
3. 启动前端
4. 验证服务状态

**耗时**：5-10秒

**何时使用**：
- ✅ 服务器重启后
- ✅ 手动停止服务后需要重启
- ✅ 首次配置启动方式

**使用方法**：
```bash
./start_all.sh
```

---

## 🎯 使用场景示例

### 场景 1: 首次部署

```bash
cd /root/BTCTradingApp/BTCOptionsTrading
git pull origin main
./deploy.sh
```

选择 PM2 启动方式（推荐）。

---

### 场景 2: 修复了一个 bug，快速部署

```bash
cd /root/BTCTradingApp/BTCOptionsTrading
./quick_deploy.sh
```

---

### 场景 3: 添加了新的 Python 包

```bash
cd /root/BTCTradingApp/BTCOptionsTrading
git pull origin main
cd backend
pip install -r requirements.txt
pm2 restart btc-backend
```

---

### 场景 4: 添加了新的 npm 包

```bash
cd /root/BTCTradingApp/BTCOptionsTrading
git pull origin main
cd frontend
npm install
npm run build
pm2 restart btc-frontend
```

---

### 场景 5: 服务器重启后

```bash
cd /root/BTCTradingApp/BTCOptionsTrading
./start_all.sh
```

或使用 PM2：
```bash
pm2 resurrect  # 恢复之前保存的进程
```

---

### 场景 6: 只想重启服务

```bash
# 使用 PM2
pm2 restart all

# 或手动
pkill -f "run_api.py"
pkill -f "npm"
./start_all.sh
```

---

## ⚡ 加速部署的技巧

### 1. 跳过依赖安装（最快）

如果确定依赖没变：

```bash
# 只更新代码和重启
git pull origin main
pm2 restart all
```

### 2. 使用 pip 缓存

```bash
# 首次安装时缓存
pip install -r requirements.txt

# 后续安装会使用缓存，更快
```

### 3. 使用 npm ci 代替 npm install

```bash
# npm ci 更快，但需要 package-lock.json
npm ci
```

### 4. 并行安装依赖

```bash
# 在两个终端同时运行
# 终端 1
cd backend && pip install -r requirements.txt

# 终端 2
cd frontend && npm install
```

### 5. 使用本地 npm 镜像（中国用户）

```bash
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 或使用 cnpm
npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install
```

---

## 🔍 监控部署进度

### 查看 Python 依赖安装进度

```bash
# 移除 --quiet 标志，显示详细输出
pip install -r requirements.txt -v
```

### 查看 npm 安装进度

```bash
# npm install 默认显示进度
npm install

# 或使用进度条
npm install --progress
```

### 实时查看日志

```bash
# 后端日志
tail -f backend/logs/api.log

# 前端日志
tail -f frontend/logs/frontend.log

# PM2 日志
pm2 logs
```

---

## 🐛 部署失败排查

### 1. 依赖安装失败

```bash
# 使用修复脚本
cd backend
./fix_dependencies.sh

# 或使用最小化依赖
pip install -r requirements-minimal.txt
```

### 2. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000
lsof -i :3000

# 停止进程
kill -9 <PID>
```

### 3. 权限问题

```bash
# 给脚本添加执行权限
chmod +x deploy.sh quick_deploy.sh start_all.sh

# 或使用 bash 运行
bash deploy.sh
```

### 4. Git 冲突

```bash
# 放弃本地修改
git reset --hard origin/main

# 或保存本地修改
git stash
git pull origin main
git stash pop
```

---

## 📊 部署时间参考

基于不同的服务器配置：

| 配置 | deploy.sh | quick_deploy.sh | start_all.sh |
|------|-----------|-----------------|--------------|
| 1核2G | 10-15分钟 | 20-30秒 | 10秒 |
| 2核4G | 5-8分钟 | 15-20秒 | 5秒 |
| 4核8G | 3-5分钟 | 10-15秒 | 5秒 |

---

## 💡 最佳实践

1. **日常开发**：使用 `quick_deploy.sh`
2. **依赖更新**：使用 `deploy.sh`
3. **生产环境**：使用 PM2 + `deploy.sh`
4. **测试环境**：使用 nohup + `quick_deploy.sh`
5. **定期备份**：在部署前备份数据库和配置

---

## 🔄 自动化部署（高级）

### 使用 Git Hooks

在服务器上设置 post-receive hook：

```bash
# 在 Git 仓库的 hooks 目录
cd /path/to/repo/.git/hooks
nano post-receive
```

添加：
```bash
#!/bin/bash
cd /root/BTCTradingApp/BTCOptionsTrading
./quick_deploy.sh
```

### 使用 Cron 定期更新

```bash
# 每天凌晨 2 点自动部署
crontab -e

# 添加
0 2 * * * cd /root/BTCTradingApp/BTCOptionsTrading && ./quick_deploy.sh >> /var/log/btc-deploy.log 2>&1
```

---

## 📞 需要帮助？

- 查看日志：`pm2 logs` 或 `tail -f backend/logs/api.log`
- 检查服务：`pm2 list` 或 `ps aux | grep python`
- 测试连接：`curl http://localhost:8000/api/health`
