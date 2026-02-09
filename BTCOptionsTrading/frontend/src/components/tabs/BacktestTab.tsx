import { useState, useEffect } from 'react'
import { strategiesApi } from '../../api/strategies'
import { backtestApi } from '../../api/backtest'
import { useAppStore } from '../../store/useAppStore'
import type { Strategy, BacktestResult, BacktestRequest, DailyPnL } from '../../api/types'
import LoadingSpinner from '../LoadingSpinner'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const BacktestTab = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([])
  const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null)
  const [dailyPnL, setDailyPnL] = useState<DailyPnL[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const { setError, setSuccessMessage } = useAppStore()

  // 表单状态
  const [formData, setFormData] = useState<BacktestRequest>({
    strategy_id: '',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
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

  // 加载每日盈亏数据
  const loadDailyPnL = async (resultId: string) => {
    try {
      const data = await backtestApi.getDailyPnL(resultId)
      setDailyPnL(data)
    } catch (error) {
      console.error('加载盈亏数据失败:', error)
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
                disabled={isRunning}
              />
            </div>
            <div>
              <label className="block text-sm text-text-secondary mb-2">结束日期</label>
              <input 
                type="date" 
                className="input w-full"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                disabled={isRunning}
              />
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
                <p className="text-lg font-bold text-text-primary">
                  {selectedResult.total_trades}
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
