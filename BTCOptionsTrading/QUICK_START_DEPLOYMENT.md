# 🚀 快速部署指南

## 3分钟完成部署

### 前提条件
- ✅ 一台云服务器（Ubuntu 20.04+）
- ✅ 服务器的SSH访问权限
- ✅ 服务器IP地址

---

## 步骤1: 上传代码（在本地Mac执行）

```bash
cd BTCOptionsTrading/deploy
./upload.sh root@YOUR_SERVER_IP
```

**示例**:
```bash
./upload.sh root@123.45.67.89
```

等待上传完成...

---

## 步骤2: 登录服务器

```bash
ssh root@YOUR_SERVER_IP
```

---

## 步骤3: 一键部署

```bash
cd /opt/btc-options-trading/deploy
chmod +x deploy.sh
sudo ./deploy.sh prod
```

等待10-15分钟，脚本会自动完成所有配置...

---

## 步骤4: 配置API密钥

```bash
# 编辑后端配置
sudo nano /opt/btc-options-trading/backend/.env
```

修改这几行：
```env
DERIBIT_API_KEY=your_real_api_key_here
DERIBIT_API_SECRET=your_real_api_secret_here
DERIBIT_TEST_MODE=false
```

保存并退出（Ctrl+X, Y, Enter）

---

## 步骤5: 重启服务

```bash
sudo supervisorctl restart btc-options-trading-backend
```

---

## 🎉 完成！

打开浏览器访问：
```
http://YOUR_SERVER_IP
```

---

## 常用命令

```bash
# 查看服务状态
sudo supervisorctl status

# 查看日志
sudo tail -f /var/log/btc-options-trading-backend.log

# 重启服务
sudo supervisorctl restart btc-options-trading-backend

# 监控系统
cd /opt/btc-options-trading/deploy
sudo ./monitor.sh
```

---

## 遇到问题？

查看详细文档：
- `deploy/DEPLOYMENT_GUIDE.md` - 完整部署指南
- `DEPLOYMENT_SUMMARY.md` - 部署总结

或运行环境检查：
```bash
cd /opt/btc-options-trading/deploy
sudo ./check-requirements.sh
```
