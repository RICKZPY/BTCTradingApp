# CSV 数据回退修复 - 合约分析标签页

## 问题
用户在"合约分析"标签页中看不到任何合约（显示 0 个可用合约）。

## 根本原因
"合约分析"标签页调用的是 `historicalApi.getAvailableInstruments()`，这个 API 从数据库读取数据。如果数据库中没有数据，就会返回空列表。

## 解决方案
实现了一个**回退机制**：
1. 首先尝试从数据库获取合约数据
2. 如果数据库中没有数据，自动回退到 CSV API
3. 用户无需切换标签页，直接在"合约分析"中看到 CSV 数据

## 修改内容

### 修改 1: `loadInstruments()` 函数
**文件**: `frontend/src/components/tabs/HistoricalDataTab.tsx`

**变更**:
- 当数据库返回 0 个合约时，自动尝试从 CSV API 获取
- 如果 CSV API 有数据，使用 CSV 数据填充合约列表
- 用户体验无缝切换

**代码逻辑**:
```typescript
// 如果数据库中没有数据，尝试从 CSV API 获取
if (instrumentList.length === 0) {
  console.info('数据库中没有合约，尝试从 CSV 数据获取...')
  try {
    const csvContracts = await csvApi.getContracts('BTC')
    const csvInstrumentList = csvContracts.map(c => c.instrument_name)
    setInstruments(csvInstrumentList)
    // ... 设置第一个合约为选中状态
    return
  } catch (csvErr) {
    console.error('从 CSV 获取合约失败:', csvErr)
  }
}
```

### 修改 2: `loadDatesForInstrument()` 函数
**文件**: `frontend/src/components/tabs/HistoricalDataTab.tsx`

**变更**:
- 当数据库中没有合约详情时，自动回退到 CSV API
- 将 CSV 数据格式转换为与数据库格式兼容的格式
- 用户看到的图表和数据格式保持一致

**代码逻辑**:
```typescript
// 首先尝试从数据库获取
try {
  const details = await historicalApi.getContractDetails(instrumentName)
  // ... 处理数据库数据
  return
} catch (dbErr) {
  console.info('数据库中没有合约详情，尝试从 CSV 获取...')
}

// 如果数据库中没有数据，尝试从 CSV 获取
try {
  const csvData = await csvApi.getContractData(instrumentName)
  // ... 转换格式并处理 CSV 数据
} catch (csvErr) {
  console.error('从 CSV 获取合约详情失败:', csvErr)
  setError('无法加载合约详情')
}
```

## 使用流程

### 步骤 1: 启动后端 API
```bash
cd BTCOptionsTrading/backend
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 2: 打开前端应用
- 访问 `http://localhost:3000`

### 步骤 3: 导航到历史数据分析
- 点击菜单中的"历史数据分析"

### 步骤 4: 点击"合约分析"标签页
```
[数据概览] [合约分析] ← 点击这里 [CSV数据分析] [数据质量]
```

### 步骤 5: 查看合约列表
- 下拉菜单现在会显示 1300 个合约（来自 CSV 数据）
- 选择一个合约
- 查看价格曲线、波动率、成交量等图表

## 工作流程

```
用户选择"合约分析"标签页
    ↓
调用 loadInstruments()
    ↓
尝试从数据库获取合约列表
    ↓
    ├─ 成功 → 显示数据库中的合约
    │
    └─ 失败或返回 0 个 → 尝试从 CSV API 获取
        ↓
        ├─ 成功 → 显示 CSV 中的 1300 个合约
        │
        └─ 失败 → 显示错误信息

用户选择一个合约
    ↓
调用 loadDatesForInstrument()
    ↓
尝试从数据库获取合约详情
    ↓
    ├─ 成功 → 显示数据库中的数据和图表
    │
    └─ 失败 → 尝试从 CSV API 获取
        ↓
        ├─ 成功 → 显示 CSV 中的数据和图表
        │
        └─ 失败 → 显示错误信息
```

## 优势

✅ **无缝体验** - 用户无需切换标签页
✅ **自动回退** - 系统自动选择可用的数据源
✅ **数据一致** - 无论来自数据库还是 CSV，格式和显示方式相同
✅ **错误处理** - 如果两个数据源都失败，显示清晰的错误信息

## 数据优先级

1. **数据库数据** - 如果数据库中有数据，优先使用
2. **CSV 数据** - 如果数据库中没有数据，回退到 CSV
3. **错误** - 如果两个数据源都失败，显示错误信息

## 验证

### 方法 1: 浏览器开发者工具
1. 打开浏览器开发者工具 (F12)
2. 切换到 **Console** 标签页
3. 查看日志输出：
   - 如果看到 "数据库中没有合约，尝试从 CSV 数据获取..." → 回退机制工作正常
   - 如果看到 "Found X instruments" → 从数据库获取成功

### 方法 2: 检查下拉菜单
- 打开"合约分析"标签页
- 点击下拉菜单
- 应该看到 1300 个合约

## 文件修改

- `frontend/src/components/tabs/HistoricalDataTab.tsx` - 修改了 `loadInstruments()` 和 `loadDatesForInstrument()` 函数

## 后续步骤

1. ✓ 在"合约分析"标签页中查看 CSV 数据
2. ✓ 选择不同的合约并分析价格曲线
3. ✓ 如果需要导入 CSV 数据到数据库，请联系开发团队

---

**最后更新**: 2026年2月23日
**状态**: ✅ 已完成
