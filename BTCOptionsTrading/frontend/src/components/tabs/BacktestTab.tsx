import { useState, useEffect } from 'react'
import { strategiesApi } from '../../api/strategies'
import { backtestApi } from '../../api/backtest'
import { useAppStore } from '../../store/useAppStore'
import type { Strategy, BacktestResult, BacktestRequest, DailyPnL, Trade } from '../../api/types'
import LoadingSpinner from '../LoadingSpinner'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const BacktestTab = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([])
  const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null)
  const [dailyPnL, setDailyPnL] = useState<DailyPnL[]>([])
  const [trades, setTrades] = useState<Trade[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [showTradeDetails, setShowTradeDetails] = useState(false)
  const { setError, setSuccessMessage } = useAppStore()

  // 表单状态 - 使用历史日期
  const [formData, setFormData] = useState<BacktestRequest>({
    strategy_id: '',
    start_date: '2024-01-01',  // 历史日期
    end_date: '2024-03-31',    // 历史日期
    initial_capital: 100000,
    underlying_symbol: 'BTC'
  })

  // 加载策略列表
  const loadStrategies = async () => {
    try {
      const data = await strategiesApi.list()
      setStrategies(data)
    } catch (error) {
      console.error('加载策略失败:', error)
    }
  }

  // 加载回测结果列表
  const loadBacktestResults = async () => {
    try {
      setIsLoading(true)
      const data = await backtestApi.listResults(undefined, 20)
      setBacktestResults(data)
      if (data.length > 0 && !selectedResult) {
        setSelectedResult(data[0])
        loadDailyPnL(data[0].id)
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : '加载回测结果失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 加载每日盈亏数据和交易记录
  const loadDailyPnL = async (resultId: string) => {
    try {
      const [pnlData, tradesData] = await Promise.all([
        backtestApi.getDailyPnL(resultId),
        backtestApi.getTrades(resultId)
      ])
      setDailyPnL(pnlData)
      setTrades(tradesData)
    } catch (error) {
      console.error('加载数据失败:', error)
    }
  }

  useEffect(() => {
    loadStrategies()
    loadBacktestResults()
  }, [])

  // 运行回测
  const handleRunBacktest = async () => {
    if (!formData.strategy_id) {
      setError('请选择策略')
      return
    }

    try {
      setIsRunning(true)
      // 转换日期格式为ISO datetime字符串
      const requestData = {
        ...formData,
        start_date: `${formData.start_date}T00:00:00`,
        end_date: `${formData.end_date}T23:59:59`
      }
      const result = await backtestApi.run(requestData)
      setSuccessMessage('回测完成！')
      loadBacktestResults()
      setSelectedResult(result)
      loadDailyPnL(result.id)
    } catch (error) {
      setError(error instanceof Error ? error.message : '回测失败')
    } finally {
      setIsRunning(false)
    }
  }

  // 选择回测结果
  const handleSelectResult = (result: BacktestResult) => {
    setSelectedResult(result)
    loadDailyPnL(result.id)
  }

  // 格式化日期
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  }

  // 格式化百分比
  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`
  }

  // 格式化金额
  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  // 准备图表数据
  const chartData = dailyPnL.map(item => ({
    date: formatDate(item.date),
    value: parseFloat(item.portfolio_value.toString()),
    pnl: parseFloat(item.cumulative_pnl.toString())
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">回测分析</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 回测参数 */}
        <div className="card lg:col-span-1">
          <h3 className="text-lg font-semibold mb-4 text-text-primary">回测参数</h3>
          
          {/* 提示信息 */}
          <div className="mb-4 p-3 bg-accent-blue bg-opacity-10 border border-accent-blue border-opacity-30 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-accent-blue flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm text-accent-blue font-medium">回测说明</p>
                <p className="text-xs text-text-secondary mt-1">
                  回测使用历史数据模拟策略表现。请选择过去的日期范围进行回测分析。
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-text-secondary mb-2">选择策略</label>
              <select 
                className="select w-full"
                value={formData.strategy_id}
                onChange={(e) => setFormData({ ...formData, strategy_id: e.target.value })}
                disabled={isRunning}
              >
                <option value="">请选择策略</option>
                {strategies.map(strategy => (
                  <option key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-text-secondary mb-2">初始资金</label>
              <input 
                type="number" 
                className="input w-full" 
                value={formData.initial_capital}
                onChange={(e) => setFormData({ ...formData, initial_capital: parseFloat(e.target.value) })}
                disabled={isRunning}
              />
            </div>
            <div>
              <label className="block text-sm text-text-secondary mb-2">开始日期</label>
              <input 
                type="date" 
                className="input w-full"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                max={new Date().toISOString().split('T')[0]}
                disabled={isRunning}
              />
              <p className="text-xs text-text-disabled mt-1">选择历史日期</p>
            </div>
            <div>
              <label className="block text-sm text-text-secondary mb-2">结束日期</label>
              <input 
                type="date" 
                className="input w-full"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                max={new Date().toISOString().split('T')[0]}
                disabled={isRunning}
              />
              <p className="text-xs text-text-disabled mt-1">不能晚于今天</p>
            </div>
            <button 
              className="btn btn-primary w-full"
              onClick={handleRunBacktest}
              disabled={isRunning || !formData.strategy_id}
            >
              {isRunning ? (
                <span className="flex items-center justify-center">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">运行中...</span>
                </span>
              ) : (
                '运行回测'
              )}
            </button>
          </div>
        </div>

        {/* 绩效指标 */}
        <div className="card lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4 text-text-primary">绩效指标</h3>
          {selectedResult ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">总收益率</p>
                <p className={`text-2xl font-bold ${selectedResult.total_return >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                  {selectedResult.total_return >= 0 ? '+' : ''}{formatPercent(selectedResult.total_return)}
                </p>
              </div>
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">夏普比率</p>
                <p className="text-2xl font-bold text-text-primary">
                  {selectedResult.sharpe_ratio?.toFixed(2) || 'N/A'}
                </p>
              </div>
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">最大回撤</p>
                <p className="text-2xl font-bold text-accent-red">
                  {selectedResult.max_drawdown ? formatPercent(selectedResult.max_drawdown) : 'N/A'}
                </p>
              </div>
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">胜率</p>
                <p className="text-2xl font-bold text-text-primary">
                  {selectedResult.win_rate ? formatPercent(selectedResult.win_rate) : 'N/A'}
                </p>
              </div>
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">初始资金</p>
                <p className="text-lg font-bold text-text-primary">
                  {formatCurrency(parseFloat(selectedResult.initial_capital.toString()))}
                </p>
              </div>
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">最终资金</p>
                <p className="text-lg font-bold text-text-primary">
                  {formatCurrency(parseFloat(selectedResult.final_capital.toString()))}
                </p>
              </div>
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">交易次数</p>
                <p className="text-lg font-bold text-accent-blue cursor-pointer hover:text-accent-blue-light"
                   onClick={() => setShowTradeDetails(!showTradeDetails)}
                   title="点击查看交易明细">
                  {selectedResult.total_trades} 次
                  <span className="text-xs ml-1">📋</span>
                </p>
              </div>
              <div className="bg-bg-secondary p-4 rounded">
                <p className="text-text-secondary text-sm">回测周期</p>
                <p className="text-sm font-bold text-text-primary">
                  {formatDate(selectedResult.start_date)} - {formatDate(selectedResult.end_date)}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-text-secondary">
              请运行回测或选择历史回测结果
            </div>
          )}
        </div>
      </div>

      {/* 交易明细 */}
      {selectedResult && showTradeDetails && trades.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-text-primary">
              交易明细 ({trades.length} 笔交易)
            </h3>
            <button
              onClick={() => setShowTradeDetails(false)}
              className="text-text-secondary hover:text-text-primary"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-text-disabled">
                  <th className="text-left py-3 px-4 text-text-secondary text-sm font-medium">时间</th>
                  <th className="text-left py-3 px-4 text-text-secondary text-sm font-medium">操作</th>
                  <th className="text-left py-3 px-4 text-text-secondary text-sm font-medium">合约</th>
                  <th className="text-right py-3 px-4 text-text-secondary text-sm font-medium">数量</th>
                  <th className="text-right py-3 px-4 text-text-secondary text-sm font-medium">价格</th>
                  <th className="text-right py-3 px-4 text-text-secondary text-sm font-medium">盈亏</th>
                  <th className="text-right py-3 px-4 text-text-secondary text-sm font-medium">组合价值</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, index) => (
                  <tr key={index} className="border-b border-text-disabled hover:bg-bg-secondary transition-colors">
                    <td className="py-3 px-4 text-text-primary text-sm">
                      {new Date(trade.timestamp).toLocaleString('zh-CN')}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        trade.action === 'buy' 
                          ? 'bg-accent-green bg-opacity-20 text-accent-green' 
                          : 'bg-accent-red bg-opacity-20 text-accent-red'
                      }`}>
                        {trade.action === 'buy' ? '买入' : '卖出'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-text-primary text-sm font-mono">
                      {trade.instrument_name}
                    </td>
                    <td className="py-3 px-4 text-right text-text-primary text-sm">
                      {trade.quantity}
                    </td>
                    <td className="py-3 px-4 text-right text-text-primary text-sm font-mono">
                      {trade.price ? formatCurrency(trade.price) : '-'}
                    </td>
                    <td className="py-3 px-4 text-right text-sm font-mono">
                      {trade.pnl !== null && trade.pnl !== undefined ? (
                        <span className={trade.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                          {trade.pnl >= 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                        </span>
                      ) : (
                        <span className="text-text-disabled">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right text-text-primary text-sm font-mono">
                      {trade.portfolio_value ? formatCurrency(trade.portfolio_value) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* 交易统计 */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-text-disabled">
            <div>
              <p className="text-text-secondary text-xs">买入次数</p>
              <p className="text-text-primary font-bold">
                {trades.filter(t => t.action === 'buy').length} 次
              </p>
            </div>
            <div>
              <p className="text-text-secondary text-xs">卖出次数</p>
              <p className="text-text-primary font-bold">
                {trades.filter(t => t.action === 'sell').length} 次
              </p>
            </div>
            <div>
              <p className="text-text-secondary text-xs">总盈利交易</p>
              <p className="text-accent-green font-bold">
                {trades.filter(t => t.pnl && t.pnl > 0).length} 次
              </p>
            </div>
            <div>
              <p className="text-text-secondary text-xs">总亏损交易</p>
              <p className="text-accent-red font-bold">
                {trades.filter(t => t.pnl && t.pnl < 0).length} 次
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 盈亏曲线图表 */}
      {selectedResult && chartData.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-text-primary">盈亏曲线</h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
              <XAxis 
                dataKey="date" 
                stroke="#848E9C"
                tick={{ fill: '#848E9C' }}
              />
              <YAxis 
                stroke="#848E9C"
                tick={{ fill: '#848E9C' }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E2329', 
                  border: '1px solid #474D57',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#EAECEF' }}
                itemStyle={{ color: '#EAECEF' }}
                formatter={(value: number) => formatCurrency(value)}
              />
              <Legend 
                wrapperStyle={{ color: '#EAECEF' }}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3861FB" 
                strokeWidth={2}
                name="组合价值"
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="pnl" 
                stroke="#0ECB81" 
                strokeWidth={2}
                name="累计盈亏"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 期权价格变化图表 */}
      {selectedResult && trades.length > 0 && (() => {
        // 从交易记录中提取期权价格数据
        const optionPriceData = trades
          .filter(t => t.price && t.price > 0)
          .map(t => ({
            timestamp: new Date(t.timestamp).getTime(),
            date: new Date(t.timestamp).toLocaleString('zh-CN', { 
              month: '2-digit', 
              day: '2-digit', 
              hour: '2-digit', 
              minute: '2-digit' 
            }),
            instrument: t.instrument_name,
            price: t.price,
            action: t.action
          }))
          .sort((a, b) => a.timestamp - b.timestamp)

        // 按合约分组
        const instrumentGroups = new Map<string, typeof optionPriceData>()
        optionPriceData.forEach(item => {
          if (!instrumentGroups.has(item.instrument)) {
            instrumentGroups.set(item.instrument, [])
          }
          instrumentGroups.get(item.instrument)!.push(item)
        })

        // 为每个合约分配颜色
        const colors = ['#3861FB', '#0ECB81', '#F6465D', '#FCD535', '#B7BDC6']
        const instruments = Array.from(instrumentGroups.keys())

        // 合并所有时间点的数据
        const timePoints = new Map<number, any>()
        optionPriceData.forEach(item => {
          if (!timePoints.has(item.timestamp)) {
            timePoints.set(item.timestamp, { 
              timestamp: item.timestamp,
              date: item.date 
            })
          }
          const point = timePoints.get(item.timestamp)!
          point[item.instrument] = item.price
          point[`${item.instrument}_action`] = item.action
        })

        const priceChartData = Array.from(timePoints.values()).sort((a, b) => a.timestamp - b.timestamp)

        return priceChartData.length > 0 ? (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">期权价格变化</h3>
              <div className="text-sm text-text-secondary">
                显示回测期间各期权合约的价格变化
              </div>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={priceChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                <XAxis 
                  dataKey="date" 
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C', fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C' }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1E2329', 
                    border: '1px solid #474D57',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#EAECEF' }}
                  itemStyle={{ color: '#EAECEF' }}
                  formatter={(value: number, name: string) => {
                    if (name.includes('_action')) return null
                    return [`$${value.toFixed(2)}`, name]
                  }}
                />
                <Legend 
                  wrapperStyle={{ color: '#EAECEF' }}
                  formatter={(value) => {
                    // 简化合约名称显示
                    const parts = value.split('-')
                    if (parts.length >= 4) {
                      return `${parts[2]} ${parts[3]}`
                    }
                    return value
                  }}
                />
                {instruments.map((instrument, index) => (
                  <Line 
                    key={instrument}
                    type="monotone" 
                    dataKey={instrument}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    name={instrument}
                    dot={{ r: 4 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
            
            {/* 图例说明 */}
            <div className="mt-4 p-3 bg-bg-secondary rounded-lg">
              <p className="text-sm text-text-secondary mb-2">图表说明：</p>
              <ul className="text-xs text-text-secondary space-y-1">
                <li>• 每个点代表一次交易时的期权价格</li>
                <li>• 不同颜色的线代表不同的期权合约</li>
                <li>• 可以看到期权价格随时间的变化趋势</li>
              </ul>
            </div>
          </div>
        ) : null
      })()}

      {/* 历史回测结果列表 */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-text-primary">历史回测结果</h3>
        {isLoading ? (
          <LoadingSpinner />
        ) : backtestResults.length === 0 ? (
          <div className="text-center py-8 text-text-secondary">
            还没有回测结果
          </div>
        ) : (
          <div className="space-y-2">
            {backtestResults.map((result) => (
              <div
                key={result.id}
                className={`p-4 rounded cursor-pointer transition-all ${
                  selectedResult?.id === result.id
                    ? 'bg-accent-blue bg-opacity-20 border border-accent-blue'
                    : 'bg-bg-secondary hover:bg-opacity-80'
                }`}
                onClick={() => handleSelectResult(result)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4">
                      <span className="text-text-primary font-medium">
                        策略ID: {result.strategy_id.substring(0, 8)}...
                      </span>
                      <span className={`font-bold ${result.total_return >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {result.total_return >= 0 ? '+' : ''}{formatPercent(result.total_return)}
                      </span>
                      <span className="text-text-secondary text-sm">
                        {formatDate(result.start_date)} - {formatDate(result.end_date)}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-text-secondary">
                      <span>夏普: {result.sharpe_ratio?.toFixed(2) || 'N/A'}</span>
                      <span>回撤: {result.max_drawdown ? formatPercent(result.max_drawdown) : 'N/A'}</span>
                      <span>胜率: {result.win_rate ? formatPercent(result.win_rate) : 'N/A'}</span>
                      <span>交易: {result.total_trades}次</span>
                    </div>
                  </div>
                  <div className="text-text-disabled text-xs">
                    {formatDate(result.created_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default BacktestTab
