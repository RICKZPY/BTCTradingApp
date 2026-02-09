import { useState, useEffect } from 'react'
import { dataApi } from '../../api/data'
import { useAppStore } from '../../store/useAppStore'
import LoadingSpinner from '../LoadingSpinner'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'

interface VolatilityData {
  strike: number
  expiry: string
  impliedVol: number
  moneyness: number
}

const VolatilityTab = () => {
  const [currency, setCurrency] = useState<'BTC' | 'ETH'>('BTC')
  const [isLoading, setIsLoading] = useState(false)
  const [volatilityData, setVolatilityData] = useState<VolatilityData[]>([])
  const [selectedExpiry, setSelectedExpiry] = useState<string>('')
  const [historicalVol, setHistoricalVol] = useState<number>(0)
  const [impliedVol, setImpliedVol] = useState<number>(0)
  const { setError } = useAppStore()

  // 生成模拟波动率数据
  const generateVolatilityData = () => {
    const strikes = [40000, 42000, 44000, 46000, 48000, 50000, 52000, 54000, 56000, 58000, 60000]
    const expiries = ['2024-03-29', '2024-06-28', '2024-09-27', '2024-12-27']
    const currentPrice = 50000
    
    const data: VolatilityData[] = []
    
    expiries.forEach(expiry => {
      strikes.forEach(strike => {
        const moneyness = strike / currentPrice
        // 模拟波动率微笑：ATM波动率最低，两端较高
        const baseVol = 0.6
        const smileEffect = Math.abs(moneyness - 1) * 0.5
        const timeEffect = (new Date(expiry).getTime() - Date.now()) / (365 * 24 * 60 * 60 * 1000) * 0.1
        const impliedVol = baseVol + smileEffect + timeEffect + (Math.random() - 0.5) * 0.1
        
        data.push({
          strike,
          expiry,
          impliedVol: Math.max(0.3, Math.min(1.2, impliedVol)),
          moneyness
        })
      })
    })
    
    return data
  }

  // 加载波动率数据
  const loadVolatilityData = async () => {
    try {
      setIsLoading(true)
      // 模拟数据加载
      const data = generateVolatilityData()
      setVolatilityData(data)
      
      // 设置默认到期日
      if (data.length > 0 && !selectedExpiry) {
        const expiries = [...new Set(data.map(d => d.expiry))]
        setSelectedExpiry(expiries[0])
      }
      
      // 模拟历史波动率和隐含波动率
      setHistoricalVol(0.65)
      setImpliedVol(0.72)
    } catch (error) {
      setError(error instanceof Error ? error.message : '加载波动率数据失败')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadVolatilityData()
  }, [currency])

  // 获取唯一的到期日列表
  const expiries = [...new Set(volatilityData.map(d => d.expiry))].sort()

  // 获取选中到期日的波动率微笑数据
  const volatilitySmileData = volatilityData
    .filter(d => d.expiry === selectedExpiry)
    .map(d => ({
      strike: d.strike,
      moneyness: d.moneyness,
      impliedVol: (d.impliedVol * 100).toFixed(2),
      impliedVolNum: d.impliedVol * 100
    }))
    .sort((a, b) => a.strike - b.strike)

  // 获取波动率期限结构数据（ATM波动率）
  const termStructureData = expiries.map(expiry => {
    const atmData = volatilityData.filter(d => d.expiry === expiry && Math.abs(d.moneyness - 1) < 0.05)
    const avgVol = atmData.reduce((sum, d) => sum + d.impliedVol, 0) / atmData.length
    return {
      expiry: new Date(expiry).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
      volatility: (avgVol * 100).toFixed(2),
      volatilityNum: avgVol * 100
    }
  })

  // 格式化百分比
  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`
  }

  // 计算波动率差异
  const volDifference = impliedVol - historicalVol
  const volDifferencePercent = (volDifference / historicalVol) * 100

  // 判断市场情绪
  const getMarketSentiment = () => {
    if (volDifferencePercent > 10) return { text: '恐慌', color: 'text-accent-red' }
    if (volDifferencePercent > 5) return { text: '谨慎', color: 'text-accent-yellow' }
    if (volDifferencePercent < -10) return { text: '乐观', color: 'text-accent-green' }
    if (volDifferencePercent < -5) return { text: '平静', color: 'text-accent-blue' }
    return { text: '中性', color: 'text-text-secondary' }
  }

  const sentiment = getMarketSentiment()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">波动率分析</h2>
        <div className="flex items-center gap-4">
          <select
            className="select"
            value={currency}
            onChange={(e) => setCurrency(e.target.value as 'BTC' | 'ETH')}
          >
            <option value="BTC">BTC</option>
            <option value="ETH">ETH</option>
          </select>
          <button
            className="btn btn-secondary"
            onClick={loadVolatilityData}
            disabled={isLoading}
          >
            {isLoading ? <LoadingSpinner size="sm" /> : '刷新数据'}
          </button>
        </div>
      </div>

      {/* 波动率概览 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-text-secondary text-sm mb-2">历史波动率 (30天)</p>
          <p className="text-3xl font-bold text-text-primary">
            {formatPercent(historicalVol * 100)}
          </p>
        </div>
        <div className="card">
          <p className="text-text-secondary text-sm mb-2">隐含波动率 (ATM)</p>
          <p className="text-3xl font-bold text-text-primary">
            {formatPercent(impliedVol * 100)}
          </p>
        </div>
        <div className="card">
          <p className="text-text-secondary text-sm mb-2">市场情绪</p>
          <p className={`text-3xl font-bold ${sentiment.color}`}>
            {sentiment.text}
          </p>
          <p className="text-text-secondary text-xs mt-1">
            IV - HV: {volDifference > 0 ? '+' : ''}{formatPercent(volDifference * 100)}
          </p>
        </div>
      </div>

      {/* 波动率对比说明 */}
      <div className="card bg-bg-secondary">
        <h3 className="text-sm font-semibold text-text-primary mb-2">波动率解读</h3>
        <div className="text-xs text-text-secondary space-y-1">
          <p>• <span className="text-accent-red">隐含波动率 {'>'} 历史波动率</span>: 市场预期未来波动加大，期权价格偏贵，适合卖出波动率策略</p>
          <p>• <span className="text-accent-green">隐含波动率 {'<'} 历史波动率</span>: 市场预期未来波动减小，期权价格偏便宜，适合买入波动率策略</p>
          <p>• <span className="text-accent-blue">隐含波动率 ≈ 历史波动率</span>: 市场预期与历史一致，期权定价合理</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          {/* 波动率微笑 */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">波动率微笑</h3>
              <select
                className="select"
                value={selectedExpiry}
                onChange={(e) => setSelectedExpiry(e.target.value)}
              >
                {expiries.map(expiry => (
                  <option key={expiry} value={expiry}>
                    {new Date(expiry).toLocaleDateString('zh-CN')}
                  </option>
                ))}
              </select>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={volatilitySmileData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                <XAxis
                  dataKey="strike"
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C' }}
                  label={{ value: '执行价', position: 'insideBottom', offset: -5, fill: '#848E9C' }}
                />
                <YAxis
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C' }}
                  label={{ value: '隐含波动率 (%)', angle: -90, position: 'insideLeft', fill: '#848E9C' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E2329',
                    border: '1px solid #474D57',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#EAECEF' }}
                  itemStyle={{ color: '#EAECEF' }}
                  formatter={(value: number) => `${value}%`}
                />
                <Legend wrapperStyle={{ color: '#EAECEF' }} />
                <Line
                  type="monotone"
                  dataKey="impliedVolNum"
                  stroke="#3861FB"
                  strokeWidth={2}
                  name="隐含波动率"
                  dot={{ fill: '#3861FB', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-xs text-text-secondary mt-2">
              波动率微笑显示不同执行价的隐含波动率。通常ATM期权波动率最低，深度实值和虚值期权波动率较高。
            </p>
          </div>

          {/* 波动率期限结构 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-text-primary">波动率期限结构</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={termStructureData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                <XAxis
                  dataKey="expiry"
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C' }}
                  label={{ value: '到期日', position: 'insideBottom', offset: -5, fill: '#848E9C' }}
                />
                <YAxis
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C' }}
                  label={{ value: 'ATM波动率 (%)', angle: -90, position: 'insideLeft', fill: '#848E9C' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E2329',
                    border: '1px solid #474D57',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#EAECEF' }}
                  itemStyle={{ color: '#EAECEF' }}
                  formatter={(value: number) => `${value}%`}
                />
                <Legend wrapperStyle={{ color: '#EAECEF' }} />
                <Line
                  type="monotone"
                  dataKey="volatilityNum"
                  stroke="#0ECB81"
                  strokeWidth={2}
                  name="ATM波动率"
                  dot={{ fill: '#0ECB81', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-xs text-text-secondary mt-2">
              期限结构显示不同到期日的ATM期权隐含波动率。正常情况下，远期波动率高于近期波动率。
            </p>
          </div>

          {/* 波动率散点图 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-text-primary">波动率分布</h3>
            <ResponsiveContainer width="100%" height={350}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                <XAxis
                  type="number"
                  dataKey="moneyness"
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C' }}
                  label={{ value: 'Moneyness (K/S)', position: 'insideBottom', offset: -5, fill: '#848E9C' }}
                  domain={[0.8, 1.2]}
                />
                <YAxis
                  type="number"
                  dataKey="impliedVol"
                  stroke="#848E9C"
                  tick={{ fill: '#848E9C' }}
                  label={{ value: '隐含波动率', angle: -90, position: 'insideLeft', fill: '#848E9C' }}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E2329',
                    border: '1px solid #474D57',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#EAECEF' }}
                  itemStyle={{ color: '#EAECEF' }}
                  formatter={(value: number) => `${(value * 100).toFixed(2)}%`}
                />
                <Legend wrapperStyle={{ color: '#EAECEF' }} />
                <Scatter
                  name="所有期权"
                  data={volatilityData}
                  fill="#3861FB"
                  fillOpacity={0.6}
                />
              </ScatterChart>
            </ResponsiveContainer>
            <p className="text-xs text-text-secondary mt-2">
              散点图显示所有期权的Moneyness与隐含波动率关系。Moneyness = 执行价/现价，1.0表示ATM。
            </p>
          </div>
        </>
      )}
    </div>
  )
}

export default VolatilityTab
