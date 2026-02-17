# 部署检查清单

使用这个清单确保部署的每个步骤都正确完成。

## 📋 部署前检查

- [ ] 服务器已准备好（Ubuntu 20.04+）
- [ ] 有服务器的SSH访问权限
- [ ] 知道服务器的IP地址
- [ ] 本地代码已更新到最新版本
- [ ] 已准备好Deribit API密钥（如需真实交易）

## 📤 上传代码

- [ ] 运行 `./upload.sh user@server-ip`
- [ ] 确认上传成功，无错误信息
- [ ] SSH登录服务器验证文件存在

## 🔧 环境检查

- [ ] 运行 `./check-requirements.sh`
- [ ] 所有必需软件已安装
- [ ] 端口80和8000可用
- [ ] 磁盘空间充足（>20GB）
- [ ] 内存充足（>4GB）

## 🚀 部署执行

- [ ] 运行 `sudo ./deploy.sh prod`
- [ ] 脚本执行完成，无错误
- [ ] 后端服务已启动
- [ ] Nginx已启动
- [ ] 防火墙已配置

## ⚙️ 配置文件

### 后端配置 (`/opt/btc-options-trading/backend/.env`)

- [ ] `ENVIRONMENT=production`
- [ ] `API_DEBUG=false`
- [ ] `DERIBIT_API_KEY` 已设置
- [ ] `DERIBIT_API_SECRET` 已设置
- [ ] `DERIBIT_TEST_MODE` 设置正确
- [ ] `API_HOST=0.0.0.0`
- [ ] `API_PORT=8000`

### 前端配置 (`/opt/btc-options-trading/frontend/.env`)

- [ ] `VITE_API_BASE_URL` 已设置为正确的地址
- [ ] 地址格式正确（http://或https://）

### Nginx配置 (`/etc/nginx/sites-available/btc-options-trading`)

- [ ] `server_name` 已设置（如有域名）
- [ ] 配置文件语法正确 (`sudo nginx -t`)
- [ ] 站点已启用

## 🔄 服务启动

- [ ] 后端服务运行中
  ```bash
  sudo supervisorctl status btc-options-trading-backend
  ```
- [ ] Nginx运行中
  ```bash
  sudo systemctl status nginx
  ```
- [ ] 端口监听正常
  ```bash
  sudo netstat -tlnp | grep -E ':(80|8000)'
  ```

## 🧪 功能测试

### 后端测试

- [ ] API健康检查
  ```bash
  curl http://localhost:8000/api/health
  ```
- [ ] API文档可访问
  ```bash
  curl http://localhost:8000/docs
  ```

### 前端测试

- [ ] 浏览器访问 `http://server-ip`
- [ ] 页面正常加载
- [ ] 无JavaScript错误（F12查看控制台）
- [ ] 可以查看策略模板
- [ ] 可以创建新策略
- [ ] API请求正常（Network标签查看）

### 完整流程测试

- [ ] 创建一个测试策略
- [ ] 运行回测
- [ ] 查看回测结果
- [ ] 删除测试策略

## 📊 监控设置

- [ ] 监控脚本可执行
  ```bash
  sudo ./monitor.sh
  ```
- [ ] 设置定时监控（可选）
  ```bash
  sudo crontab -e
  # 添加: */5 * * * * /opt/btc-options-trading/deploy/monitor.sh
  ```

## 🔒 安全配置

- [ ] 防火墙已启用
  ```bash
  sudo ufw status
  ```
- [ ] 只开放必要端口（22, 80, 443）
- [ ] SSH密钥登录已配置（推荐）
- [ ] 已禁用SSH密码登录（推荐）
- [ ] HTTPS已配置（如有域名）
  ```bash
  sudo certbot --nginx -d your-domain.com
  ```

## 💾 备份设置

- [ ] 创建备份目录
  ```bash
  sudo mkdir -p /opt/backups
  ```
- [ ] 测试数据库备份
  ```bash
  sudo cp /opt/btc-options-trading/backend/data/btc_options.db \
         /opt/backups/btc_options_test.db
  ```
- [ ] 设置自动备份（可选）

## 📝 日志检查

- [ ] 后端日志正常
  ```bash
  sudo tail -50 /var/log/btc-options-trading-backend.log
  ```
- [ ] Nginx访问日志正常
  ```bash
  sudo tail -50 /var/log/nginx/btc-options-trading_access.log
  ```
- [ ] 无严重错误信息

## 📚 文档准备

- [ ] 记录服务器IP地址
- [ ] 记录管理员账号信息
- [ ] 记录API密钥位置
- [ ] 记录重要命令和路径
- [ ] 准备故障排查文档

## ✅ 最终验证

- [ ] 系统可以从外网访问
- [ ] 所有核心功能正常工作
- [ ] 性能满足要求
- [ ] 日志记录正常
- [ ] 监控正常运行

## 🎉 部署完成

- [ ] 通知相关人员系统已上线
- [ ] 记录部署时间和版本
- [ ] 创建系统使用文档
- [ ] 安排定期维护计划

---

## 📞 问题联系

如果遇到问题：
1. 查看 `DEPLOYMENT_GUIDE.md` 故障排查章节
2. 检查日志文件
3. 运行 `./monitor.sh` 查看系统状态
4. 查看 `DEPLOYMENT_SUMMARY.md` 常见问题

---

**部署日期**: _______________  
**部署人员**: _______________  
**服务器IP**: _______________  
**域名**: _______________ (如有)  
**版本**: _______________
