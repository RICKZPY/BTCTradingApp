# Backend 目录结构

## 核心文件
- `main.py` - 主应用入口
- `run_api.py` - API服务器启动脚本
- `run_simple_api.py` - 简化版API服务器
- `start_api.sh` - API启动脚本
- `historical_cli.py` - 历史数据命令行工具
- `daily_data_collector.py` - 每日数据收集器
- `collect_data_simple.py` - 简单数据收集脚本
- `simple_orderbook_collector.py` - 简单orderbook收集器（推荐使用）

## 目录说明

### `/src` - 源代码
核心业务逻辑和API实现

### `/scripts` - 工具脚本
- 环境检查和配置脚本
- 诊断和修复工具
- 部署和设置脚本
- 数据收集设置脚本

### `/tests` - 测试文件
所有测试脚本

### `/docs` - 文档
- API文档
- 使用指南
- 故障排除文档

### `/examples` - 示例代码
使用示例和演示脚本

### `/data` - 数据目录
- `/data/orderbook` - orderbook数据
- `/data/downloads` - 下载的CSV文件
- `/data/exports` - 导出的数据

### `/logs` - 日志文件
应用日志

## 快速开始

### 启动API服务器
```bash
./start_api.sh
```

### 收集Orderbook数据
```bash
python3 simple_orderbook_collector.py
```

### 设置定时任务
```bash
./scripts/setup_daily_orderbook.sh
```
