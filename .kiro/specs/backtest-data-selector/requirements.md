# Requirements Document

## Introduction

本文档定义了回测数据选择器功能的需求。该功能旨在改进用户在配置回测时的数据选择体验，通过展示可用的历史数据信息、提供数据质量指标，以及简化回测配置流程，让用户能够基于真实的历史数据进行回测分析。

## Glossary

- **Backtest_Data_Selector**: 回测数据选择器，用于展示和选择历史数据的用户界面组件
- **Historical_Data_Manager**: 历史数据管理器，后端服务类，负责管理和提供历史数据
- **Backtest_Engine**: 回测引擎，执行回测计算的核心组件
- **Data_Coverage**: 数据覆盖率，表示特定时间段内数据的完整性百分比
- **Instrument**: 交易合约，如 BTC 期权合约
- **Date_Range**: 日期范围，包含开始日期和结束日期的时间区间
- **Data_Quality_Metrics**: 数据质量指标，包括覆盖率、缺失数据点、数据完整性等统计信息

## Requirements

### Requirement 1: 展示可用历史数据信息

**User Story:** 作为交易员，我想要在回测界面看到系统中可用的历史数据信息，以便我了解可以使用哪些数据进行回测。

#### Acceptance Criteria

1. WHEN 用户打开回测配置界面，THE Backtest_Data_Selector SHALL 调用 Historical_Data_Manager.get_available_dates() 获取可用日期列表
2. WHEN 用户打开回测配置界面，THE Backtest_Data_Selector SHALL 调用 Historical_Data_Manager.get_available_instruments() 获取可用合约列表
3. WHEN 可用数据信息加载完成，THE Backtest_Data_Selector SHALL 显示最早可用日期和最晚可用日期
4. WHEN 可用数据信息加载完成，THE Backtest_Data_Selector SHALL 显示可用合约的数量和列表
5. WHEN 数据加载失败，THE Backtest_Data_Selector SHALL 显示错误消息并提供重试选项

### Requirement 2: 提供数据质量指标

**User Story:** 作为交易员，我想要了解历史数据的质量和完整性，以便我评估回测结果的可靠性。

#### Acceptance Criteria

1. WHEN 用户选择一个日期范围，THE Backtest_Data_Selector SHALL 调用 Historical_Data_Manager.get_coverage_stats() 获取该范围的数据覆盖率统计
2. WHEN 数据覆盖率统计返回，THE Backtest_Data_Selector SHALL 显示数据覆盖率百分比
3. WHEN 数据覆盖率统计返回，THE Backtest_Data_Selector SHALL 显示缺失数据点的数量
4. WHEN 数据覆盖率低于 90%，THE Backtest_Data_Selector SHALL 显示警告提示用户数据可能不完整
5. WHEN 用户选择的日期范围内没有数据，THE Backtest_Data_Selector SHALL 阻止用户继续配置回测并显示提示信息

### Requirement 3: 简化日期选择流程

**User Story:** 作为交易员，我想要轻松选择有数据的日期范围，而不需要手动猜测哪些日期有数据。

#### Acceptance Criteria

1. WHEN 用户点击日期选择器，THE Backtest_Data_Selector SHALL 在日历视图中高亮显示有数据的日期
2. WHEN 用户选择开始日期，THE Backtest_Data_Selector SHALL 自动限制结束日期只能选择开始日期之后且有数据的日期
3. WHEN 用户选择的日期范围包含无数据的日期，THE Backtest_Data_Selector SHALL 自动调整范围到最近的有数据日期
4. THE Backtest_Data_Selector SHALL 提供快速选择预设日期范围的选项（如"最近 7 天"、"最近 30 天"、"最近 90 天"）
5. WHEN 用户选择预设日期范围，THE Backtest_Data_Selector SHALL 自动填充对应的开始和结束日期

### Requirement 4: 合约选择功能

**User Story:** 作为交易员，我想要选择特定的合约进行回测，以便我针对性地分析特定合约的策略表现。

#### Acceptance Criteria

1. WHEN 用户查看合约列表，THE Backtest_Data_Selector SHALL 显示每个合约的基本信息（合约名称、到期日、类型）
2. WHEN 用户选择合约，THE Backtest_Data_Selector SHALL 允许单选或多选合约
3. WHEN 用户选择多个合约，THE Backtest_Data_Selector SHALL 显示已选择的合约数量
4. WHEN 用户选择合约后更改日期范围，THE Backtest_Data_Selector SHALL 过滤掉在该日期范围内没有数据的合约
5. THE Backtest_Data_Selector SHALL 提供搜索和过滤功能，让用户快速找到目标合约

### Requirement 5: 回测数据集配置

**User Story:** 作为交易员，我想要基于选择的参数生成回测数据集，以便我使用真实数据进行回测。

#### Acceptance Criteria

1. WHEN 用户完成日期范围和合约选择，THE Backtest_Data_Selector SHALL 启用"开始回测"按钮
2. WHEN 用户点击"开始回测"按钮，THE Backtest_Data_Selector SHALL 调用 Historical_Data_Manager.get_data_for_backtest() 并传递选择的参数
3. WHEN 数据集生成成功，THE Backtest_Data_Selector SHALL 将数据集传递给 Backtest_Engine
4. WHEN 数据集生成失败，THE Backtest_Data_Selector SHALL 显示错误信息并保持在配置界面
5. WHEN 数据集生成中，THE Backtest_Data_Selector SHALL 显示加载进度指示器

### Requirement 6: 数据预览功能

**User Story:** 作为交易员，我想要在开始回测前预览选择的数据，以便我确认数据符合预期。

#### Acceptance Criteria

1. WHEN 用户完成日期范围和合约选择，THE Backtest_Data_Selector SHALL 提供"预览数据"选项
2. WHEN 用户点击"预览数据"，THE Backtest_Data_Selector SHALL 显示数据样本（前 10 条记录）
3. WHEN 显示数据预览，THE Backtest_Data_Selector SHALL 展示关键字段（时间戳、合约、价格、成交量）
4. WHEN 数据预览显示，THE Backtest_Data_Selector SHALL 提供关闭预览并返回配置界面的选项
5. THE Backtest_Data_Selector SHALL 在预览界面显示数据集的总记录数

### Requirement 7: 配置保存和加载

**User Story:** 作为交易员，我想要保存常用的回测配置，以便我快速重复使用相同的数据选择设置。

#### Acceptance Criteria

1. WHEN 用户完成回测配置，THE Backtest_Data_Selector SHALL 提供"保存配置"选项
2. WHEN 用户保存配置，THE Backtest_Data_Selector SHALL 将配置存储到本地存储（包括日期范围、选择的合约、预设名称）
3. WHEN 用户打开回测配置界面，THE Backtest_Data_Selector SHALL 显示已保存的配置列表
4. WHEN 用户选择已保存的配置，THE Backtest_Data_Selector SHALL 自动填充对应的日期范围和合约选择
5. WHEN 用户删除已保存的配置，THE Backtest_Data_Selector SHALL 从本地存储中移除该配置

### Requirement 8: API 端点实现

**User Story:** 作为系统，我需要提供 API 端点来支持前端的数据查询需求，以便前端能够获取历史数据信息。

#### Acceptance Criteria

1. THE 系统 SHALL 提供 GET /api/backtest/available-dates 端点返回可用日期列表
2. THE 系统 SHALL 提供 GET /api/backtest/available-instruments 端点返回可用合约列表
3. THE 系统 SHALL 提供 GET /api/backtest/coverage-stats 端点接受日期范围参数并返回数据覆盖率统计
4. THE 系统 SHALL 提供 POST /api/backtest/prepare-data 端点接受配置参数并返回回测数据集标识符
5. THE 系统 SHALL 提供 GET /api/backtest/preview-data 端点接受配置参数并返回数据样本

### Requirement 9: 响应式设计

**User Story:** 作为用户，我想要在不同设备上使用回测数据选择器，以便我可以在移动设备或桌面设备上配置回测。

#### Acceptance Criteria

1. WHEN 界面在桌面设备上显示，THE Backtest_Data_Selector SHALL 使用多列布局展示数据信息
2. WHEN 界面在移动设备上显示，THE Backtest_Data_Selector SHALL 使用单列布局并折叠次要信息
3. WHEN 用户在小屏幕设备上操作，THE Backtest_Data_Selector SHALL 确保所有交互元素的触摸目标至少为 44x44 像素
4. WHEN 界面尺寸改变，THE Backtest_Data_Selector SHALL 自动调整布局而不丢失用户输入
5. THE Backtest_Data_Selector SHALL 在所有支持的屏幕尺寸上保持可读性和可用性

### Requirement 10: 性能优化

**User Story:** 作为用户，我想要快速加载和交互的回测配置界面，以便我高效地完成回测设置。

#### Acceptance Criteria

1. WHEN 用户打开回测配置界面，THE Backtest_Data_Selector SHALL 在 2 秒内完成初始数据加载
2. WHEN 用户更改日期范围，THE Backtest_Data_Selector SHALL 在 500 毫秒内更新数据覆盖率统计
3. WHEN 用户搜索合约，THE Backtest_Data_Selector SHALL 在 200 毫秒内显示搜索结果
4. THE Backtest_Data_Selector SHALL 使用防抖技术避免频繁的 API 调用
5. THE Backtest_Data_Selector SHALL 缓存已加载的数据以减少重复请求
