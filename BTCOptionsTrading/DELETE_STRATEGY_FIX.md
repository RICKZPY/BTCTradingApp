# 删除策略功能修复

## 问题描述

用户尝试删除策略时出现 "network issue" 错误。

## 问题分析

经过排查发现两个问题：

### 1. 后端服务器未运行
- 后端API服务器没有启动
- 导致前端无法连接到API
- 表现为 "network issue" 错误

### 2. 数据库外键约束错误
当后端服务器启动后，删除操作触发了数据库错误：
```
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) 
NOT NULL constraint failed: backtest_results.strategy_id
```

**原因**：
- 策略有关联的回测结果
- 删除策略时，SQLAlchemy尝试将 `backtest_results.strategy_id` 设置为 NULL
- 但该字段有 NOT NULL 约束，导致删除失败

## 解决方案

### 1. 启动后端服务器

```bash
cd BTCOptionsTrading/backend
python run_api.py
```

服务器将在 http://localhost:8000 运行

### 2. 修复删除逻辑

修改 `src/storage/dao.py` 中的 `StrategyDAO.delete()` 方法：

**修改前**：
```python
@staticmethod
def delete(db: Session, strategy_id: UUID) -> bool:
    """删除策略"""
    db_strategy = StrategyDAO.get_by_id(db, strategy_id)
    if db_strategy:
        db.delete(db_strategy)
        db.commit()
        return True
    return False
```

**修改后**：
```python
@staticmethod
def delete(db: Session, strategy_id: UUID) -> bool:
    """删除策略及其关联的回测结果和策略腿"""
    db_strategy = StrategyDAO.get_by_id(db, strategy_id)
    if db_strategy:
        # 先删除关联的回测结果
        db.query(BacktestResultModel).filter(
            BacktestResultModel.strategy_id == str(strategy_id)
        ).delete()
        
        # 删除关联的策略腿
        db.query(StrategyLegModel).filter(
            StrategyLegModel.strategy_id == str(strategy_id)
        ).delete()
        
        # 最后删除策略本身
        db.delete(db_strategy)
        db.commit()
        return True
    return False
```

## 修复说明

新的删除逻辑按以下顺序操作：

1. **删除回测结果**：先删除所有关联的回测结果
2. **删除策略腿**：删除策略的所有腿
3. **删除策略**：最后删除策略本身

这样可以避免外键约束错误，确保级联删除正确执行。

## 测试验证

### 测试删除功能

```bash
# 1. 获取策略列表
curl -X GET http://localhost:8000/api/strategies/

# 2. 删除一个策略（替换为实际的策略ID）
curl -X DELETE http://localhost:8000/api/strategies/{strategy_id}

# 3. 验证删除成功
# 应该返回: {"message":"Strategy deleted successfully"}

# 4. 再次获取策略列表，确认策略已被删除
curl -X GET http://localhost:8000/api/strategies/
```

### 测试结果

```bash
# 删除前
$ curl -X GET http://localhost:8000/api/strategies/ | python -m json.tool
[
    {
        "id": "479db974-affd-4d50-bd36-19e452ee652f",
        "name": "Test",
        ...
    },
    ...
]

# 执行删除
$ curl -X DELETE http://localhost:8000/api/strategies/479db974-affd-4d50-bd36-19e452ee652f
{"message":"Strategy deleted successfully"}

# 删除后（该策略不再出现在列表中）
$ curl -X GET http://localhost:8000/api/strategies/ | python -m json.tool
[
    {
        "id": "2d4cefd8-0b6d-4a2c-9387-9092c1b2d228",
        "name": "strangle 策略",
        ...
    },
    ...
]
```

✓ 删除功能正常工作

## 前端使用

现在您可以在前端界面正常删除策略：

1. 进入"策略"标签页
2. 找到要删除的策略
3. 点击删除按钮（垃圾桶图标）
4. 确认删除
5. 策略将从列表中消失

## 注意事项

### 数据安全
- 删除策略会同时删除：
  - 策略本身
  - 所有策略腿
  - 所有关联的回测结果
- **删除操作不可恢复**，请谨慎操作

### 建议
1. 删除前确认策略不再需要
2. 如果有重要的回测结果，考虑先导出数据
3. 可以使用"复制"功能保留策略副本

## 相关文件

- `BTCOptionsTrading/backend/src/storage/dao.py` - 修复的删除逻辑
- `BTCOptionsTrading/backend/src/api/routes/strategies.py` - 删除API路由
- `BTCOptionsTrading/frontend/src/api/strategies.ts` - 前端API客户端

## 后续改进

可以考虑的改进：

1. **软删除**：添加 `deleted_at` 字段，标记删除而不是真正删除
2. **删除确认**：在后端添加额外的确认机制
3. **数据导出**：删除前自动导出策略和回测数据
4. **回收站**：实现回收站功能，允许恢复已删除的策略

## 故障排除

### 问题：仍然显示 "network issue"

**检查**：
1. 后端服务器是否正在运行
   ```bash
   curl http://localhost:8000/health
   ```
2. 端口8000是否被占用
   ```bash
   lsof -ti:8000
   ```
3. 前端API地址配置是否正确

**解决**：
- 重启后端服务器
- 检查防火墙设置
- 查看浏览器控制台错误信息

### 问题：删除失败，显示其他错误

**检查**：
1. 查看后端日志
   ```bash
   tail -f BTCOptionsTrading/backend/logs/app.log
   ```
2. 检查数据库文件权限
3. 确认策略ID正确

**解决**：
- 根据错误日志排查
- 检查数据库完整性
- 必要时重建数据库

## 总结

删除策略功能现已修复，可以正常使用。主要修复了：
1. ✓ 后端服务器启动
2. ✓ 数据库外键约束处理
3. ✓ 级联删除逻辑

现在可以安全地删除不需要的策略了！
