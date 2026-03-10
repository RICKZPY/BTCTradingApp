# Bugfix Requirements Document

## Introduction

当前的情绪交易服务（sentiment_trading_service.py）采用持续运行的Python进程模式，每分钟检查一次时间，在每天早上5点执行交易。这种实现方式在资源有限的服务器环境（2核vCPU）下会造成不必要的资源消耗。服务需要24小时保持Python进程运行和WebSocket连接，但实际上每天只执行一次交易操作。

本次修复将把持续运行的服务模式改为按需执行的cron job模式，大幅降低服务器资源占用，同时保持相同的功能。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN sentiment trading服务运行时 THEN 系统需要24小时保持Python进程运行

1.2 WHEN sentiment trading服务运行时 THEN 系统需要持续维护WebSocket连接到Deribit

1.3 WHEN sentiment trading服务运行时 THEN 系统每分钟执行一次时间检查循环，即使不在交易时间

1.4 WHEN 在2核vCPU的有限资源服务器上运行时 THEN 持续运行的Python进程占用宝贵的CPU和内存资源

1.5 WHEN 服务需要重启或维护时 THEN 需要手动管理进程的启动和停止

### Expected Behavior (Correct)

2.1 WHEN 到达每天早上5点时 THEN 系统SHALL通过cron job触发Python脚本执行一次性任务

2.2 WHEN Python脚本被cron触发时 THEN 系统SHALL建立临时连接到Deribit，执行交易后断开连接

2.3 WHEN 不在交易时间时 THEN 系统SHALL不运行任何Python进程，不占用服务器资源

2.4 WHEN 在2核vCPU的有限资源服务器上运行时 THEN 系统SHALL仅在需要时短暂占用资源（每天约几分钟）

2.5 WHEN 需要调度任务时 THEN 系统SHALL使用操作系统的cron机制自动管理任务执行

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 每天早上5点执行交易时 THEN 系统SHALL CONTINUE TO获取情绪数据并分析

3.2 WHEN 执行情绪策略时 THEN 系统SHALL CONTINUE TO根据情绪分析结果选择正确的交易策略（看涨/看跌/中性）

3.3 WHEN 执行交易时 THEN 系统SHALL CONTINUE TO使用相同的期权选择逻辑和下单参数

3.4 WHEN 交易完成后 THEN 系统SHALL CONTINUE TO记录交易历史到JSON文件

3.5 WHEN 发生错误时 THEN 系统SHALL CONTINUE TO记录详细的错误日志

3.6 WHEN 使用主网和测试网配置时 THEN 系统SHALL CONTINUE TO支持从主网获取数据、在测试网执行交易的混合模式

3.7 WHEN 查询持仓和订单时 THEN 系统SHALL CONTINUE TO返回相同格式的数据

3.8 WHEN 没有合适的期权可交易时 THEN 系统SHALL CONTINUE TO跳过交易并记录原因
