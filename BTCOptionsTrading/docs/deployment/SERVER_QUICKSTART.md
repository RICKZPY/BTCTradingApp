# 服务器快速启动指南

## 方法一：使用自动部署脚本（推荐）

```bash
# 1. SSH 登录到服务器
ssh your_username@your_server_ip

# 2. 进入项目目录
cd /path/to/BTCOptionsTrading

# 3. 运行部署脚本
./deploy.sh
```

脚本会自动完成：
- 拉取最新代码
- 更新依赖
- 停止旧进程
- 启动新服务
- 验证服务状态

## 方法二：手动部署

### 步骤 1: 更新代码

```bash
cd /path/to/BTCOptionsTrading
git pull origin main
```

### 步骤 2: 启动后端

```bash
cd backend

# 激活虚拟环境（如果使用）
source venv/bin/activate

# 或使用 conda
# conda activate your_env

# 后台启动
nohup python run_api.py > logs/api.log 2>&1 &

# 查看日志
tail -f logs/api.log
```

### 步骤 3: 启动前端

```bash
cd ../frontend

# 开发模式（快速启动）
nohup npm start > logs/frontend.log 2>&1 &

# 或生产模式（需要先构建）
npm run build
npx serve -s build -l 3000
```

## 方法三：使用 PM2（生产环境推荐）

### 首次安装 PM2

```bash
npm install -g pm2
```

### 启动服务

```bash
cd /path/to/BTCOptionsTrading

# 启动后端
cd backend
pm2 start run_api.py --name btc-backend --interpreter python3

# 启动前端
cd ../frontend
npm run build
pm2 serve build 3000 --name btc-frontend --spa

# 保存配置
pm2 save

# 设置开机自启
pm2 startup
```

### PM2 常用命令

```bash
pm2 list                    # 查看所有进程
pm2 logs                    # 查看所有日志
pm2 logs btc-backend        # 查看后端日志
pm2 logs btc-frontend       # 查看前端日志
pm2 restart btc-backend     # 重启后端
pm2 restart btc-frontend    # 重启前端
pm2 restart all             # 重启所有
pm2 stop all                # 停止所有
pm2 delete all              # 删除所有进程
pm2 monit                   # 实时监控
```

## 验证部署

### 检查服务状态

```bash
# 检查后端
curl http://localhost:8000/api/health

# 检查前端
curl http://localhost:3000

# 检查进程
ps aux | grep "run_api.py"
ps aux | grep "npm"
```

### 检查端口占用

```bash
# 检查 8000 端口（后端）
lsof -i :8000

# 检查 3000 端口（前端）
lsof -i :3000
```

## 停止服务

### 使用 PM2

```bash
pm2 stop btc-backend
pm2 stop btc-frontend
```

### 手动停止

```bash
# 查找进程 ID
ps aux | grep "run_api.py"
ps aux | grep "npm"

# 停止进程
kill -9 <PID>

# 或使用 pkill
pkill -f "run_api.py"
pkill -f "npm.*start"
```

## 常见问题

### 1. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000
lsof -i :3000

# 停止进程
kill -9 <PID>
```

### 2. 权限问题

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 如果需要 sudo
sudo ./deploy.sh
```

### 3. Python 环境问题

```bash
# 检查 Python 版本
python --version
python3 --version

# 检查虚拟环境
which python
```

### 4. Node.js 版本问题

```bash
# 检查 Node 版本（需要 >= 14）
node -v

# 更新 Node.js
# 使用 nvm
nvm install 18
nvm use 18
```

### 5. 依赖安装失败

```bash
# 清除缓存重新安装
cd backend
pip install -r requirements.txt --force-reinstall

cd ../frontend
rm -rf node_modules package-lock.json
npm install
```

## 访问应用

- 前端界面: `http://your_server_ip:3000`
- 后端 API: `http://your_server_ip:8000`
- API 文档: `http://your_server_ip:8000/docs`

## 配置反向代理（可选）

如果想通过域名访问，需要配置 Nginx：

```bash
# 安装 Nginx
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # CentOS/RHEL

# 创建配置文件
sudo nano /etc/nginx/sites-available/btc-trading

# 粘贴配置（参考 DEPLOYMENT_GUIDE.md）

# 启用配置
sudo ln -s /etc/nginx/sites-available/btc-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 安全提示

1. **防火墙配置**
   ```bash
   # 开放必要端口
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **环境变量**
   - 确保 `.env` 文件包含正确的 API 密钥
   - 不要在 git 中提交 `.env` 文件

3. **HTTPS**
   - 生产环境建议配置 SSL 证书
   - 可使用 Let's Encrypt 免费证书

## 监控和日志

### 查看日志

```bash
# 后端日志
tail -f backend/logs/api.log

# 前端日志（如果使用 nohup）
tail -f frontend/logs/frontend.log

# PM2 日志
pm2 logs
```

### 磁盘空间

```bash
# 检查磁盘使用
df -h

# 清理日志（如果需要）
> backend/logs/api.log
```

### 系统资源

```bash
# 查看 CPU 和内存
top
htop

# PM2 监控
pm2 monit
```

## 更新流程

每次有新代码时：

```bash
# 1. 拉取代码
git pull origin main

# 2. 重启服务
pm2 restart all

# 或使用部署脚本
./deploy.sh
```

## 需要帮助？

查看详细文档：
- `DEPLOYMENT_GUIDE.md` - 完整部署指南
- `README.md` - 项目说明
- `backend/README.md` - 后端文档
