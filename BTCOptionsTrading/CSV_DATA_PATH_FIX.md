# CSV数据路径修复 (CSV Data Path Fix)

## 问题 (Problem)
CSV API 只查找 `/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots` 目录中的文件，但你把文件放在了 `data/downloads` 目录。

## 解决方案 (Solution)
已更新 CSV API 以支持多个数据源位置。现在会自动查找以下目录（按优先级）：

1. `./data/downloads` - 本地相对路径（优先）
2. `/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots` - 服务器路径
3. `/root/BTCTradingApp/BTCOptionsTrading/backend/data/downloads` - 服务器下载路径
4. `data/daily_snapshots` - 备用相对路径

## 修改内容 (Changes Made)

### 后端 (`backend/src/api/routes/csv_data.py`)
- ✓ 添加 `CSV_DATA_DIRS` 列表支持多个目录
- ✓ 添加 `get_csv_data_dir()` 函数自动查找存在的目录
- ✓ 更新所有 API 端点使用动态目录
- ✓ 在响应中返回 `data_dir` 字段显示实际使用的目录

## 使用方式 (Usage)

### 方式1: 使用本地相对路径（推荐）
```bash
# 在后端目录下创建 data/downloads 目录
mkdir -p data/downloads

# 把 CSV 文件放入该目录
cp your_files.csv data/downloads/
```

### 方式2: 使用服务器路径
```bash
# 把文件放在服务器的这个目录
/root/BTCTradingApp/BTCOptionsTrading/backend/data/downloads/
```

### 方式3: 使用原始路径
```bash
# 或者放在原始位置
/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots/
```

## 验证修复 (Verification)

### 1. 重启后端 API
```bash
cd BTCOptionsTrading/backend
python -m uvicorn src.api.app:app --reload
```

### 2. 检查 API 响应
```bash
# 获取摘要，查看 data_dir 字段
curl http://localhost:8000/api/csv/summary | jq '.data_dir'

# 应该输出类似：
# "./data/downloads"
```

### 3. 刷新前端
- 打开历史数据分析页面
- 点击"CSV数据分析"标签页
- 下拉菜单应该显示你的合约列表

## 调试技巧 (Debugging Tips)

### 查看实际使用的目录
```bash
curl http://localhost:8000/api/csv/summary | jq '.data_dir'
```

### 查看找到的文件数
```bash
curl http://localhost:8000/api/csv/summary | jq '.total_files'
```

### 查看找到的合约数
```bash
curl http://localhost:8000/api/csv/summary | jq '.total_contracts'
```

### 查看合约列表
```bash
curl http://localhost:8000/api/csv/contracts?underlying=BTC | jq '.contracts | length'
```

## 常见问题 (FAQ)

**Q: 为什么还是看不到数据？**
A: 
1. 确保 CSV 文件确实在 `data/downloads` 目录中
2. 检查文件名是否以 `.csv` 结尾
3. 检查 CSV 文件格式是否正确（需要有 `instrument_name`, `timestamp` 等列）
4. 查看 API 响应中的 `data_dir` 字段确认使用的目录

**Q: 如何同时支持多个目录？**
A: 目前 API 只使用第一个存在的目录。如果需要合并多个目录的数据，可以：
1. 把所有 CSV 文件复制到同一个目录
2. 或者修改 `get_csv_data_dir()` 函数支持多目录合并

**Q: 如何重置为原始路径？**
A: 删除 `data/downloads` 目录，API 会自动回退到其他路径

## 文件修改 (Files Modified)

- ✓ `backend/src/api/routes/csv_data.py` - 支持多个数据源目录

## 下一步 (Next Steps)

1. 把 CSV 文件放在 `data/downloads` 目录
2. 重启后端 API
3. 刷新前端应用
4. 在"CSV数据分析"中查看你的数据

---

**更新时间**: 2026年2月22日
**版本**: 1.1.0
