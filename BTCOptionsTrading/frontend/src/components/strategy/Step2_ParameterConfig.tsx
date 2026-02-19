import { useState, useEffect } from 'react'
import StrikePicker from './StrikePicker'
import ExpiryPicker from './ExpiryPicker'
import { dataApi } from '../../api/data'

interface Step2Props {
  selectedTemplate: string
  formData: any
  setFormData: (data: any) => void
  underlyingPrice: number
}

const Step2_ParameterConfig = ({ 
  selectedTemplate, 
  formData, 
  setFormData,
  underlyingPrice 
}: Step2Props) => {
  const [optionsData, setOptionsData] = useState<Array<{
    strike: number
    callPrice: number
    putPrice: number
    callIV: number
    putIV: number
  }>>([])
  const [isLoadingOptions, setIsLoadingOptions] = useState(false)
  const [optionsLoadError, setOptionsLoadError] = useState<string | null>(null)
  const [useManualInput, setUseManualInput] = useState(false)
  const [availableExpiryDates, setAvailableExpiryDates] = useState<string[]>([])
  const [isLoadingDates, setIsLoadingDates] = useState(false)

  // 加载可用的到期日期
  const loadAvailableExpiryDates = async () => {
    try {
      setIsLoadingDates(true)
      const rawData = await dataApi.getOptionsChain('BTC')
      
      // 提取所有唯一的到期日期
      const datesSet = new Set<string>()
      rawData.forEach((option: any) => {
        if (option.expiration_timestamp) {
          const date = new Date(option.expiration_timestamp * 1000)
          const dateStr = date.toISOString().split('T')[0]
          datesSet.add(dateStr)
        }
      })
      
      // 转换为数组并排序
      const sortedDates = Array.from(datesSet).sort()
      setAvailableExpiryDates(sortedDates)
    } catch (error) {
      console.error('加载到期日期失败:', error)
      // 如果加载失败，生成一些默认日期
      const defaultDates = []
      const today = new Date()
      for (let i = 7; i <= 90; i += 7) {
        const futureDate = new Date(today)
        futureDate.setDate(today.getDate() + i)
        defaultDates.push(futureDate.toISOString().split('T')[0])
      }
      setAvailableExpiryDates(defaultDates)
    } finally {
      setIsLoadingDates(false)
    }
  }

  // 组件加载时获取可用日期
  useEffect(() => {
    loadAvailableExpiryDates()
  }, [])

  // 加载期权链数据
  const loadOptionsChain = async (expiryDate: string) => {
    if (!expiryDate) return

    try {
      setIsLoadingOptions(true)
      setOptionsLoadError(null)
      const rawData = await dataApi.getOptionsChain('BTC')
      
      const strikeMap = new Map<number, { call?: any; put?: any }>()
      const targetDate = new Date(expiryDate).toISOString().split('T')[0]
      
      rawData.forEach((option: any) => {
        const optionDate = new Date(option.expiration_timestamp * 1000)
          .toISOString().split('T')[0]
        
        if (optionDate !== targetDate) return
        
        const strike = option.strike
        if (!strike) return
        
        if (!strikeMap.has(strike)) {
          strikeMap.set(strike, {})
        }
        
        const strikeData = strikeMap.get(strike)!
        if (option.option_type === 'call') {
          strikeData.call = option
        } else if (option.option_type === 'put') {
          strikeData.put = option
        }
      })
      
      const processedData = Array.from(strikeMap.entries())
        .filter(([_, data]) => data.call && data.put)
        .map(([strike, data]) => ({
          strike,
          callPrice: data.call?.mark_price || 0,
          putPrice: data.put?.mark_price || 0,
          callIV: data.call?.implied_volatility || 0,
          putIV: data.put?.implied_volatility || 0
        }))
        .sort((a, b) => a.strike - b.strike)
      
      setOptionsData(processedData)
      
      if (processedData.length === 0) {
        setOptionsLoadError('未找到该到期日的期权数据，使用模拟数据')
        generateMockOptionsData()
      }
    } catch (error) {
      console.error('加载期权链失败:', error)
      setOptionsLoadError('无法加载实时市场数据，使用模拟数据')
      generateMockOptionsData()
    } finally {
      setIsLoadingOptions(false)
    }
  }

  const generateMockOptionsData = () => {
    const basePrice = underlyingPrice || 45000
    const strikeInterval = 1000
    const mockData = []
    
    for (let i = -7; i <= 7; i++) {
      const strike = Math.round(basePrice + (i * strikeInterval))
      mockData.push({
        strike,
        callPrice: Math.max(0, basePrice - strike + Math.random() * 1000),
        putPrice: Math.max(0, strike - basePrice + Math.random() * 1000),
        callIV: 0.6 + Math.random() * 0.4,
        putIV: 0.6 + Math.random() * 0.4
      })
    }
    
    setOptionsData(mockData)
  }

  useEffect(() => {
    if (formData.expiry_date) {
      loadOptionsChain(formData.expiry_date)
    }
  }, [formData.expiry_date])

  const getSelectedOptionData = (strike: string) => {
    if (!strike || !optionsData.length) return null
    const strikeNum = parseFloat(strike)
    return optionsData.find(opt => opt.strike === strikeNum)
  }

  const renderMarketDataDisplay = (strike: string, optionType: 'call' | 'put' | 'both' = 'both') => {
    const data = getSelectedOptionData(strike)
    
    if (!data) {
      return (
        <div className="mt-2 p-3 bg-bg-secondary rounded-lg border border-text-disabled">
          <p className="text-sm text-text-secondary">
            {isLoadingOptions ? '加载市场数据中...' : '请先选择到期日和执行价'}
          </p>
        </div>
      )
    }

    // 如果有错误且使用模拟数据，显示提示
    const isUsingMockData = optionsLoadError !== null

    return (
      <div className="mt-2 p-3 bg-bg-secondary rounded-lg border border-accent-blue border-opacity-30">
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs font-medium text-text-secondary">市场数据</div>
          {isUsingMockData && (
            <span className="text-xs text-yellow-500 flex items-center gap-1">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              模拟数据
            </span>
          )}
        </div>
        <div className="grid grid-cols-2 gap-3">
          {(optionType === 'call' || optionType === 'both') && (
            <div>
              <div className="text-xs text-text-secondary mb-1">看涨期权 (Call)</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-text-secondary">价格:</span>
                  <span className="font-mono text-accent-green">
                    {data.callPrice > 0 ? `${data.callPrice.toFixed(4)} BTC` : '-'}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-text-secondary">隐含波动率:</span>
                  <span className="font-mono text-text-primary">
                    {data.callIV > 0 ? `${(data.callIV * 100).toFixed(1)}%` : '-'}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          {(optionType === 'put' || optionType === 'both') && (
            <div>
              <div className="text-xs text-text-secondary mb-1">看跌期权 (Put)</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-text-secondary">价格:</span>
                  <span className="font-mono text-accent-red">
                    {data.putPrice > 0 ? `${data.putPrice.toFixed(4)} BTC` : '-'}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-text-secondary">隐含波动率:</span>
                  <span className="font-mono text-text-primary">
                    {data.putIV > 0 ? `${(data.putIV * 100).toFixed(1)}%` : '-'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {underlyingPrice > 0 && (
          <div className="mt-2 pt-2 border-t border-text-disabled">
            <div className="flex justify-between text-xs">
              <span className="text-text-secondary">标的价格:</span>
              <span className="font-mono text-text-primary font-medium">
                ${underlyingPrice.toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderStrikeInput = (
    value: string,
    onChange: (value: string) => void,
    label: string,
    optionType: 'call' | 'put' | 'both' = 'both',
    helpText?: string
  ) => {
    return (
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-text-primary">
            {label}
          </label>
          <button
            type="button"
            onClick={() => setUseManualInput(!useManualInput)}
            className="text-xs text-accent-blue hover:text-accent-blue-light transition-colors"
          >
            {useManualInput ? '使用选择器' : '手动输入'}
          </button>
        </div>
        
        {helpText && (
          <p className="text-xs text-text-secondary mb-2">{helpText}</p>
        )}
        
        {useManualInput ? (
          <input
            type="number"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="input w-full"
            placeholder="输入执行价，例如: 45000"
            required
            step="100"
          />
        ) : (
          <StrikePicker
            value={value ? parseFloat(value) : null}
            onChange={(strike) => onChange(strike.toString())}
            underlyingPrice={underlyingPrice}
            optionsData={optionsData}
            label=""
            disabled={isLoadingOptions || !formData.expiry_date}
          />
        )}
        
        {value && !useManualInput && renderMarketDataDisplay(value, optionType)}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 基本信息 */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          策略名称
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="input w-full"
          placeholder="留空将自动生成"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          策略描述
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          className="input w-full"
          rows={2}
          placeholder="可选"
        />
      </div>

      {/* 到期日 */}
      <div>
        <ExpiryPicker
          value={formData.expiry_date}
          onChange={(date) => setFormData({ ...formData, expiry_date: date })}
          availableDates={availableExpiryDates}
          label="到期日"
          disabled={isLoadingDates}
        />
        
        {optionsLoadError && (
          <div className="mt-2 p-3 bg-yellow-900 bg-opacity-20 border border-yellow-600 border-opacity-30 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm text-yellow-200 font-medium mb-1">{optionsLoadError}</p>
                <p className="text-xs text-yellow-300">
                  您可以使用模拟数据继续创建策略，或点击"手动输入"按钮直接输入执行价。
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          数量 *
        </label>
        <input
          type="number"
          value={formData.quantity}
          onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
          className="input w-full"
          min="1"
          required
        />
      </div>

      {/* 根据策略类型显示不同的字段 */}
      {selectedTemplate === 'single_leg' && (
        renderStrikeInput(
          formData.strike,
          (value) => setFormData({ ...formData, strike: value }),
          '执行价 *',
          'both'
        )
      )}

      {selectedTemplate === 'straddle' && (
        renderStrikeInput(
          formData.strike,
          (value) => setFormData({ ...formData, strike: value }),
          '执行价 *',
          'both',
          '看涨和看跌期权使用相同执行价'
        )
      )}

      {selectedTemplate === 'strangle' && (
        <>
          {renderStrikeInput(
            formData.call_strike,
            (value) => setFormData({ ...formData, call_strike: value }),
            '看涨期权执行价 *',
            'call'
          )}
          {renderStrikeInput(
            formData.put_strike,
            (value) => setFormData({ ...formData, put_strike: value }),
            '看跌期权执行价 *',
            'put'
          )}
        </>
      )}

      {selectedTemplate === 'iron_condor' && (
        <div className="space-y-3">
          <p className="text-sm text-text-secondary">
            铁鹰策略需要4个执行价（从低到高）
          </p>
          {renderStrikeInput(
            formData.strikes[0],
            (value) => {
              const newStrikes = [...formData.strikes]
              newStrikes[0] = value
              setFormData({ ...formData, strikes: newStrikes })
            },
            '买入看跌执行价 *',
            'put'
          )}
          {renderStrikeInput(
            formData.strikes[1],
            (value) => {
              const newStrikes = [...formData.strikes]
              newStrikes[1] = value
              setFormData({ ...formData, strikes: newStrikes })
            },
            '卖出看跌执行价 *',
            'put'
          )}
          {renderStrikeInput(
            formData.strikes[2],
            (value) => {
              const newStrikes = [...formData.strikes]
              newStrikes[2] = value
              setFormData({ ...formData, strikes: newStrikes })
            },
            '卖出看涨执行价 *',
            'call'
          )}
          {renderStrikeInput(
            formData.strikes[3],
            (value) => {
              const newStrikes = [...formData.strikes]
              newStrikes[3] = value
              setFormData({ ...formData, strikes: newStrikes })
            },
            '买入看涨执行价 *',
            'call'
          )}
        </div>
      )}

      {selectedTemplate === 'butterfly' && (
        <>
          {renderStrikeInput(
            formData.strike,
            (value) => setFormData({ ...formData, strike: value }),
            '中心执行价 *',
            'call'
          )}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              翼宽 *
            </label>
            <input
              type="number"
              value={formData.wing_width}
              onChange={(e) => setFormData({ ...formData, wing_width: e.target.value })}
              className="input w-full"
              placeholder="例如: 2000"
              required
            />
            <p className="text-xs text-text-secondary mt-1">
              翼宽决定了两侧执行价与中心执行价的距离
            </p>
          </div>
        </>
      )}
    </div>
  )
}

export default Step2_ParameterConfig
