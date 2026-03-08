# 低资源服务器安装指南

## 问题诊断

如果在安装时卡在 "Preparing metadata (pyproject.toml)"，通常是因为：
1. 内存不足（<512MB）
2. 没有swap空间
3. pip在编译某些包时需要大量内存

## 🚀 解决方案

### 方案1：使用低内存安装脚本（推荐）

```bash
cd BTCTradingApp/BTCOptionsTrading
chmod +x server_install_low_memory.sh
./server_install_low_memory.sh
```

这个脚本会：
- 自动创建临时swap空间
- 使用国内镜像源加速下载
- 逐个安装依赖包，避免内存溢出
- 使用 `--no-cache-dir` 减少内存使用

### 方案2：手动配置swap空间

如果方案1还是卡住，先手动增加swap：

```bash
# 1. 创建2GB swap文件
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 验证swap已启用
free -h

# 3. 设置永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 4. 然后再运行安装脚本
./server_install_low_memory.sh
```

### 方案3：完全手动安装

如果自动脚本都失败，完全手动安装：

```bash
cd BTCTradingApp/BTCOptionsTrading/backend

# 1. 配置pip使用国内镜像
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

# 2. 升级pip
python3 -m pip install --upgrade pip --no-cache-dir

# 3. 逐个安装依赖（重要！）
pip3 install aiohttp --no-cache-dir
sleep 5

pip3 install fastapi --no-cache-dir
sleep 5

pip3 install uvicorn --no-cache-dir
sleep 5

pip3 install python-dotenv --no-cache-dir
sleep 5

# 4. 验证安装
python3 -c "import aiohttp, fastapi, uvicorn; print('所有依赖安装成功')"

# 5. 创建目录
mkdir -p data logs backups

# 6. 配置.env
cat > .env << 'EOF'
DERIBIT_API_KEY=your_api_key_here
DERIBIT_API_SECRET=your_api_secret_here
EOF

# 7. 编辑.env填入真实API密钥
nano .env

# 8. 设置权限
chmod +x *.sh

# 9. 测试
python3 test_sentiment_trading.py
```

### 方案4：使用预编译的wheel包

如果某个包一直卡住，可以尝试安装预编译版本：

```bash
# 对于aiohttp，可以尝试安装旧版本
pip3 install aiohttp==3.8.1 --no-cache-dir

# 或者跳过某些可选依赖
pip3 install fastapi --no-deps --no-cache-dir
pip3 install uvicorn --no-deps --no-cache-dir
```

## 🔧 优化建议

### 1. 永久增加swap空间

```bash
# 创建2GB swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 调整swappiness（可选）
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. 清理不必要的进程

```bash
# 查看内存使用
free -h
ps aux --sort=-%mem | head -10

# 停止不必要的服务
sudo systemctl stop apache2  # 如果有
sudo systemctl stop mysql    # 如果有
```

### 3. 使用轻量级Python环境

```bash
# 如果可能，使用pypy（更省内存）
# 或者使用miniconda而不是anaconda
```

## 📊 检查系统资源

```bash
# 查看内存
free -h

# 查看swap
swapon --show

# 查看磁盘空间
df -h

# 实时监控
htop  # 或 top
```

## 🐛 常见问题

### Q: 安装时提示 "Killed"
A: 这是内存不足导致的。增加swap空间后重试。

### Q: pip install 一直卡住不动
A: 
1. 按 Ctrl+C 中断
2. 增加swap空间
3. 使用 `--no-cache-dir` 参数
4. 逐个安装依赖包

### Q: 某个包安装失败
A: 尝试：
```bash
# 使用国内镜像
pip3 install package_name -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip3 install package_name -i https://mirrors.aliyun.com/pypi/simple/
```

### Q: 服务启动后很快崩溃
A: 
1. 检查内存：`free -h`
2. 查看日志：`tail -f logs/sentiment_trading.log`
3. 可能需要更多内存或优化代码

## 💡 最小配置要求

- **CPU**: 1核心
- **内存**: 512MB + 1GB swap
- **磁盘**: 2GB可用空间
- **网络**: 稳定的互联网连接

## 🎯 推荐配置

- **CPU**: 1-2核心
- **内存**: 1GB + 1GB swap
- **磁盘**: 5GB可用空间

## 📞 如果还是无法安装

考虑以下选项：

1. **升级服务器配置**
   - 增加内存到至少1GB
   - 或使用更高配置的服务器

2. **使用Docker**
   - 在本地构建Docker镜像
   - 上传到服务器运行

3. **使用云函数**
   - 将服务部署到AWS Lambda或阿里云函数计算
   - 按需运行，不占用持续资源

4. **本地运行**
   - 在本地电脑运行服务
   - 使用ngrok等工具暴露API

## ✅ 安装成功后

```bash
# 1. 配置API密钥
nano backend/.env

# 2. 测试
cd backend
python3 test_sentiment_trading.py

# 3. 启动服务
./start_sentiment_trading.sh

# 4. 验证
curl http://localhost:5002/api/health
```

## 📝 监控内存使用

启动服务后，监控内存：

```bash
# 实时监控
watch -n 5 free -h

# 查看进程内存
ps aux | grep sentiment

# 如果内存不足，考虑：
# 1. 增加swap
# 2. 优化代码减少内存使用
# 3. 升级服务器配置
```
