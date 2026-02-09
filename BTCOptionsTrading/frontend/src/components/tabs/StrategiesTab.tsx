import { useState, useEffect } from 'react'
import { strategiesApi } from '../../api/strategies'
import { useAppStore } from '../../store/useAppStore'
import type { Strategy, StrategyTemplate } from '../../api/types'
import Modal from '../Modal'
import LoadingSpinner from '../LoadingSpinner'

const StrategiesTab = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [templates, setTemplates] = useState<StrategyTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [isCreating, setIsCreating] = useState(false)
  const { setError, setSuccessMessage } = useAppStore()

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
      setStrategies(data)
    } catch (error) {
      setError(error instanceof Error ? error.message : '加载策略失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 加载策略模板
  const loadTemplates = async () => {
    try {
      const data = await strategiesApi.getTemplates()
      setTemplates(data.templates)
    } catch (error) {
      console.error('加载模板失败:', error)
    }
  }

  useEffect(() => {
    loadStrategies()
    loadTemplates()
  }, [])

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

    try {
      setIsCreating(true)
      
      // 根据不同的策略类型构建请求数据
      const quantity = parseInt(formData.quantity) || 1
      const expiryDate = new Date(formData.expiry_date).toISOString()
      
      // 辅助函数：创建期权合约对象
      const createContract = (optionType: string, strike: number) => ({
        instrument_name: `BTC-${formData.expiry_date}-${strike}-${optionType === 'call' ? 'C' : 'P'}`,
        underlying: 'BTC',
        option_type: optionType,
        strike_price: strike,
        expiration_date: expiryDate
      })

      let legs: any[] = []

      switch (selectedTemplate) {
        case 'single_leg':
          // 单腿策略 - 默认买入看涨
          const singleStrike = parseFloat(formData.strike)
          legs = [{
            option_contract: createContract('call', singleStrike),
            action: 'buy',
            quantity: quantity
          }]
          break

        case 'straddle':
          // 跨式策略
          const straddleStrike = parseFloat(formData.strike)
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
          const callStrike = parseFloat(formData.call_strike)
          const putStrike = parseFloat(formData.put_strike)
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
          const strikes = formData.strikes.map(s => parseFloat(s))
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
          const centerStrike = parseFloat(formData.strike)
          const wingWidth = parseFloat(formData.wing_width)
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
        name: formData.name || `${selectedTemplate} 策略`,
        description: formData.description || '',
        strategy_type: selectedTemplate,
        legs: legs
      }

      await strategiesApi.create(requestData)
      setSuccessMessage('策略创建成功')
      setIsCreateModalOpen(false)
      resetForm()
      loadStrategies()
    } catch (error) {
      setError(error instanceof Error ? error.message : '创建策略失败')
    } finally {
      setIsCreating(false)
    }
  }

  // 格式化日期
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">策略管理</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setIsCreateModalOpen(true)}
        >
          + 创建新策略
        </button>
      </div>

      {/* 策略模板卡片 */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-text-primary">策略模板</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div 
              key={template.type}
              className="card hover:bg-opacity-80 cursor-pointer transition-all"
              onClick={() => {
                setSelectedTemplate(template.type)
                setIsCreateModalOpen(true)
              }}
            >
              <h4 className="text-lg font-semibold mb-2 text-text-primary">{template.name}</h4>
              <p className="text-text-secondary text-sm">{template.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 已创建的策略列表 */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-text-primary">我的策略</h3>
        
        {isLoading ? (
          <div className="card">
            <LoadingSpinner />
          </div>
        ) : strategies.length === 0 ? (
          <div className="card text-center py-8">
            <p className="text-text-secondary">还没有创建任何策略</p>
            <p className="text-text-secondary text-sm mt-2">点击上方"创建新策略"按钮开始</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {strategies.map((strategy) => (
              <div key={strategy.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-text-primary">{strategy.name}</h4>
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
                  </div>
                  <button
                    onClick={() => handleDelete(strategy.id)}
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
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                执行价 *
              </label>
              <input
                type="number"
                value={formData.strike}
                onChange={(e) => setFormData({ ...formData, strike: e.target.value })}
                className="input w-full"
                placeholder="例如: 45000"
                required
              />
            </div>
          )}

          {selectedTemplate === 'straddle' && (
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                执行价 * (看涨和看跌期权使用相同执行价)
              </label>
              <input
                type="number"
                value={formData.strike}
                onChange={(e) => setFormData({ ...formData, strike: e.target.value })}
                className="input w-full"
                placeholder="例如: 45000"
                required
              />
            </div>
          )}

          {selectedTemplate === 'strangle' && (
            <>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  看涨期权执行价 *
                </label>
                <input
                  type="number"
                  value={formData.call_strike}
                  onChange={(e) => setFormData({ ...formData, call_strike: e.target.value })}
                  className="input w-full"
                  placeholder="例如: 47000"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  看跌期权执行价 *
                </label>
                <input
                  type="number"
                  value={formData.put_strike}
                  onChange={(e) => setFormData({ ...formData, put_strike: e.target.value })}
                  className="input w-full"
                  placeholder="例如: 43000"
                  required
                />
              </div>
            </>
          )}

          {selectedTemplate === 'iron_condor' && (
            <div className="space-y-3">
              <p className="text-sm text-text-secondary">
                铁鹰策略需要4个执行价（从低到高）
              </p>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  买入看跌执行价 *
                </label>
                <input
                  type="number"
                  value={formData.strikes[0]}
                  onChange={(e) => {
                    const newStrikes = [...formData.strikes]
                    newStrikes[0] = e.target.value
                    setFormData({ ...formData, strikes: newStrikes })
                  }}
                  className="input w-full"
                  placeholder="例如: 42000"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  卖出看跌执行价 *
                </label>
                <input
                  type="number"
                  value={formData.strikes[1]}
                  onChange={(e) => {
                    const newStrikes = [...formData.strikes]
                    newStrikes[1] = e.target.value
                    setFormData({ ...formData, strikes: newStrikes })
                  }}
                  className="input w-full"
                  placeholder="例如: 43500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  卖出看涨执行价 *
                </label>
                <input
                  type="number"
                  value={formData.strikes[2]}
                  onChange={(e) => {
                    const newStrikes = [...formData.strikes]
                    newStrikes[2] = e.target.value
                    setFormData({ ...formData, strikes: newStrikes })
                  }}
                  className="input w-full"
                  placeholder="例如: 46500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  买入看涨执行价 *
                </label>
                <input
                  type="number"
                  value={formData.strikes[3]}
                  onChange={(e) => {
                    const newStrikes = [...formData.strikes]
                    newStrikes[3] = e.target.value
                    setFormData({ ...formData, strikes: newStrikes })
                  }}
                  className="input w-full"
                  placeholder="例如: 48000"
                  required
                />
              </div>
            </div>
          )}

          {selectedTemplate === 'butterfly' && (
            <>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  中心执行价 *
                </label>
                <input
                  type="number"
                  value={formData.strike}
                  onChange={(e) => setFormData({ ...formData, strike: e.target.value })}
                  className="input w-full"
                  placeholder="例如: 45000"
                  required
                />
              </div>
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
    </div>
  )
}

export default StrategiesTab
