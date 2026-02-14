import { useState, useEffect } from 'react'
import Modal from '../Modal'
import type { Strategy, StrategyTemplate } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'

interface StrategyEditModalProps {
  isOpen: boolean
  onClose: () => void
  strategy: Strategy | null
  templates: StrategyTemplate[]
  onUpdate: (strategyId: string, data: any) => Promise<void>
}

const StrategyEditModal = ({ isOpen, onClose, strategy, templates, onUpdate }: StrategyEditModalProps) => {
  const { setError } = useAppStore()
  const [isUpdating, setIsUpdating] = useState(false)
  
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

  // 当策略改变时，预填充表单
  useEffect(() => {
    if (strategy && strategy.legs && strategy.legs.length > 0) {
      const legs = strategy.legs
      
      // 提取到期日（从第一个腿）
      const expiryDate = legs[0].option_contract.expiration_date.split('T')[0]
      
      // 提取数量（从第一个腿）
      const quantity = legs[0].quantity.toString()
      
      // 根据策略类型提取执行价
      let newFormData = {
        name: strategy.name,
        description: strategy.description || '',
        expiry_date: expiryDate,
        quantity: quantity,
        strike: '',
        call_strike: '',
        put_strike: '',
        strikes: ['', '', '', ''],
        wing_width: ''
      }

      switch (strategy.strategy_type) {
        case 'single_leg':
          newFormData.strike = legs[0].option_contract.strike_price.toString()
          break

        case 'straddle':
          // 跨式策略：看涨和看跌使用相同执行价
          newFormData.strike = legs[0].option_contract.strike_price.toString()
          break

        case 'strangle':
          // 宽跨式策略：找到看涨和看跌的执行价
          const callLeg = legs.find(leg => leg.option_contract.option_type === 'call')
          const putLeg = legs.find(leg => leg.option_contract.option_type === 'put')
          if (callLeg) newFormData.call_strike = callLeg.option_contract.strike_price.toString()
          if (putLeg) newFormData.put_strike = putLeg.option_contract.strike_price.toString()
          break

        case 'iron_condor':
          // 铁鹰策略：4个执行价（从低到高）
          const sortedLegs = [...legs].sort((a, b) => 
            a.option_contract.strike_price - b.option_contract.strike_price
          )
          newFormData.strikes = sortedLegs.map(leg => 
            leg.option_contract.strike_price.toString()
          )
          break

        case 'butterfly':
          // 蝶式策略：中心执行价和翼宽
          const sortedButterflyLegs = [...legs].sort((a, b) => 
            a.option_contract.strike_price - b.option_contract.strike_price
          )
          const centerStrike = sortedButterflyLegs[1].option_contract.strike_price
          const wingWidth = centerStrike - sortedButterflyLegs[0].option_contract.strike_price
          newFormData.strike = centerStrike.toString()
          newFormData.wing_width = wingWidth.toString()
          break
      }

      setFormData(newFormData)
    }
  }, [strategy])

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!strategy) return

    try {
      setIsUpdating(true)
      
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

      switch (strategy.strategy_type) {
        case 'single_leg':
          const singleStrike = parseFloat(formData.strike)
          legs = [{
            option_contract: createContract('call', singleStrike),
            action: 'buy',
            quantity: quantity
          }]
          break

        case 'straddle':
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
        name: formData.name,
        description: formData.description,
        strategy_type: strategy.strategy_type,
        legs: legs
      }

      await onUpdate(strategy.id, requestData)
      onClose()
    } catch (error) {
      setError(error instanceof Error ? error.message : '更新策略失败')
    } finally {
      setIsUpdating(false)
    }
  }

  if (!strategy) return null

  const selectedTemplate = strategy.strategy_type

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="编辑策略"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 策略类型显示（不可编辑） */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            策略类型
          </label>
          <div className="input w-full bg-bg-secondary cursor-not-allowed">
            {templates.find(t => t.type === strategy.strategy_type)?.name || strategy.strategy_type}
          </div>
          <p className="text-xs text-text-secondary mt-1">策略类型不可修改</p>
        </div>

        {/* 基本信息 */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            策略名称 *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="input w-full"
            required
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
            onClick={onClose}
            className="btn btn-secondary"
            disabled={isUpdating}
          >
            取消
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isUpdating}
          >
            {isUpdating ? '更新中...' : '保存更改'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default StrategyEditModal
