# 部署指南

本指南说明如何将更新推送到服务器并启动前后端服务。

## 本次更新内容

### 修复的问题
1. **快速交易功能修复**
   - 修复了 `test_mode` 参数错误（改为 `testnet`）
   - 添加了 `DeribitTrader.test_connection()` 方法
   - 修复了 SQLAlchemy 会话管理问题（使用 `joinedload` 预加载关联数据）
   - 移除了对不存在的 `mid_price` 属性的访问
   - 改用市价单确保快速成交
   - 修复了错误处理逻辑

2. **修改的文件**
   - `backend/src/api/routes/quick_trading.py` - 快速交易路由
   - `backend/src/trading/deribit_trader.py` - 交易客户端
   - `backend/src/trading/strategy_executor.py` - 策略执行器
   - `backend/src/storage/dao.py` - 数据访问层

## 部署步骤

### 1. 提交并推送代码

```bash
cd BTCOptionsTrading

# 添加所有更改
git add .

# 提交更改
git commit -m "修复快速交易功能：修复参数错误、会话管理和价格获取问题"

# 推送到远程仓库
git push origin main
```

### 2. 在服务器上更新代码

```bash
# SSH 登录到服务器
ssh your_username@your_server_ip

# 进入项目目录
cd /path/to/BTCOptionsTrading

# 拉取最新代码
git pull origin main
```

### 3. 启动后端服务

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（如果使用）
source venv/bin/activate  # 或者 conda activate your_env

# 安装/更新依赖（如果需要）
pip install -r requirements.txt

# 检查环境配置
python scripts/check_env_simple.py

# 启动后端 API（使用 nohup 在后台运行）
nohup python run_api.py > logs/api.log 2>&1 &

# 或者使用 screen/tmux
screen -S btc-api
python run_api.py
# 按 Ctrl+A 然后 D 来分离 screen

# 查看日志确认启动成功
tail -f logs/api.log
```

### 4. 启动前端服务

```bash
# 进入前端目录
cd ../frontend

# 安装/更新依赖（如果需要）
npm install

# 构建生产版本
npm run build

# 使用 serve 或 nginx 提供静态文件服务
# 方法 1: 使用 serve
npx serve -s build -l 3000

# 方法 2: 使用 PM2（推荐用于生产环境）
npm install -g pm2
pm2 serve build 3000 --name btc-frontend --spa

# 或者在开发模式下运行
nohup npm start > logs/frontend.log 2>&1 &
```

### 5. 使用 PM2 管理进程（推荐）

PM2 是一个生产级的进程管理器，可以自动重启、日志管理等。

```bash
# 安装 PM2
npm install -g pm2

# 启动后端
cd backend
pm2 start run_api.py --name btc-backend --interpreter python3

# 启动前端（生产模式）
cd ../frontend
npm run build
pm2 serve build 3000 --name btc-frontend --spa

# 查看进程状态
pm2 list

# 查看日志
pm2 logs btc-backend
pm2 logs btc-frontend

# 保存 PM2 配置
pm2 save

# 设置开机自启
pm2 startup
```

### 6. 验证部署

```bash
# 检查后端是否运行
curl http://localhost:8000/api/health

# 检查前端是否运行
curl http://localhost:3000

# 测试快速交易 API
curl http://localhost:8000/api/quick-trading/test-connection?api_key=YOUR_KEY&api_secret=YOUR_SECRET&test_mode=true
```

### 7. 配置反向代理（可选，用于生产环境）

如果使用 Nginx 作为反向代理：

```nginx
# /etc/nginx/sites-available/btc-trading
server {
    listen 80;
    server_name your_domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/btc-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 常用管理命令

### PM2 命令
```bash
pm2 list                    # 查看所有进程
pm2 restart btc-backend     # 重启后端
pm2 restart btc-frontend    # 重启前端
pm2 stop btc-backend        # 停止后端
pm2 logs btc-backend        # 查看后端日志
pm2 monit                   # 监控所有进程
```

### 手动启动/停止
```bash
# 查找进程
ps aux | grep "run_api.py"
ps aux | grep "npm"

# 停止进程
kill -9 <PID>

# 或使用 pkill
pkill -f "run_api.py"
pkill -f "npm start"
```

## 故障排查

### 后端无法启动
1. 检查端口是否被占用：`lsof -i :8000`
2. 检查日志：`tail -f backend/logs/api.log`
3. 检查环境变量：`cat backend/.env`
4. 检查 Python 依赖：`pip list`

### 前端无法启动
1. 检查端口是否被占用：`lsof -i :3000`
2. 检查 Node 版本：`node -v`（需要 >= 14）
3. 清除缓存：`rm -rf node_modules package-lock.json && npm install`

### 快速交易功能问题
1. 检查 API 密钥配置
2. 查看后端日志中的错误信息
3. 测试 Deribit 连接：`python backend/scripts/diagnose_deribit_connection.py`

## 安全建议

1. **不要提交敏感信息**
   - 确保 `.env` 文件在 `.gitignore` 中
   - 不要在代码中硬编码 API 密钥

2. **使用 HTTPS**
   - 在生产环境中配置 SSL 证书
   - 可以使用 Let's Encrypt 免费证书

3. **防火墙配置**
   - 只开放必要的端口（80, 443）
   - 限制数据库端口的访问

4. **定期备份**
   - 备份数据库：`backend/data/btc_options.db`
   - 备份配置文件：`backend/.env`

## 监控和维护

1. **日志轮转**
   - 配置 logrotate 防止日志文件过大

2. **性能监控**
   - 使用 PM2 监控内存和 CPU 使用
   - 定期检查磁盘空间

3. **更新维护**
   - 定期更新依赖包
   - 关注安全漏洞通知
