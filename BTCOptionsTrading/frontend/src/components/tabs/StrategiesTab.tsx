import { useState, useEffect } from 'react'
import { strategiesApi } from '../../api/strategies'
import { dataApi } from '../../api/data'
import { useAppStore } from '../../store/useAppStore'
import type { Strategy, StrategyTemplate } from '../../api/types'
import Modal from '../Modal'
import LoadingSpinner from '../LoadingSpinner'
import StrategyDetailModal from '../strategy/StrategyDetailModal'
import StrategyEditModal from '../strategy/StrategyEditModal'
import StrikePicker from '../strategy/StrikePicker'
import StrategyWizard from '../strategy/StrategyWizard'
import PayoffDiagram from '../strategy/PayoffDiagram'
import SmartStrategyBuilder from '../strategy/SmartStrategyBuilder'
import ScheduledTradingManager from '../strategy/ScheduledTradingManager'
import QuickTradingModal from '../strategy/QuickTradingModal'

const StrategiesTab = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [templates, setTemplates] = useState<StrategyTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isWizardOpen, setIsWizardOpen] = useState(false)
  const [isSmartBuilderOpen, setIsSmartBuilderOpen] = useState(false)
  const [isScheduledTradingOpen, setIsScheduledTradingOpen] = useState(false)
  const [isQuickTradingOpen, setIsQuickTradingOpen] = useState(false)
  const [quickTradingStrategy, setQuickTradingStrategy] = useState<Strategy | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [isCreating, setIsCreating] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [copyInitialData, setCopyInitialData] = useState<{
    selectedTemplate?: string
    formData?: any
  } | undefined>(undefined)
  const { setError, setSuccessMessage } = useAppStore()

  // 期权链数据状态
  const [underlyingPrice, setUnderlyingPrice] = useState<number>(0)
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

  // 搜索和筛选状态
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'created_at' | 'max_profit' | 'max_loss'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // 表单状态
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    strike: '',
    expiry_date: '',
    quantity: '1',
    // 多腿策略的额外字段
    call_strike: '',
    put_strike: '',
    strikes: ['', '', '', ''], // 用于铁鹰策略
    wing_width: ''
  })

  // 加载策略列表
  const loadStrategies = async () => {
    try {
      setIsLoading(true)
      const data = await strategiesApi.list()
      // 确保 data 是数组
      setStrategies(Array.isArray(data) ? data : [])
    } catch (error) {
      setError(error instanceof Error ? error.message : '加载策略失败')
      setStrategies([]) // 出错时设置为空数组
    } finally {
      setIsLoading(false)
    }
  }

  // 加载策略模板
  const loadTemplates = async () => {
    try {
      const data = await strategiesApi.getTemplates()
      // 确保 templates 是数组
      setTemplates(Array.isArray(data.templates) ? data.templates : [])
    } catch (error) {
      console.error('加载模板失败:', error)
      setTemplates([]) // 出错时设置为空数组
    }
  }

  useEffect(() => {
    loadStrategies()
    loadTemplates()
    loadUnderlyingPrice()
  }, [])

  // 加载标的资产价格
  const loadUnderlyingPrice = async () => {
    try {
      const data = await dataApi.getUnderlyingPrice('BTC')
      setUnderlyingPrice(data.price)
    } catch (error) {
      console.error('加载标的价格失败:', error)
      setUnderlyingPrice(45000) // 使用默认值
    }
  }

  // 加载期权链数据
  const loadOptionsChain = async (expiryDate: string) => {
    if (!expiryDate) return

    try {
      setIsLoadingOptions(true)
      setOptionsLoadError(null)
      const rawData = await dataApi.getOptionsChain('BTC')
      
      // 处理数据：按执行价分组
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
      
      // 转换为StrikePicker需要的格式
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
      
      // 如果没有数据，使用模拟数据并显示警告
      if (processedData.length === 0) {
        setOptionsLoadError('未找到该到期日的期权数据，使用模拟数据')
        generateMockOptionsData()
      }
    } catch (error) {
      console.error('加载期权链失败:', error)
      setOptionsLoadError('无法加载实时市场数据，使用模拟数据。您也可以手动输入执行价。')
      // 生成模拟数据作为降级
      generateMockOptionsData()
    } finally {
      setIsLoadingOptions(false)
    }
  }

  // 生成模拟期权数据
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

  // 当到期日改变时加载期权链
  useEffect(() => {
    if (formData.expiry_date && isCreateModalOpen) {
      loadOptionsChain(formData.expiry_date)
    }
  }, [formData.expiry_date, isCreateModalOpen])

  // 获取选中执行价的市场数据
  const getSelectedOptionData = (strike: string) => {
    if (!strike || !optionsData.length) return null
    const strikeNum = parseFloat(strike)
    return optionsData.find(opt => opt.strike === strikeNum)
  }

  // 渲染市场数据显示组件
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

    return (
      <div className="mt-2 p-3 bg-bg-secondary rounded-lg border border-accent-blue border-opacity-30">
        <div className="text-xs font-medium text-text-secondary mb-2">市场数据</div>
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

  // 渲染执行价输入（支持选择器或手动输入）
  const renderStrikeInput = (
    value: string,
    onChange: (value: string) => void,
    label: string,
    optionType: 'call' | 'put' | 'both' = 'both'
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

  // 删除策略
  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个策略吗？')) return
    
    try {
      await strategiesApi.delete(id)
      setSuccessMessage('策略已删除')
      loadStrategies()
    } catch (error) {
      setError(error instanceof Error ? error.message : '删除策略失败')
    }
  }

  // 更新策略
  const handleUpdate = async (strategyId: string, data: any) => {
    try {
      await strategiesApi.update(strategyId, data)
      setSuccessMessage('策略已更新')
      setIsEditModalOpen(false)
      setIsDetailModalOpen(false)
      setSelectedStrategy(null)
      loadStrategies()
    } catch (error) {
      setError(error instanceof Error ? error.message : '更新策略失败')
      throw error
    }
  }

  // 打开编辑模态框
  const handleEdit = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setIsDetailModalOpen(false)
    setIsEditModalOpen(true)
  }

  // 复制策略
  const handleCopy = (strategy: Strategy) => {
    // 从策略中提取参数
    const legs = strategy.legs || []
    
    // 根据策略类型预填充表单
    const newFormData: any = {
      name: `${strategy.name} (副本)`,
      description: strategy.description || '',
      quantity: legs.length > 0 ? legs[0].quantity.toString() : '1',
      expiry_date: '',
      strike: '',
      call_strike: '',
      put_strike: '',
      strikes: ['', '', '', ''],
      wing_width: ''
    }

    // 从第一个腿获取到期日
    if (legs.length > 0 && legs[0].option_contract) {
      const expiryDate = new Date(legs[0].option_contract.expiration_date)
      newFormData.expiry_date = expiryDate.toISOString().split('T')[0]
    }

    // 根据策略类型填充执行价
    switch (strategy.strategy_type) {
      case 'single_leg':
        if (legs.length > 0) {
          newFormData.strike = legs[0].option_contract.strike_price.toString()
        }
        break
      
      case 'straddle':
        if (legs.length > 0) {
          newFormData.strike = legs[0].option_contract.strike_price.toString()
        }
        break
      
      case 'strangle':
        if (legs.length >= 2) {
          // 找到看涨和看跌期权
          const callLeg = legs.find(leg => leg.option_contract.option_type === 'call')
          const putLeg = legs.find(leg => leg.option_contract.option_type === 'put')
          if (callLeg) newFormData.call_strike = callLeg.option_contract.strike_price.toString()
          if (putLeg) newFormData.put_strike = putLeg.option_contract.strike_price.toString()
        }
        break
      
      case 'iron_condor':
        if (legs.length >= 4) {
          // 按执行价排序
          const sortedLegs = [...legs].sort((a, b) => 
            a.option_contract.strike_price - b.option_contract.strike_price
          )
          newFormData.strikes = sortedLegs.map(leg => 
            leg.option_contract.strike_price.toString()
          )
        }
        break
      
      case 'butterfly':
        if (legs.length >= 3) {
          // 找到中心执行价（卖出的那个）
          const centerLeg = legs.find(leg => leg.action === 'sell')
          if (centerLeg) {
            newFormData.strike = centerLeg.option_contract.strike_price.toString()
            // 计算翼宽
            const buyLegs = legs.filter(leg => leg.action === 'buy')
            if (buyLegs.length >= 2) {
              const wingWidth = Math.abs(
                buyLegs[0].option_contract.strike_price - centerLeg.option_contract.strike_price
              )
              newFormData.wing_width = wingWidth.toString()
            }
          }
        }
        break
    }

    // 关闭详情模态框，打开向导并传递初始数据
    setIsDetailModalOpen(false)
    setIsWizardOpen(true)
    
    // 设置向导的初始数据（通过state传递）
    setCopyInitialData({
      selectedTemplate: strategy.strategy_type,
      formData: newFormData
    })
  }

  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      strike: '',
      expiry_date: '',
      quantity: '1',
      call_strike: '',
      put_strike: '',
      strikes: ['', '', '', ''],
      wing_width: ''
    })
    setSelectedTemplate('')
  }

  // 创建策略
  const handleCreateStrategy = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedTemplate) {
      setError('请选择策略模板')
      return
    }

    await createStrategyFromData(formData, selectedTemplate)
  }

  // 从向导创建策略
  const handleWizardComplete = async (data: any) => {
    await createStrategyFromData(data, data.strategy_type)
  }

  // 通用策略创建逻辑
  const createStrategyFromData = async (data: any, strategyType: string) => {
    try {
      setIsCreating(true)
      
      // 根据不同的策略类型构建请求数据
      const quantity = parseInt(data.quantity) || 1
      const expiryDate = new Date(data.expiry_date).toISOString()
      
      // 辅助函数：创建期权合约对象
      const createContract = (optionType: string, strike: number) => ({
        instrument_name: `BTC-${data.expiry_date}-${strike}-${optionType === 'call' ? 'C' : 'P'}`,
        underlying: 'BTC',
        option_type: optionType,
        strike_price: strike,
        expiration_date: expiryDate
      })

      let legs: any[] = []

      switch (strategyType) {
        case 'single_leg':
          // 单腿策略 - 默认买入看涨
          const singleStrike = parseFloat(data.strike)
          legs = [{
            option_contract: createContract('call', singleStrike),
            action: 'buy',
            quantity: quantity
          }]
          break

        case 'straddle':
          // 跨式策略
          const straddleStrike = parseFloat(data.strike)
          legs = [
            {
              option_contract: createContract('call', straddleStrike),
              action: 'buy',
              quantity: quantity
            },
            {
              option_contract: createContract('put', straddleStrike),
              action: 'buy',
              quantity: quantity
            }
          ]
          break

        case 'strangle':
          // 宽跨式策略
          const callStrike = parseFloat(data.call_strike)
          const putStrike = parseFloat(data.put_strike)
          legs = [
            {
              option_contract: createContract('call', callStrike),
              action: 'buy',
              quantity: quantity
            },
            {
              option_contract: createContract('put', putStrike),
              action: 'buy',
              quantity: quantity
            }
          ]
          break

        case 'iron_condor':
          // 铁鹰策略
          const strikes = data.strikes.map((s: string) => parseFloat(s))
          legs = [
            {
              option_contract: createContract('put', strikes[0]),
              action: 'buy',
              quantity: quantity
            },
            {
              option_contract: createContract('put', strikes[1]),
              action: 'sell',
              quantity: quantity
            },
            {
              option_contract: createContract('call', strikes[2]),
              action: 'sell',
              quantity: quantity
            },
            {
              option_contract: createContract('call', strikes[3]),
              action: 'buy',
              quantity: quantity
            }
          ]
          break

        case 'butterfly':
          // 蝶式策略
          const centerStrike = parseFloat(data.strike)
          const wingWidth = parseFloat(data.wing_width)
          legs = [
            {
              option_contract: createContract('call', centerStrike - wingWidth),
              action: 'buy',
              quantity: quantity
            },
            {
              option_contract: createContract('call', centerStrike),
              action: 'sell',
              quantity: quantity * 2
            },
            {
              option_contract: createContract('call', centerStrike + wingWidth),
              action: 'buy',
              quantity: quantity
            }
          ]
          break
      }

      const requestData = {
        name: data.name || `${strategyType} 策略`,
        description: data.description || '',
        strategy_type: strategyType,
        legs: legs
      }

      await strategiesApi.create(requestData)
      setSuccessMessage('策略创建成功')
      setIsCreateModalOpen(false)
      setIsWizardOpen(false)
      resetForm()
      loadStrategies()
    } catch (error) {
      setError(error instanceof Error ? error.message : '创建策略失败')
      throw error
    } finally {
      setIsCreating(false)
    }
  }

  // 格式化日期
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  // 过滤和排序策略
  const getFilteredAndSortedStrategies = () => {
    let filtered = [...strategies]

    // 搜索过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(strategy => 
        strategy.name.toLowerCase().includes(query) ||
        (strategy.description && strategy.description.toLowerCase().includes(query))
      )
    }

    // 类型筛选
    if (filterType !== 'all') {
      filtered = filtered.filter(strategy => strategy.strategy_type === filterType)
    }

    // 排序
    filtered.sort((a, b) => {
      let comparison = 0
      
      switch (sortBy) {
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'max_profit':
          const profitA = a.max_profit ?? 0
          const profitB = b.max_profit ?? 0
          comparison = profitA - profitB
          break
        case 'max_loss':
          const lossA = a.max_loss ?? 0
          const lossB = b.max_loss ?? 0
          comparison = lossA - lossB
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return filtered
  }

  const filteredStrategies = getFilteredAndSortedStrategies()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">策略管理</h2>
        <div className="flex gap-3">
          <button 
            className="btn btn-secondary"
            onClick={() => setIsScheduledTradingOpen(true)}
            title="管理定时交易"
          >
            ⏰ 定时交易
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => setIsSmartBuilderOpen(true)}
            title="使用智能构建器（相对参数）"
          >
            🧠 智能构建
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => setIsCreateModalOpen(true)}
            title="快速创建（简化表单）"
          >
            快速创建
          </button>
          <button 
            className="btn btn-primary"
            onClick={() => setIsWizardOpen(true)}
            title="使用向导创建（推荐）"
          >
            + 创建新策略
          </button>
        </div>
      </div>

      {/* 策略模板卡片 */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-text-primary">策略模板</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.isArray(templates) && templates.map((template) => (
            <div 
              key={template.type}
              className="card hover:bg-opacity-80 cursor-pointer transition-all group relative overflow-hidden"
              onClick={() => {
                setSelectedTemplate(template.type)
                setIsCreateModalOpen(true)
              }}
            >
              {/* 基本信息 */}
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-lg font-semibold text-text-primary flex-1">{template.name}</h4>
                  {/* 收益曲线图示 */}
                  <div className="ml-2">
                    <PayoffDiagram strategyType={template.type} width={80} height={40} />
                  </div>
                </div>
                
                <p className="text-text-secondary text-sm mb-3">{template.description}</p>
                
                {/* 市场条件标签 */}
                {template.market_condition && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs px-2 py-1 bg-accent-blue bg-opacity-20 text-accent-blue rounded">
                      {template.market_condition}
                    </span>
                  </div>
                )}
                
                {/* 关键特点（悬停显示） */}
                {template.key_features && template.key_features.length > 0 && (
                  <div className="mt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <div className="text-xs font-medium text-text-secondary mb-2">关键特点:</div>
                    <ul className="space-y-1">
                      {template.key_features.slice(0, 3).map((feature, index) => (
                        <li key={index} className="text-xs text-text-secondary flex items-start gap-2">
                          <svg className="w-3 h-3 text-accent-green mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    
                    {/* 了解更多链接 */}
                    {template.detailed_description && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          alert(`${template.name}\n\n${template.detailed_description}\n\n风险特征:\n最大收益: ${template.risk_profile?.max_profit}\n最大损失: ${template.risk_profile?.max_loss}\n盈亏平衡: ${template.risk_profile?.breakeven}`)
                        }}
                        className="mt-3 text-xs text-accent-blue hover:text-accent-blue-light flex items-center gap-1"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        了解更多
                      </button>
                    )}
                  </div>
                )}
              </div>
              
              {/* 悬停时的详细信息背景 */}
              <div className="absolute inset-0 bg-gradient-to-t from-bg-secondary to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none" />
            </div>
          ))}
        </div>
      </div>

      {/* 已创建的策略列表 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-text-primary">我的策略</h3>
          <div className="text-sm text-text-secondary">
            共 {filteredStrategies.length} 个策略
            {searchQuery || filterType !== 'all' ? ` (已过滤 ${strategies.length} 个中的 ${filteredStrategies.length} 个)` : ''}
          </div>
        </div>

        {/* 搜索和筛选控件 */}
        <div className="mb-4 space-y-3">
          {/* 搜索框 */}
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索策略名称或描述..."
              className="input w-full pl-10"
            />
            <svg 
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-secondary"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-secondary hover:text-text-primary"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* 筛选和排序控件 */}
          <div className="flex gap-3 flex-wrap">
            {/* 类型筛选 */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input flex-1 min-w-[200px]"
            >
              <option value="all">所有类型</option>
              <option value="single_leg">单腿策略</option>
              <option value="straddle">跨式策略</option>
              <option value="strangle">宽跨式策略</option>
              <option value="iron_condor">铁鹰策略</option>
              <option value="butterfly">蝶式策略</option>
            </select>

            {/* 排序选择 */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="input flex-1 min-w-[200px]"
            >
              <option value="created_at">按创建时间</option>
              <option value="max_profit">按最大收益</option>
              <option value="max_loss">按最大损失</option>
            </select>

            {/* 排序方向 */}
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-4 py-2 bg-bg-secondary text-text-primary rounded-lg hover:bg-opacity-80 transition-colors flex items-center gap-2"
              title={sortOrder === 'asc' ? '升序' : '降序'}
            >
              {sortOrder === 'asc' ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                  </svg>
                  升序
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                  </svg>
                  降序
                </>
              )}
            </button>
          </div>
        </div>
        
        {isLoading ? (
          <div className="card">
            <LoadingSpinner />
          </div>
        ) : filteredStrategies.length === 0 ? (
          <div className="card text-center py-8">
            {strategies.length === 0 ? (
              <>
                <p className="text-text-secondary">还没有创建任何策略</p>
                <p className="text-text-secondary text-sm mt-2">点击上方"创建新策略"按钮开始</p>
              </>
            ) : (
              <>
                <p className="text-text-secondary">没有找到匹配的策略</p>
                <p className="text-text-secondary text-sm mt-2">尝试调整搜索条件或筛选器</p>
                <button
                  onClick={() => {
                    setSearchQuery('')
                    setFilterType('all')
                  }}
                  className="mt-4 px-4 py-2 bg-accent-blue text-white rounded-lg hover:bg-opacity-80 transition-colors"
                >
                  清除筛选
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredStrategies.map((strategy) => (
              <div 
                key={strategy.id} 
                className="card cursor-pointer hover:border-accent-blue transition-colors"
                onClick={() => {
                  setSelectedStrategy(strategy)
                  setIsDetailModalOpen(true)
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-lg font-semibold text-text-primary">{strategy.name}</h4>
                      {strategy.name.includes('(副本)') && (
                        <span className="text-xs px-2 py-0.5 bg-accent-blue bg-opacity-20 text-accent-blue rounded border border-accent-blue border-opacity-30">
                          复制策略
                        </span>
                      )}
                    </div>
                    {strategy.description && (
                      <p className="text-text-secondary text-sm mt-1">{strategy.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-3 text-sm">
                      <span className="text-text-secondary">
                        类型: <span className="text-text-primary">{strategy.strategy_type}</span>
                      </span>
                      {strategy.max_profit !== null && strategy.max_profit !== undefined && (
                        <span className="text-text-secondary">
                          最大收益: <span className="text-accent-green">${strategy.max_profit.toFixed(2)}</span>
                        </span>
                      )}
                      {strategy.max_loss !== null && strategy.max_loss !== undefined && (
                        <span className="text-text-secondary">
                          最大损失: <span className="text-accent-red">${Math.abs(strategy.max_loss).toFixed(2)}</span>
                        </span>
                      )}
                    </div>
                    <p className="text-text-disabled text-xs mt-2">
                      创建时间: {formatDate(strategy.created_at)}
                    </p>
                    
                    {/* 快速操作按钮 */}
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setQuickTradingStrategy(strategy)
                          setIsQuickTradingOpen(true)
                        }}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors"
                        title="立即执行交易"
                      >
                        ⚡ 快速交易
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(strategy.id)
                    }}
                    className="text-accent-red hover:text-opacity-80 transition-colors ml-4"
                    title="删除策略"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 策略详情模态框 */}
      <StrategyDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false)
          setSelectedStrategy(null)
        }}
        strategy={selectedStrategy}
        onDelete={handleDelete}
        onEdit={handleEdit}
        onCopy={handleCopy}
      />

      {/* 策略编辑模态框 */}
      <StrategyEditModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false)
          setSelectedStrategy(null)
        }}
        strategy={selectedStrategy}
        templates={templates}
        onUpdate={handleUpdate}
      />

      {/* 创建策略模态框 */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false)
          resetForm()
        }}
        title="创建新策略"
        size="lg"
      >
        <form onSubmit={handleCreateStrategy} className="space-y-4">
          {/* 策略模板选择 */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              策略模板 *
            </label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="input w-full"
              required
            >
              <option value="">请选择策略模板</option>
              {templates.map((template) => (
                <option key={template.type} value={template.type}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

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
            <label className="block text-sm font-medium text-text-primary mb-2">
              到期日 *
            </label>
            <input
              type="date"
              value={formData.expiry_date}
              onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
              className="input w-full"
              required
              min={new Date().toISOString().split('T')[0]}
            />
            
            {/* 显示期权链加载错误 */}
            {optionsLoadError && (
              <div className="mt-2 p-3 bg-yellow-900 bg-opacity-20 border border-yellow-600 border-opacity-30 rounded-lg">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-sm text-yellow-200">{optionsLoadError}</p>
                    <p className="text-xs text-yellow-300 mt-1">
                      提示：您可以使用下方的执行价选择器（显示模拟数据），或直接手动输入执行价数值。
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
              '执行价 * (看涨和看跌期权使用相同执行价)',
              'both'
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

          {/* 按钮 */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => {
                setIsCreateModalOpen(false)
                resetForm()
              }}
              className="btn btn-secondary"
              disabled={isCreating}
            >
              取消
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isCreating}
            >
              {isCreating ? '创建中...' : '创建策略'}
            </button>
          </div>
        </form>
      </Modal>

      {/* 策略创建向导 */}
      <StrategyWizard
        isOpen={isWizardOpen}
        onClose={() => {
          setIsWizardOpen(false)
          setCopyInitialData(undefined)
        }}
        onComplete={handleWizardComplete}
        templates={templates}
        underlyingPrice={underlyingPrice}
        initialData={copyInitialData}
      />

      {/* 智能策略构建器 */}
      <Modal
        isOpen={isSmartBuilderOpen}
        onClose={() => setIsSmartBuilderOpen(false)}
        title="智能策略构建器"
        size="xl"
      >
        <SmartStrategyBuilder
          onStrategyBuilt={(strategy) => {
            setSuccessMessage('策略构建成功！')
            setIsSmartBuilderOpen(false)
            loadStrategies()
          }}
          onCancel={() => setIsSmartBuilderOpen(false)}
        />
      </Modal>

      {/* 定时交易管理 */}
      <Modal
        isOpen={isScheduledTradingOpen}
        onClose={() => setIsScheduledTradingOpen(false)}
        title="定时交易管理"
        size="xl"
      >
        <ScheduledTradingManager
          strategies={strategies}
          onClose={() => setIsScheduledTradingOpen(false)}
        />
      </Modal>

      {/* 快速交易 */}
      <Modal
        isOpen={isQuickTradingOpen}
        onClose={() => {
          setIsQuickTradingOpen(false)
          setQuickTradingStrategy(null)
        }}
        title="⚡ 快速交易"
        size="lg"
      >
        {quickTradingStrategy && (
          <QuickTradingModal
            strategy={quickTradingStrategy}
            onClose={() => {
              setIsQuickTradingOpen(false)
              setQuickTradingStrategy(null)
            }}
            onSuccess={() => {
              loadStrategies()
            }}
          />
        )}
      </Modal>
    </div>
  )
}

export default StrategiesTab
