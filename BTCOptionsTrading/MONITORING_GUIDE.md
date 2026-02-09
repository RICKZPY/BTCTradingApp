# 系统监控指南

## 概述

BTC期权交易系统集成了完整的性能监控、健康检查和统计分析功能，帮助您实时了解系统运行状态。

## 功能特性

### 1. 性能监控
- **CPU使用率**: 实时监控CPU负载
- **内存使用**: 跟踪内存使用情况和可用内存
- **磁盘使用**: 监控磁盘空间使用率
- **网络连接**: 统计活动连接数
- **响应时间**: 记录每个请求的响应时间

### 2. 健康检查
- **自动健康评估**: 基于多个指标自动判断系统健康状态
- **阈值监控**: 可配置的健康检查阈值
- **问题诊断**: 自动识别和报告系统问题

### 3. 请求统计
- **请求计数**: 统计总请求数和错误数
- **错误率**: 计算请求错误率和成功率
- **响应时间分析**: 平均、最小、最大响应时间

### 4. 历史数据
- **指标历史**: 保存最近100个数据点
- **时间范围查询**: 支持查询指定时间范围的历史数据

## API接口

### 1. 健康检查 `/health`

**请求:**
```bash
GET http://localhost:8000/health
```

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-09T22:22:51.778562",
  "service": "BTC Options Trading System",
  "checks": {
    "cpu": true,
    "memory": true,
    "disk": true,
    "error_rate": true,
    "response_time": true
  },
  "issues": []
}
```

**状态说明:**
- `healthy`: 所有检查通过
- `degraded`: 60%以上检查通过
- `unhealthy`: 少于60%检查通过

### 2. 系统状态 `/status`

**请求:**
```bash
GET http://localhost:8000/status
```

**响应:**
```json
{
  "status": "operational",
  "timestamp": "2026-02-09T22:22:52.009905",
  "uptime": {
    "start_time": "2026-02-09T22:22:51.561471",
    "uptime_seconds": 0.448434,
    "uptime_formatted": "0:00:00"
  },
  "performance": {
    "cpu_percent": 0.0,
    "memory_percent": 90.5,
    "memory_used_mb": 3516.6,
    "disk_usage_percent": 5.9,
    "active_connections": 0
  },
  "requests": {
    "total": 2,
    "errors": 0,
    "error_rate": 0.0,
    "avg_response_time_ms": 107.16
  },
  "database": {
    "connected": true,
    "stats": {
      "strategies": 7,
      "backtests": 0,
      "positions": 0
    }
  }
}
```

### 3. 性能指标 `/metrics`

**请求:**
```bash
GET http://localhost:8000/metrics
```

**响应:**
```json
{
  "timestamp": "2026-02-09T22:22:52.009905",
  "cpu_percent": 0.0,
  "memory_percent": 90.5,
  "memory_used_mb": 3519.9,
  "memory_available_mb": 3120.1,
  "disk_usage_percent": 5.9,
  "active_connections": 0,
  "request_count": 3,
  "error_count": 0,
  "avg_response_time_ms": 111.24
}
```

### 4. 历史指标 `/metrics/history`

**请求:**
```bash
GET http://localhost:8000/metrics/history?minutes=10
```

**参数:**
- `minutes`: 查询时间范围（1-60分钟，默认10分钟）

**响应:**
```json
{
  "period_minutes": 10,
  "data_points": 4,
  "history": [
    {
      "timestamp": "2026-02-09T22:22:51.778562",
      "cpu_percent": 0.0,
      "memory_percent": 90.4,
      "memory_used_mb": 3516.6,
      "memory_available_mb": 3120.1,
      "disk_usage_percent": 5.9,
      "active_connections": 0,
      "request_count": 1,
      "error_count": 0,
      "avg_response_time_ms": 0.0
    }
  ]
}
```

### 5. 统计信息 `/statistics`

**请求:**
```bash
GET http://localhost:8000/statistics
```

**响应:**
```json
{
  "uptime": {
    "start_time": "2026-02-09T22:22:51.561471",
    "uptime_seconds": 0.448434,
    "uptime_formatted": "0:00:00"
  },
  "requests": {
    "total_requests": 5,
    "total_errors": 0,
    "error_rate": 0.0,
    "success_rate": 1.0,
    "avg_response_time_ms": 87.84,
    "min_response_time_ms": 1.52,
    "max_response_time_ms": 119.40
  }
}
```

### 6. 重置计数器 `/metrics/reset`

**请求:**
```bash
POST http://localhost:8000/metrics/reset
```

**响应:**
```json
{
  "status": "success",
  "message": "Metrics counters reset",
  "timestamp": "2026-02-09T22:22:52.009905"
}
```

**注意:** 此接口会重置所有请求计数器和统计数据，生产环境应添加认证保护。

## 响应时间头

所有API请求都会在响应头中包含 `X-Response-Time` 字段，显示该请求的处理时间：

```
X-Response-Time: 110.25ms
```

## 健康检查阈值

系统使用以下默认阈值进行健康检查：

| 指标 | 阈值 | 说明 |
|------|------|------|
| CPU使用率 | 80% | 超过此值触发警告 |
| 内存使用率 | 85% | 超过此值触发警告 |
| 磁盘使用率 | 90% | 超过此值触发警告 |
| 错误率 | 5% | 超过此值触发警告 |
| 平均响应时间 | 1000ms | 超过此值触发警告 |

## 使用示例

### Python示例

```python
import requests

# 检查系统健康
response = requests.get('http://localhost:8000/health')
health = response.json()

if health['status'] == 'healthy':
    print('系统运行正常')
else:
    print(f'系统状态: {health["status"]}')
    for issue in health['issues']:
        print(f'  - {issue}')

# 获取性能指标
response = requests.get('http://localhost:8000/metrics')
metrics = response.json()

print(f'CPU: {metrics["cpu_percent"]:.1f}%')
print(f'内存: {metrics["memory_percent"]:.1f}%')
print(f'平均响应时间: {metrics["avg_response_time_ms"]:.2f}ms')

# 获取历史数据
response = requests.get('http://localhost:8000/metrics/history?minutes=5')
history = response.json()

print(f'最近5分钟有 {history["data_points"]} 个数据点')
```

### JavaScript示例

```javascript
// 检查系统健康
fetch('http://localhost:8000/health')
  .then(response => response.json())
  .then(health => {
    console.log('系统状态:', health.status);
    if (health.issues.length > 0) {
      console.log('发现问题:');
      health.issues.forEach(issue => console.log('  -', issue));
    }
  });

// 获取系统状态
fetch('http://localhost:8000/status')
  .then(response => response.json())
  .then(status => {
    console.log('运行时长:', status.uptime.uptime_formatted);
    console.log('CPU使用率:', status.performance.cpu_percent + '%');
    console.log('总请求数:', status.requests.total);
  });
```

### cURL示例

```bash
# 健康检查
curl http://localhost:8000/health

# 系统状态
curl http://localhost:8000/status

# 性能指标
curl http://localhost:8000/metrics

# 历史数据（最近5分钟）
curl "http://localhost:8000/metrics/history?minutes=5"

# 统计信息
curl http://localhost:8000/statistics

# 重置计数器
curl -X POST http://localhost:8000/metrics/reset
```

## 监控集成

### 1. 自动化监控脚本

创建定时任务监控系统健康：

```bash
#!/bin/bash
# monitor.sh

while true; do
    health=$(curl -s http://localhost:8000/health)
    status=$(echo $health | jq -r '.status')
    
    if [ "$status" != "healthy" ]; then
        echo "[$(date)] 警告: 系统状态 $status"
        echo $health | jq '.issues'
    fi
    
    sleep 60  # 每分钟检查一次
done
```

### 2. 日志监控

系统会自动记录所有请求和错误到日志文件：

```
logs/api_YYYYMMDD.log
```

### 3. 告警集成

可以将监控数据集成到告警系统（如Prometheus、Grafana等）：

```python
# prometheus_exporter.py
from prometheus_client import start_http_server, Gauge
import requests
import time

# 创建指标
cpu_gauge = Gauge('system_cpu_percent', 'CPU使用率')
memory_gauge = Gauge('system_memory_percent', '内存使用率')
response_time_gauge = Gauge('system_avg_response_time_ms', '平均响应时间')

def collect_metrics():
    response = requests.get('http://localhost:8000/metrics')
    metrics = response.json()
    
    cpu_gauge.set(metrics['cpu_percent'])
    memory_gauge.set(metrics['memory_percent'])
    response_time_gauge.set(metrics['avg_response_time_ms'])

if __name__ == '__main__':
    start_http_server(8001)  # Prometheus指标端口
    while True:
        collect_metrics()
        time.sleep(15)  # 每15秒采集一次
```

## 性能优化建议

### 1. 高CPU使用率
- 检查是否有大量并发请求
- 优化计算密集型操作
- 考虑增加服务器资源

### 2. 高内存使用率
- 检查是否有内存泄漏
- 清理不必要的缓存数据
- 优化数据结构

### 3. 慢响应时间
- 检查数据库查询性能
- 添加缓存层
- 优化API接口逻辑

### 4. 高错误率
- 检查日志文件定位错误原因
- 验证输入数据
- 增强错误处理

## 故障排查

### 问题1: 监控接口返回500错误

**原因:** psutil库未安装

**解决:**
```bash
pip install psutil==5.9.5
```

### 问题2: 内存使用率一直很高

**原因:** 可能是系统本身内存占用高，不一定是应用问题

**解决:**
- 检查其他应用的内存占用
- 调整健康检查阈值
- 增加系统内存

### 问题3: 历史数据为空

**原因:** 系统刚启动，还没有收集到足够数据

**解决:**
- 等待几分钟后再查询
- 发送一些测试请求生成数据

## 测试

运行监控系统测试：

```bash
cd BTCOptionsTrading/backend
python test_monitoring.py
```

测试包括：
1. 健康检查接口
2. 系统状态接口
3. 性能指标接口
4. 历史指标接口
5. 统计信息接口
6. 负载模拟测试
7. 响应时间头验证

## 配置

监控系统的阈值可以在 `src/monitoring/system_monitor.py` 中配置：

```python
self.thresholds = {
    'cpu_percent': 80.0,           # CPU使用率阈值
    'memory_percent': 85.0,        # 内存使用率阈值
    'disk_usage_percent': 90.0,    # 磁盘使用率阈值
    'error_rate': 0.05,            # 错误率阈值（5%）
    'avg_response_time_ms': 1000.0 # 响应时间阈值（1秒）
}
```

## 最佳实践

1. **定期检查**: 建议每分钟检查一次健康状态
2. **设置告警**: 当系统状态变为 `degraded` 或 `unhealthy` 时发送告警
3. **保存历史**: 定期导出历史数据用于长期分析
4. **性能基线**: 建立正常运行时的性能基线，便于异常检测
5. **日志分析**: 结合日志文件进行深入分析

## 相关文档

- [API配置指南](API_CONFIGURATION_GUIDE.md)
- [WebSocket实时推送指南](WEBSOCKET_GUIDE.md)
- [系统使用指南](使用指南.md)
