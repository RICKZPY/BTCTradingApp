# Implementation Plan: Backtest Data Selector

## Overview

本实施计划将回测数据选择器功能分解为一系列增量式的开发任务。实施将从后端 API 开始，然后构建前端组件，最后进行集成和测试。每个任务都建立在前面任务的基础上，确保代码始终处于可工作状态。

技术栈：
- 后端：Python + FastAPI
- 前端：React + TypeScript
- 测试：pytest (后端), Jest + React Testing Library (前端), Hypothesis (后端 PBT), fast-check (前端 PBT)

## Tasks

- [x] 1. 后端 API 基础设施搭建
  - 创建 `/backend/src/api/routes/backtest_data.py` 路由文件
  - 定义所有 Pydantic 数据模型（DateRange, Instrument, 各种 Response 模型）
  - 设置路由器并注册到主应用
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 2. 实现可用日期和合约查询端点
  - [ ] 2.1 实现 GET /api/backtest/available-dates 端点
    - 调用 HistoricalDataManager.get_available_dates()
    - 计算最早和最晚日期
    - 返回 AvailableDatesResponse
    - _Requirements: 8.1, 1.1_
  
  - [ ]* 2.2 编写 available-dates 端点的单元测试
    - 测试成功响应格式
    - 测试空数据情况
    - 测试错误处理
    - _Requirements: 8.1_
  
  - [ ] 2.3 实现 GET /api/backtest/available-instruments 端点
    - 调用 HistoricalDataManager.get_available_instruments()
    - 支持可选的日期范围过滤参数
    - 返回 AvailableInstrumentsResponse
    - _Requirements: 8.2, 1.2, 4.4_
  
  - [ ]* 2.4 编写 available-instruments 端点的单元测试
    - 测试无过滤参数的情况
    - 测试带日期范围过滤的情况
    - 测试参数验证
    - _Requirements: 8.2_

- [ ] 3. 实现数据覆盖率统计端点
  - [ ] 3.1 实现 GET /api/backtest/coverage-stats 端点
    - 验证日期范围参数（开始日期 <= 结束日期）
    - 调用 HistoricalDataManager.get_coverage_stats()
    - 返回 CoverageStatsResponse
    - _Requirements: 8.3, 2.1_
  
  - [ ]* 3.2 编写 coverage-stats 端点的单元测试
    - 测试有效日期范围
    - 测试无效日期范围（返回 400）
    - 测试无数据情况
    - _Requirements: 8.3_
  
  - [ ]* 3.3 编写日期范围验证的属性测试
    - **Property: API 参数验证**
    - **Validates: Requirements 8.3**
    - 使用 Hypothesis 生成随机日期对
    - 验证 start_date <= end_date 时返回 200/404
    - 验证 start_date > end_date 时返回 400

- [ ] 4. 实现数据准备和预览端点
  - [ ] 4.1 实现 POST /api/backtest/prepare-data 端点
    - 验证请求参数（日期范围、合约列表非空）
    - 调用 HistoricalDataManager.get_data_for_backtest()
    - 生成数据集 ID（UUID）
    - 返回 PrepareDataResponse
    - _Requirements: 8.4, 5.2_
  
  - [ ] 4.2 实现 GET /api/backtest/preview-data 端点
    - 验证请求参数
    - 调用 HistoricalDataManager.get_data_for_backtest()
    - 限制返回记录数（默认 10 条）
    - 返回 PreviewDataResponse
    - _Requirements: 8.5, 6.2_
  
  - [ ]* 4.3 编写数据准备和预览端点的单元测试
    - 测试有效请求
    - 测试参数验证
    - 测试空合约列表（返回 400）
    - 测试无数据情况
    - _Requirements: 8.4, 8.5_

- [ ] 5. 后端错误处理和验证增强
  - [ ] 5.1 实现统一错误响应格式
    - 创建 ErrorResponse 模型
    - 实现全局异常处理器
    - 为所有端点添加错误处理
    - _Requirements: 所有后端需求_
  
  - [ ] 5.2 添加资源限制验证
    - 限制单次请求最多 100 个合约
    - 限制日期范围最多 1 年
    - 返回清晰的错误消息
    - _Requirements: 8.3, 8.4, 8.5_

- [ ] 6. Checkpoint - 后端 API 完成
  - 确保所有后端测试通过，询问用户是否有问题

- [ ] 7. 前端状态管理和类型定义
  - 创建 `/frontend/src/types/backtest.ts` 定义所有 TypeScript 接口
  - 定义 BacktestDataState 接口
  - 定义所有 API 响应类型
  - 定义组件 Props 接口
  - _Requirements: 所有前端需求_

- [ ] 8. 前端 API 客户端实现
  - [ ] 8.1 创建 `/frontend/src/api/backtestData.ts` API 客户端
    - 实现 fetchAvailableDates()
    - 实现 fetchAvailableInstruments()
    - 实现 fetchCoverageStats()
    - 实现 prepareBacktestData()
    - 实现 previewBacktestData()
    - 添加错误处理和类型安全
    - _Requirements: 1.1, 1.2, 2.1, 5.2, 6.2_
  
  - [ ] 8.2 实现请求缓存机制
    - 使用 Map 缓存 API 响应
    - 实现缓存键生成逻辑
    - 添加缓存过期机制（可选）
    - _Requirements: 10.5_
  
  - [ ]* 8.3 编写 API 客户端的属性测试
    - **Property 24: 缓存效果验证**
    - **Validates: Requirements 10.5**
    - 验证相同参数的第二次请求使用缓存

- [ ] 9. 实现 DateRangeSelector 组件
  - [ ] 9.1 创建基础 DateRangeSelector 组件
    - 创建 `/frontend/src/components/backtest/DateRangeSelector.tsx`
    - 实现日历视图（使用 react-datepicker 或类似库）
    - 实现日期范围选择逻辑
    - 添加预设选项（7天、30天、90天）
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  
  - [ ] 9.2 实现日期高亮和验证
    - 高亮可用日期
    - 限制结束日期选择范围
    - 自动调整无效日期范围
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 9.3 编写 DateRangeSelector 的单元测试
    - 测试预设选项点击
    - 测试日期选择交互
    - 测试无效范围处理
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ]* 9.4 编写日期范围相关的属性测试
    - **Property 5: 日历高亮正确性**
    - **Validates: Requirements 3.1**
    - **Property 6: 结束日期范围限制**
    - **Validates: Requirements 3.2**
    - **Property 8: 预设日期范围计算正确性**
    - **Validates: Requirements 3.5**

- [ ] 10. 实现 InstrumentSelector 组件
  - [ ] 10.1 创建基础 InstrumentSelector 组件
    - 创建 `/frontend/src/components/backtest/InstrumentSelector.tsx`
    - 显示合约列表
    - 实现多选功能（使用复选框）
    - 显示选择数量
    - _Requirements: 4.1, 4.2, 4.3, 4.5_
  
  - [ ] 10.2 实现搜索和过滤功能
    - 添加搜索输入框
    - 实现搜索逻辑（按合约名称、类型过滤）
    - 实现防抖（300ms）
    - 根据日期范围过滤合约
    - _Requirements: 4.4, 4.5, 10.3, 10.4_
  
  - [ ]* 10.3 编写 InstrumentSelector 的单元测试
    - 测试合约列表渲染
    - 测试选择交互
    - 测试搜索功能
    - 测试日期范围过滤
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 10.4 编写合约选择相关的属性测试
    - **Property 9: 合约信息完整性**
    - **Validates: Requirements 4.1**
    - **Property 10: 选择数量一致性**
    - **Validates: Requirements 4.3**
    - **Property 11: 日期范围过滤合约**
    - **Validates: Requirements 4.4**
    - **Property 23: 防抖效果验证**
    - **Validates: Requirements 10.4**

- [ ] 11. 实现 DataQualityDisplay 组件
  - [ ] 11.1 创建 DataQualityDisplay 组件
    - 创建 `/frontend/src/components/backtest/DataQualityDisplay.tsx`
    - 显示覆盖率百分比（使用进度条）
    - 显示总数据点和缺失数据点
    - 显示低覆盖率警告（< 90%）
    - 显示加载状态
    - _Requirements: 2.2, 2.3, 2.4_
  
  - [ ]* 11.2 编写 DataQualityDisplay 的单元测试
    - 测试数据显示
    - 测试警告显示条件
    - 测试加载状态
    - _Requirements: 2.2, 2.3, 2.4_
  
  - [ ]* 11.3 编写数据质量显示的属性测试
    - **Property 4: 覆盖率统计完整显示**
    - **Validates: Requirements 2.2, 2.3**

- [ ] 12. 实现 DataPreviewModal 组件
  - [ ] 12.1 创建 DataPreviewModal 组件
    - 创建 `/frontend/src/components/backtest/DataPreviewModal.tsx`
    - 实现模态框布局
    - 显示数据样本表格（时间戳、合约、价格、成交量）
    - 显示总记录数
    - 添加关闭按钮
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 12.2 编写 DataPreviewModal 的单元测试
    - 测试模态框打开/关闭
    - 测试数据显示
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 12.3 编写数据预览相关的属性测试
    - **Property 14: 预览数据字段完整性**
    - **Validates: Requirements 6.3**
    - **Property 15: 预览总数显示正确性**
    - **Validates: Requirements 6.5**

- [ ] 13. 实现 ConfigurationManager 功能
  - [ ] 13.1 创建配置管理工具函数
    - 创建 `/frontend/src/utils/configStorage.ts`
    - 实现 saveConfiguration() - 保存到 localStorage
    - 实现 loadConfigurations() - 从 localStorage 加载
    - 实现 deleteConfiguration() - 从 localStorage 删除
    - 添加错误处理（配额超限、访问被禁用）
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 13.2 编写配置管理的单元测试
    - 测试保存配置
    - 测试加载配置
    - 测试删除配置
    - 测试 localStorage 错误处理
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 13.3 编写配置管理的属性测试
    - **Property 16: 配置保存加载往返**
    - **Validates: Requirements 7.2, 7.4**
    - **Property 17: 配置删除一致性**
    - **Validates: Requirements 7.5**

- [ ] 14. 实现主 BacktestDataSelector 组件
  - [ ] 14.1 创建 BacktestDataSelector 主组件
    - 创建 `/frontend/src/components/backtest/BacktestDataSelector.tsx`
    - 设置状态管理（使用 useState 或 useReducer）
    - 组合所有子组件
    - 实现组件挂载时的数据加载
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ] 14.2 实现数据流和交互逻辑
    - 日期范围变更时触发覆盖率查询
    - 日期范围变更时过滤合约列表
    - 实现"开始回测"按钮启用逻辑
    - 实现"预览数据"功能
    - 实现配置保存/加载 UI
    - _Requirements: 2.1, 4.4, 5.1, 6.1, 7.1, 7.3_
  
  - [ ] 14.3 实现错误处理和加载状态
    - 处理所有 API 调用错误
    - 显示加载指示器
    - 提供重试选项
    - _Requirements: 1.5, 5.4, 5.5_
  
  - [ ]* 14.4 编写 BacktestDataSelector 的单元测试
    - 测试组件初始化
    - 测试数据加载流程
    - 测试用户交互
    - 测试错误处理
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 5.1, 5.4, 5.5_
  
  - [ ]* 14.5 编写主组件的属性测试
    - **Property 1: 日期范围显示正确性**
    - **Validates: Requirements 1.3**
    - **Property 2: 合约数量显示一致性**
    - **Validates: Requirements 1.4**
    - **Property 3: 日期范围变更触发覆盖率查询**
    - **Validates: Requirements 2.1**
    - **Property 12: 按钮启用条件**
    - **Validates: Requirements 5.1**
    - **Property 13: 回测参数传递正确性**
    - **Validates: Requirements 5.2**

- [ ] 15. Checkpoint - 核心功能完成
  - 确保所有核心功能测试通过，询问用户是否有问题

- [ ] 16. 实现响应式设计
  - [ ] 16.1 添加响应式样式
    - 使用 CSS Grid/Flexbox 实现响应式布局
    - 桌面设备：多列布局
    - 移动设备：单列布局，折叠次要信息
    - 确保触摸目标至少 44x44 像素
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [ ] 16.2 实现布局调整时的状态保持
    - 使用 useEffect 监听窗口大小变化
    - 确保状态不丢失
    - _Requirements: 9.4_
  
  - [ ]* 16.3 编写响应式设计的属性测试
    - **Property 18: 触摸目标尺寸要求**
    - **Validates: Requirements 9.3**
    - **Property 19: 布局调整状态保持**
    - **Validates: Requirements 9.4**

- [ ] 17. 性能优化
  - [ ] 17.1 实现防抖和节流
    - 为搜索输入添加防抖（300ms）
    - 为覆盖率查询添加防抖（300ms）
    - _Requirements: 10.2, 10.3, 10.4_
  
  - [ ] 17.2 优化渲染性能
    - 使用 React.memo 优化子组件
    - 使用 useMemo 缓存计算结果
    - 使用 useCallback 缓存回调函数
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ]* 17.3 编写性能测试
    - **Property 20: 初始加载性能**
    - **Validates: Requirements 10.1**
    - **Property 21: 覆盖率查询性能**
    - **Validates: Requirements 10.2**
    - **Property 22: 搜索响应性能**
    - **Validates: Requirements 10.3**
    - 使用 React DevTools Profiler 测量渲染时间

- [ ] 18. 集成到现有应用
  - [ ] 18.1 将 BacktestDataSelector 集成到回测页面
    - 找到现有的回测配置界面
    - 替换或增强现有的日期/合约选择逻辑
    - 连接到现有的 BacktestEngine
    - _Requirements: 5.3_
  
  - [ ] 18.2 更新路由和导航
    - 确保回测页面路由正确
    - 更新导航菜单（如需要）
    - _Requirements: 所有需求_

- [ ] 19. 端到端测试
  - [ ]* 19.1 编写端到端测试
    - 使用 Playwright 或 Cypress
    - 测试完整的用户流程：
      1. 打开回测配置界面
      2. 查看可用数据
      3. 选择日期范围
      4. 选择合约
      5. 查看数据质量
      6. 预览数据
      7. 保存配置
      8. 开始回测
    - _Requirements: 所有需求_

- [ ] 20. 最终 Checkpoint - 完整功能验证
  - 运行所有测试（单元测试、属性测试、端到端测试）
  - 手动测试所有功能
  - 验证性能指标
  - 询问用户进行最终验收测试

## Notes

- 标记 `*` 的任务为可选测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号以确保可追溯性
- Checkpoint 任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证特定示例和边界情况
- 建议按顺序执行任务，因为后续任务依赖前面的任务
