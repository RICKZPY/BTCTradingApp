# 需求文档 - 策略管理页面增强

## 简介

策略管理是BTC期权交易回测系统的核心功能。当前实现存在可用性问题，包括历史策略无法编辑、配置选项有限、缺乏用户指引以及未与实时市场数据联动。本需求旨在全面提升策略管理页面的用户体验和功能完整性。

## 术语表

- **Strategy_Manager**: 策略管理系统，负责创建、编辑、删除和查看策略
- **Options_Chain**: 期权链，包含特定到期日的所有期权合约及其市场数据
- **Real_Time_Data**: 实时市场数据，从Deribit API获取的当前期权价格和希腊字母
- **Strategy_Template**: 策略模板，预定义的期权策略类型（如跨式、宽跨式、铁鹰等）
- **Strategy_Leg**: 策略腿，组成多腿策略的单个期权合约
- **Greeks**: 希腊字母，包括Delta、Gamma、Theta、Vega、Rho等风险指标
- **ATM**: 平值期权（At-The-Money），执行价接近标的资产当前价格的期权
- **Strike_Price**: 执行价，期权合约的行权价格
- **Expiry_Date**: 到期日，期权合约的到期日期
- **Market_Data_Integration**: 市场数据集成，将实时期权链数据集成到策略创建流程中

## 需求

### 需求 1: 策略编辑功能

**用户故事:** 作为交易员，我想要编辑已创建的策略，以便调整策略参数而无需重新创建。

#### 验收标准

1. WHEN 用户点击策略卡片 THEN THE Strategy_Manager SHALL 显示策略详情模态框
2. WHEN 用户在详情模态框中点击"编辑"按钮 THEN THE Strategy_Manager SHALL 打开编辑表单并预填充当前策略数据
3. WHEN 用户修改策略参数并保存 THEN THE Strategy_Manager SHALL 更新数据库中的策略记录
4. WHEN 策略更新成功 THEN THE Strategy_Manager SHALL 刷新策略列表并显示成功消息
5. WHEN 用户取消编辑 THEN THE Strategy_Manager SHALL 关闭编辑表单而不保存更改

### 需求 2: 策略详情查看

**用户故事:** 作为交易员，我想要查看策略的完整详情，包括所有腿的配置和预期收益风险。

#### 验收标准

1. WHEN 用户点击策略卡片 THEN THE Strategy_Manager SHALL 显示包含所有策略信息的详情模态框
2. THE Strategy_Manager SHALL 在详情中显示策略名称、描述、类型和创建时间
3. THE Strategy_Manager SHALL 在详情中显示每个策略腿的合约信息（期权类型、执行价、到期日、买卖方向、数量）
4. THE Strategy_Manager SHALL 在详情中显示策略的最大收益、最大损失和盈亏平衡点
5. THE Strategy_Manager SHALL 在详情中提供"编辑"和"删除"操作按钮

### 需求 3: 实时市场数据集成

**用户故事:** 作为交易员，我想要在创建策略时看到实时的期权价格和希腊字母，以便做出更明智的决策。

#### 验收标准

1. WHEN 用户选择到期日 THEN THE Strategy_Manager SHALL 从Deribit API获取该到期日的期权链数据
2. WHEN 用户选择执行价 THEN THE Strategy_Manager SHALL 显示该执行价对应的实时期权价格
3. THE Strategy_Manager SHALL 在策略创建表单中显示选中期权的当前价格、隐含波动率和Delta
4. WHEN 市场数据加载失败 THEN THE Strategy_Manager SHALL 显示错误消息并允许用户手动输入价格
5. THE Strategy_Manager SHALL 每30秒自动刷新市场数据（当表单打开时）

### 需求 4: 智能执行价选择器

**用户故事:** 作为交易员，我想要从实时期权链中选择执行价，而不是手动输入数字。

#### 验收标准

1. WHEN 用户点击执行价输入框 THEN THE Strategy_Manager SHALL 显示期权链选择器下拉菜单
2. THE Strategy_Manager SHALL 在选择器中显示所有可用的执行价及其对应的期权价格
3. THE Strategy_Manager SHALL 高亮显示平值期权（ATM）
4. WHEN 用户选择执行价 THEN THE Strategy_Manager SHALL 自动填充执行价并显示该期权的市场数据
5. THE Strategy_Manager SHALL 在选择器中显示每个执行价的看涨和看跌期权价格

### 需求 5: 策略创建向导

**用户故事:** 作为新用户，我想要有一个分步向导来创建策略，以便理解每个参数的含义。

#### 验收标准

1. WHEN 用户点击"创建新策略"按钮 THEN THE Strategy_Manager SHALL 显示策略创建向导的第一步
2. THE Strategy_Manager SHALL 将策略创建分为3步：选择模板、配置参数、确认创建
3. WHEN 用户在每一步完成输入 THEN THE Strategy_Manager SHALL 验证输入并允许进入下一步
4. THE Strategy_Manager SHALL 在每个输入字段旁显示帮助提示图标
5. WHEN 用户点击帮助图标 THEN THE Strategy_Manager SHALL 显示该参数的详细说明和示例

### 需求 6: 策略模板增强

**用户故事:** 作为交易员，我想要看到每个策略模板的详细说明和适用场景，以便选择合适的策略。

#### 验收标准

1. THE Strategy_Manager SHALL 为每个策略模板显示详细描述、适用市场条件和风险收益特征
2. THE Strategy_Manager SHALL 为每个策略模板显示收益曲线图示
3. WHEN 用户悬停在策略模板卡片上 THEN THE Strategy_Manager SHALL 显示该策略的关键特点
4. THE Strategy_Manager SHALL 为每个策略模板提供"了解更多"链接到详细文档
5. THE Strategy_Manager SHALL 根据当前市场条件推荐合适的策略模板

### 需求 7: 策略验证和风险提示

**用户故事:** 作为交易员，我想要在创建策略前看到风险提示，以便避免不合理的配置。

#### 验收标准

1. WHEN 用户配置策略参数 THEN THE Strategy_Manager SHALL 实时验证参数的合理性
2. WHEN 策略的最大损失超过初始资金的50% THEN THE Strategy_Manager SHALL 显示高风险警告
3. WHEN 执行价配置不合理（如宽跨式的看涨执行价低于看跌执行价） THEN THE Strategy_Manager SHALL 显示错误提示
4. THE Strategy_Manager SHALL 在创建前显示策略的预期最大收益、最大损失和盈亏比
5. WHEN 用户确认创建高风险策略 THEN THE Strategy_Manager SHALL 要求用户二次确认

### 需求 8: 策略复制功能

**用户故事:** 作为交易员，我想要复制现有策略并修改参数，以便快速创建相似策略。

#### 验收标准

1. WHEN 用户在策略详情中点击"复制"按钮 THEN THE Strategy_Manager SHALL 打开创建表单并预填充原策略的所有参数
2. THE Strategy_Manager SHALL 在复制的策略名称后添加"(副本)"后缀
3. WHEN 用户修改参数并保存 THEN THE Strategy_Manager SHALL 创建新策略而不影响原策略
4. THE Strategy_Manager SHALL 在策略列表中显示复制关系（如"基于XXX策略"）
5. WHEN 用户复制策略 THEN THE Strategy_Manager SHALL 保留原策略的所有腿配置

### 需求 9: 策略搜索和筛选

**用户故事:** 作为交易员，我想要搜索和筛选策略列表，以便快速找到特定策略。

#### 验收标准

1. THE Strategy_Manager SHALL 在策略列表上方提供搜索框
2. WHEN 用户输入搜索关键词 THEN THE Strategy_Manager SHALL 实时过滤策略列表（按名称和描述）
3. THE Strategy_Manager SHALL 提供按策略类型筛选的下拉菜单
4. THE Strategy_Manager SHALL 提供按创建时间排序的选项（最新/最旧）
5. THE Strategy_Manager SHALL 提供按收益/损失排序的选项

### 需求 10: 批量操作

**用户故事:** 作为交易员，我想要批量删除或导出策略，以便高效管理大量策略。

#### 验收标准

1. THE Strategy_Manager SHALL 在策略列表中提供多选复选框
2. WHEN 用户选中多个策略 THEN THE Strategy_Manager SHALL 显示批量操作工具栏
3. THE Strategy_Manager SHALL 在批量操作工具栏中提供"删除"和"导出"按钮
4. WHEN 用户点击批量删除 THEN THE Strategy_Manager SHALL 要求确认并删除所有选中的策略
5. WHEN 用户点击批量导出 THEN THE Strategy_Manager SHALL 将选中策略导出为JSON文件

### 需求 11: 策略导入导出

**用户故事:** 作为交易员，我想要导出和导入策略配置，以便在不同环境间共享策略。

#### 验收标准

1. WHEN 用户在策略详情中点击"导出"按钮 THEN THE Strategy_Manager SHALL 将策略配置导出为JSON文件
2. THE Strategy_Manager SHALL 在策略列表页面提供"导入策略"按钮
3. WHEN 用户选择JSON文件导入 THEN THE Strategy_Manager SHALL 验证文件格式并创建策略
4. WHEN 导入的策略名称已存在 THEN THE Strategy_Manager SHALL 自动添加数字后缀避免冲突
5. THE Strategy_Manager SHALL 在导入后显示成功导入的策略数量

### 需求 12: 实时价格更新

**用户故事:** 作为交易员，我想要在策略列表中看到基于当前市场价格的实时盈亏，以便监控策略表现。

#### 验收标准

1. THE Strategy_Manager SHALL 在策略卡片上显示当前市场价值
2. THE Strategy_Manager SHALL 在策略卡片上显示未实现盈亏（基于当前市场价格）
3. WHEN 市场价格更新 THEN THE Strategy_Manager SHALL 通过WebSocket自动更新策略的市场价值
4. THE Strategy_Manager SHALL 用颜色标识盈利（绿色）和亏损（红色）
5. WHEN 用户打开策略详情 THEN THE Strategy_Manager SHALL 显示每个腿的当前市场价格和盈亏

### 需求 13: 快速创建常用策略

**用户故事:** 作为交易员，我想要快速创建常用策略（如ATM跨式），以便节省时间。

#### 验收标准

1. THE Strategy_Manager SHALL 在策略模板区域提供"快速创建"按钮
2. WHEN 用户点击"快速创建ATM跨式" THEN THE Strategy_Manager SHALL 自动选择最接近当前价格的执行价
3. WHEN 用户点击"快速创建ATM宽跨式" THEN THE Strategy_Manager SHALL 自动选择合理的看涨和看跌执行价
4. THE Strategy_Manager SHALL 使用默认的到期日（最近的周五）
5. WHEN 快速创建完成 THEN THE Strategy_Manager SHALL 显示确认对话框供用户调整参数

### 需求 14: 策略性能指标

**用户故事:** 作为交易员，我想要看到策略的关键性能指标，以便评估策略质量。

#### 验收标准

1. THE Strategy_Manager SHALL 在策略详情中显示策略的总Delta、Gamma、Theta、Vega
2. THE Strategy_Manager SHALL 在策略详情中显示盈亏平衡点
3. THE Strategy_Manager SHALL 在策略详情中显示最大收益和最大损失
4. THE Strategy_Manager SHALL 在策略详情中显示收益风险比
5. THE Strategy_Manager SHALL 在策略详情中显示策略的初始成本

### 需求 15: 移动端响应式设计

**用户故事:** 作为移动端用户，我想要在手机上也能方便地管理策略，以便随时随地操作。

#### 验收标准

1. THE Strategy_Manager SHALL 在移动设备上使用响应式布局
2. WHEN 屏幕宽度小于768px THEN THE Strategy_Manager SHALL 将策略卡片改为单列显示
3. THE Strategy_Manager SHALL 在移动端优化表单输入体验（使用原生选择器）
4. THE Strategy_Manager SHALL 在移动端简化策略详情显示（使用折叠面板）
5. THE Strategy_Manager SHALL 在移动端提供滑动手势删除策略

## 非功能需求

### 性能需求

1. THE Strategy_Manager SHALL 在2秒内加载策略列表（100个策略以内）
2. THE Strategy_Manager SHALL 在1秒内完成策略创建操作
3. THE Strategy_Manager SHALL 在500毫秒内响应搜索和筛选操作
4. THE Strategy_Manager SHALL 在3秒内从Deribit API获取期权链数据

### 可用性需求

1. THE Strategy_Manager SHALL 为所有交互元素提供清晰的视觉反馈
2. THE Strategy_Manager SHALL 为所有错误情况提供友好的错误消息
3. THE Strategy_Manager SHALL 为关键操作提供撤销功能
4. THE Strategy_Manager SHALL 遵循无障碍设计标准（WCAG 2.1 AA级）

### 可靠性需求

1. WHEN Deribit API不可用 THEN THE Strategy_Manager SHALL 降级使用模拟数据
2. THE Strategy_Manager SHALL 在网络错误时自动重试（最多3次）
3. THE Strategy_Manager SHALL 在本地缓存期权链数据（5分钟有效期）
4. THE Strategy_Manager SHALL 在操作失败时保留用户输入的数据
