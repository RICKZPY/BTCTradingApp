import { useState, useEffect } from 'react'
import { dataApi } from '../../api/data'
import LoadingSpinner from '../LoadingSpinner'

interface OptionChainData {
  strike: number
  call: {
    price: number
    iv: number
    delta: number
    gamma: number
    theta: number
    vega: number
    volume: number
    openInterest: number
  }
  put: {
    price: number
    iv: number
    delta: number
    gamma: number
    theta: number
    vega: number
    volume: number
    openInterest: number
  }
}

const OptionsChainTab = () => {
  const [currency, setCurrency] = useState<'BTC' | 'ETH'>('BTC')
  const [expiryDate, setExpiryDate] = useState<string>('')
  const [expiryDates, setExpiryDates] = useState<string[]>([])
  const [optionsData, setOptionsData] = useState<OptionChainData[]>([])
  const [underlyingPrice, setUnderlyingPrice] = useState<number>(0)
  const [isLoading, setIsLoading] = useState(false)
  const [showGreeks, setShowGreeks] = useState(false)

  // 生成到期日列表（未来3个月的每周五）
  const generateExpiryDates = () => {
    const dates: string[] = []
    const today = new Date()
    
    for (let i = 0; i < 12; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + (i * 7))
      // 找到下一个周五
      const dayOfWeek = date.getDay()
      const daysUntilFriday = (5 - dayOfWeek + 7) % 7
      date.setDate(date.getDate() + daysUntilFriday)
      
      dates.push(date.toISOString().split('T')[0])
    }
    
    setExpiryDates(dates)
    if (dates.length > 0) {
      setExpiryDate(dates[0])
    }
  }

  // 加载标的资产价格
  const loadUnderlyingPrice = async () => {
    try {
      const data = await dataApi.getUnderlyingPrice(currency)
      setUnderlyingPrice(data.price)
    } catch (error) {
      console.error('加载标的价格失败:', error)
      // 使用模拟数据
      setUnderlyingPrice(currency === 'BTC' ? 45000 : 2500)
    }
  }

  // 加载期权链数据
  const loadOptionsChain = async () => {
    if (!expiryDate) return

    try {
      setIsLoading(true)
      // 调用后端API获取期权链数据
      const rawData = await dataApi.getOptionsChain(currency)
      
      // 将后端返回的数据转换为前端格式
      const processedData = processOptionsChainData(rawData, expiryDate)
      
      // 检查数据是否有效（是否有定价数据）
      const hasValidPricing = processedData.some(option => 
        (option.call.price > 0 || option.put.price > 0)
      )
      
      if (processedData.length > 0 && hasValidPricing) {
        // 有数据且有定价，使用真实数据
        setOptionsData(processedData)
      } else {
        // 没有数据或没有定价，使用模拟数据
        console.log('No valid pricing data from API, using mock data')
        generateMockData()
      }
    } catch (error) {
      console.error('加载期权链失败:', error)
      // 使用模拟数据
      generateMockData()
    } finally {
      setIsLoading(false)
    }
  }

  // 处理后端返回的期权链数据
  const processOptionsChainData = (rawData: any[], targetExpiryDate: string): OptionChainData[] => {
    // 按执行价分组
    const strikeMap = new Map<number, { call?: any; put?: any }>()
    
    // 过滤指定到期日的期权
    const targetDate = new Date(targetExpiryDate).toISOString().split('T')[0]
    
    rawData.forEach((option: any) => {
      // 检查到期日是否匹配
      const optionDate = new Date(option.expiration_date || option.expiration_timestamp * 1000)
        .toISOString().split('T')[0]
      
      if (optionDate !== targetDate) return
      
      const strike = option.strike || option.strike_price
      if (!strike) return
      
      if (!strikeMap.has(strike)) {
        strikeMap.set(strike, {})
      }
      
      const strikeData = strikeMap.get(strike)!
      const optionData = {
        price: option.mark_price || option.last_price || option.current_price || 0,
        iv: option.implied_volatility || option.mark_iv || 0,
        delta: option.delta || (option.greeks && option.greeks.delta) || 0,
        gamma: option.gamma || (option.greeks && option.greeks.gamma) || 0,
        theta: option.theta || (option.greeks && option.greeks.theta) || 0,
        vega: option.vega || (option.greeks && option.greeks.vega) || 0,
        volume: option.volume || (option.stats && option.stats.volume) || 0,
        openInterest: option.open_interest || 0
      }
      
      if (option.option_type === 'call' || option.option_type === 'C') {
        strikeData.call = optionData
      } else if (option.option_type === 'put' || option.option_type === 'P') {
        strikeData.put = optionData
      }
    })
    
    // 转换为数组并排序
    const result: OptionChainData[] = []
    Array.from(strikeMap.entries())
      .sort((a, b) => a[0] - b[0])
      .forEach(([strike, data]) => {
        if (data.call && data.put) {
          result.push({
            strike,
            call: data.call,
            put: data.put
          })
        }
      })
    
    return result
  }

  // 生成模拟数据（使用Black-Scholes模型）
  const generateMockData = () => {
    const strikes: OptionChainData[] = []
    const basePrice = underlyingPrice || (currency === 'BTC' ? 45000 : 2500)
    const strikeInterval = currency === 'BTC' ? 1000 : 50
    
    // 计算到期时间（天数）
    const today = new Date()
    const expiry = new Date(expiryDate)
    const daysToExpiry = Math.max(1, Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)))
    const timeToExpiry = daysToExpiry / 365.0
    
    // 基础参数
    const riskFreeRate = 0.05
    const baseIV = 0.8 // 80% 基础隐含波动率
    
    // 简化的Black-Scholes计算
    const calculateCallPrice = (S: number, K: number, T: number, r: number, sigma: number) => {
      const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T))
      const d2 = d1 - sigma * Math.sqrt(T)
      const N_d1 = 0.5 * (1 + erf(d1 / Math.sqrt(2)))
      const N_d2 = 0.5 * (1 + erf(d2 / Math.sqrt(2)))
      return S * N_d1 - K * Math.exp(-r * T) * N_d2
    }
    
    const calculatePutPrice = (S: number, K: number, T: number, r: number, sigma: number) => {
      const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T))
      const d2 = d1 - sigma * Math.sqrt(T)
      const N_minus_d1 = 0.5 * (1 + erf(-d1 / Math.sqrt(2)))
      const N_minus_d2 = 0.5 * (1 + erf(-d2 / Math.sqrt(2)))
      return K * Math.exp(-r * T) * N_minus_d2 - S * N_minus_d1
    }
    
    // 误差函数近似
    const erf = (x: number) => {
      const sign = x >= 0 ? 1 : -1
      x = Math.abs(x)
      const a1 = 0.254829592
      const a2 = -0.284496736
      const a3 = 1.421413741
      const a4 = -1.453152027
      const a5 = 1.061405429
      const p = 0.3275911
      const t = 1.0 / (1.0 + p * x)
      const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x)
      return sign * y
    }
    
    // 计算Delta
    const calculateCallDelta = (S: number, K: number, T: number, r: number, sigma: number) => {
      const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T))
      return 0.5 * (1 + erf(d1 / Math.sqrt(2)))
    }
    
    const calculatePutDelta = (S: number, K: number, T: number, r: number, sigma: number) => {
      return calculateCallDelta(S, K, T, r, sigma) - 1
    }

    for (let i = -7; i <= 7; i++) {
      const strike = Math.round(basePrice + (i * strikeInterval))
      const moneyness = basePrice / strike
      
      // 波动率微笑：OTM期权波动率更高
      const ivAdjustment = Math.abs(moneyness - 1) * 0.3
      const callIV = baseIV + ivAdjustment + (Math.random() - 0.5) * 0.1
      const putIV = baseIV + ivAdjustment + (Math.random() - 0.5) * 0.1
      
      // 计算期权价格
      const callPrice = calculateCallPrice(basePrice, strike, timeToExpiry, riskFreeRate, callIV)
      const putPrice = calculatePutPrice(basePrice, strike, timeToExpiry, riskFreeRate, putIV)
      
      // 计算Delta
      const callDelta = calculateCallDelta(basePrice, strike, timeToExpiry, riskFreeRate, callIV)
      const putDelta = calculatePutDelta(basePrice, strike, timeToExpiry, riskFreeRate, putIV)
      
      // 计算Gamma（简化）
      const gamma = Math.exp(-0.5 * Math.pow((Math.log(moneyness) / (callIV * Math.sqrt(timeToExpiry))), 2)) / 
                    (basePrice * callIV * Math.sqrt(2 * Math.PI * timeToExpiry))
      
      // 计算Theta（简化，每日衰减）
      const callTheta = -callPrice * 0.01 / daysToExpiry
      const putTheta = -putPrice * 0.01 / daysToExpiry
      
      // 计算Vega（简化）
      const vega = basePrice * Math.sqrt(timeToExpiry) * gamma * 0.01
      
      strikes.push({
        strike,
        call: {
          price: Math.max(0, callPrice),
          iv: callIV,
          delta: callDelta,
          gamma: gamma,
          theta: callTheta,
          vega: vega,
          volume: Math.floor(Math.random() * 1000),
          openInterest: Math.floor(Math.random() * 5000)
        },
        put: {
          price: Math.max(0, putPrice),
          iv: putIV,
          delta: putDelta,
          gamma: gamma,
          theta: putTheta,
          vega: vega,
          volume: Math.floor(Math.random() * 1000),
          openInterest: Math.floor(Math.random() * 5000)
        }
      })
    }

    setOptionsData(strikes)
  }

  useEffect(() => {
    generateExpiryDates()
  }, [])

  useEffect(() => {
    loadUnderlyingPrice()
  }, [currency])

  useEffect(() => {
    if (expiryDate && underlyingPrice) {
      loadOptionsChain()
    }
  }, [expiryDate, underlyingPrice])

  // 格式化价格
  const formatPrice = (price: number) => {
    return price.toFixed(2)
  }

  // 格式化百分比
  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  // 格式化希腊字母
  const formatGreek = (value: number) => {
    return value.toFixed(4)
  }

  // 判断是否接近ATM
  const isNearATM = (strike: number) => {
    const diff = Math.abs(strike - underlyingPrice)
    const threshold = currency === 'BTC' ? 1000 : 50
    return diff < threshold
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">期权链</h2>
        <div className="flex items-center space-x-4">
          <div>
            <label className="text-sm text-text-secondary mr-2">标的资产:</label>
            <select 
              className="select"
              value={currency}
              onChange={(e) => setCurrency(e.target.value as 'BTC' | 'ETH')}
            >
              <option value="BTC">BTC</option>
              <option value="ETH">ETH</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-text-secondary mr-2">到期日:</label>
            <select 
              className="select"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
            >
              {expiryDates.map(date => (
                <option key={date} value={date}>
                  {new Date(date).toLocaleDateString('zh-CN')}
                </option>
              ))}
            </select>
          </div>
          <button 
            className="btn btn-secondary"
            onClick={loadOptionsChain}
            disabled={isLoading}
          >
            {isLoading ? <LoadingSpinner size="sm" /> : '刷新数据'}
          </button>
        </div>
      </div>

      {/* 标的价格显示 */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-text-secondary">当前价格:</span>
            <span className="text-2xl font-bold text-text-primary ml-3 font-mono">
              ${(underlyingPrice || 0).toLocaleString()}
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showGreeks}
                onChange={(e) => setShowGreeks(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-text-secondary text-sm">显示希腊字母</span>
            </label>
          </div>
        </div>
      </div>

      {/* 期权链表格 */}
      <div className="card">
        {isLoading ? (
          <div className="py-8">
            <LoadingSpinner />
          </div>
        ) : optionsData.length === 0 ? (
          <div className="text-center py-8 text-text-secondary">
            暂无数据
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-text-disabled">
                  <th colSpan={showGreeks ? 5 : 3} className="text-center py-3 px-4 text-accent-green text-sm font-medium">
                    看涨期权 (Call)
                  </th>
                  <th className="text-center py-3 px-4 text-text-primary text-sm font-medium">
                    执行价
                  </th>
                  <th colSpan={showGreeks ? 5 : 3} className="text-center py-3 px-4 text-accent-red text-sm font-medium">
                    看跌期权 (Put)
                  </th>
                </tr>
                <tr className="border-b border-text-disabled">
                  {/* Call 列 */}
                  <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">价格</th>
                  <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">IV</th>
                  <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">Delta</th>
                  {showGreeks && (
                    <>
                      <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">Gamma</th>
                      <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">Vega</th>
                    </>
                  )}
                  
                  {/* Strike */}
                  <th className="text-center py-2 px-4 text-text-secondary text-xs font-medium">Strike</th>
                  
                  {/* Put 列 */}
                  <th className="text-left py-2 px-3 text-text-secondary text-xs font-medium">Delta</th>
                  <th className="text-left py-2 px-3 text-text-secondary text-xs font-medium">IV</th>
                  <th className="text-left py-2 px-3 text-text-secondary text-xs font-medium">价格</th>
                  {showGreeks && (
                    <>
                      <th className="text-left py-2 px-3 text-text-secondary text-xs font-medium">Gamma</th>
                      <th className="text-left py-2 px-3 text-text-secondary text-xs font-medium">Vega</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {optionsData.map((option, index) => {
                  const isATM = isNearATM(option.strike)
                  return (
                    <tr 
                      key={index}
                      className={`border-b border-text-disabled hover:bg-bg-secondary transition-colors ${
                        isATM ? 'bg-accent-blue bg-opacity-5' : ''
                      }`}
                    >
                      {/* Call 数据 */}
                      <td className="py-2 px-3 font-mono text-right text-accent-green text-sm">
                        ${formatPrice(option.call.price)}
                      </td>
                      <td className="py-2 px-3 font-mono text-right text-sm">
                        {formatPercent(option.call.iv)}
                      </td>
                      <td className="py-2 px-3 font-mono text-right text-sm">
                        {formatGreek(option.call.delta)}
                      </td>
                      {showGreeks && (
                        <>
                          <td className="py-2 px-3 font-mono text-right text-sm">
                            {formatGreek(option.call.gamma)}
                          </td>
                          <td className="py-2 px-3 font-mono text-right text-sm">
                            {formatGreek(option.call.vega)}
                          </td>
                        </>
                      )}
                      
                      {/* Strike */}
                      <td className={`py-2 px-4 font-mono text-center font-bold ${
                        isATM ? 'text-accent-blue' : 'text-text-primary'
                      }`}>
                        ${option.strike.toLocaleString()}
                      </td>
                      
                      {/* Put 数据 */}
                      <td className="py-2 px-3 font-mono text-left text-sm">
                        {formatGreek(option.put.delta)}
                      </td>
                      <td className="py-2 px-3 font-mono text-left text-sm">
                        {formatPercent(option.put.iv)}
                      </td>
                      <td className="py-2 px-3 font-mono text-left text-accent-red text-sm">
                        ${formatPrice(option.put.price)}
                      </td>
                      {showGreeks && (
                        <>
                          <td className="py-2 px-3 font-mono text-left text-sm">
                            {formatGreek(option.put.gamma)}
                          </td>
                          <td className="py-2 px-3 font-mono text-left text-sm">
                            {formatGreek(option.put.vega)}
                          </td>
                        </>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 说明 */}
      <div className="card bg-bg-secondary">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-text-secondary">IV:</span>
            <span className="text-text-primary ml-2">隐含波动率</span>
          </div>
          <div>
            <span className="text-text-secondary">Delta:</span>
            <span className="text-text-primary ml-2">价格变化敏感度</span>
          </div>
          <div>
            <span className="text-text-secondary">Gamma:</span>
            <span className="text-text-primary ml-2">Delta变化率</span>
          </div>
          <div>
            <span className="text-text-secondary">Vega:</span>
            <span className="text-text-primary ml-2">波动率敏感度</span>
          </div>
          <div>
            <span className="text-accent-blue">蓝色高亮:</span>
            <span className="text-text-primary ml-2">接近平值期权(ATM)</span>
          </div>
          <div>
            <span className="text-accent-green">绿色:</span>
            <span className="text-text-primary ml-2">看涨期权</span>
            <span className="text-accent-red ml-3">红色:</span>
            <span className="text-text-primary ml-2">看跌期权</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OptionsChainTab
