import Modal from '../Modal'
import type { Strategy } from '../../api/types'

interface StrategyDetailModalProps {
  isOpen: boolean
  onClose: () => void
  strategy: Strategy | null
  onEdit?: (strategy: Strategy) => void
  onDelete?: (strategyId: string) => void
  onCopy?: (strategy: Strategy) => void
}

const StrategyDetailModal = ({
  isOpen,
  onClose,
  strategy,
  onEdit,
  onDelete,
  onCopy
}: StrategyDetailModalProps) => {
  if (!strategy) return null

  const handleEdit = () => {
    if (onEdit) {
      onEdit(strategy)
    }
  }

  const handleDelete = () => {
    if (onDelete && confirm('确定要删除这个策略吗？')) {
      onDelete(strategy.id)
      onClose()
    }
  }

  const handleCopy = () => {
    if (onCopy) {
      onCopy(strategy)
      onClose()
    }
  }

  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 格式化策略类型
  const formatStrategyType = (type: string) => {
    const typeMap: Record<string, string> = {
      'single_leg': '单腿期权',
      'straddle': '跨式策略',
      'strangle': '宽跨式策略',
      'iron_condor': '铁鹰策略',
      'butterfly': '蝶式策略',
      'custom': '自定义策略'
    }
    return typeMap[type] || type
  }

  // 格式化货币
  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || value === null) return 'N/A'
    return `$${value.toFixed(2)}`
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="策略详情" size="lg">
      <div className="space-y-6">
        {/* 复制策略提示 */}
        {strategy.name.includes('(副本)') && (
          <div className="bg-accent-blue bg-opacity-10 border border-accent-blue border-opacity-30 rounded-lg p-3">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-accent-blue flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-accent-blue">这是一个复制的策略</p>
                <p className="text-xs text-accent-blue-light mt-1">
                  此策略是通过复制功能创建的，包含了原策略的所有参数配置。
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 基本信息 */}
        <div className="bg-bg-secondary rounded-lg p-4">
          <h3 className="text-lg font-semibold text-text-primary mb-4">基本信息</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-text-secondary mb-1">策略名称</p>
              <div className="flex items-center gap-2">
                <p className="text-base text-text-primary font-medium">{strategy.name}</p>
                {strategy.name.includes('(副本)') && (
                  <span className="text-xs px-2 py-0.5 bg-accent-blue bg-opacity-20 text-accent-blue rounded border border-accent-blue border-opacity-30">
                    副本
                  </span>
                )}
              </div>
            </div>
            <div>
              <p className="text-sm text-text-secondary mb-1">策略类型</p>
              <p className="text-base text-text-primary">{formatStrategyType(strategy.strategy_type)}</p>
            </div>
            <div className="col-span-2">
              <p className="text-sm text-text-secondary mb-1">描述</p>
              <p className="text-base text-text-primary">{strategy.description || '无描述'}</p>
            </div>
            <div>
              <p className="text-sm text-text-secondary mb-1">创建时间</p>
              <p className="text-base text-text-primary">{formatDate(strategy.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-text-secondary mb-1">策略ID</p>
              <p className="text-base text-text-primary font-mono text-sm">{strategy.id}</p>
            </div>
          </div>
        </div>

        {/* 风险指标 */}
        <div className="bg-bg-secondary rounded-lg p-4">
          <h3 className="text-lg font-semibold text-text-primary mb-4">风险指标</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-text-secondary mb-1">最大收益</p>
              <p className={`text-lg font-semibold ${
                strategy.max_profit && strategy.max_profit > 0 
                  ? 'text-green-500' 
                  : 'text-text-primary'
              }`}>
                {formatCurrency(strategy.max_profit)}
              </p>
            </div>
            <div>
              <p className="text-sm text-text-secondary mb-1">最大损失</p>
              <p className={`text-lg font-semibold ${
                strategy.max_loss && strategy.max_loss < 0 
                  ? 'text-red-500' 
                  : 'text-text-primary'
              }`}>
                {formatCurrency(strategy.max_loss)}
              </p>
            </div>
            {strategy.initial_cost !== undefined && (
              <div>
                <p className="text-sm text-text-secondary mb-1">初始成本</p>
                <p className="text-base text-text-primary font-medium">
                  {formatCurrency(strategy.initial_cost)}
                </p>
              </div>
            )}
            {strategy.risk_reward_ratio !== undefined && (
              <div>
                <p className="text-sm text-text-secondary mb-1">风险收益比</p>
                <p className="text-base text-text-primary font-medium">
                  {strategy.risk_reward_ratio.toFixed(2)}
                </p>
              </div>
            )}
            {strategy.breakeven_points && strategy.breakeven_points.length > 0 && (
              <div className="col-span-2">
                <p className="text-sm text-text-secondary mb-1">盈亏平衡点</p>
                <p className="text-base text-text-primary font-medium">
                  {strategy.breakeven_points.map(bp => `$${bp.toFixed(2)}`).join(', ')}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* 希腊字母 */}
        {strategy.greeks && (
          <div className="bg-bg-secondary rounded-lg p-4">
            <h3 className="text-lg font-semibold text-text-primary mb-4">希腊字母</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-text-secondary mb-1">Delta (Δ)</p>
                <p className="text-lg font-semibold text-text-primary">
                  {strategy.greeks.delta.toFixed(4)}
                </p>
                <p className="text-xs text-text-secondary mt-1">价格敏感度</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-text-secondary mb-1">Gamma (Γ)</p>
                <p className="text-lg font-semibold text-text-primary">
                  {strategy.greeks.gamma.toFixed(6)}
                </p>
                <p className="text-xs text-text-secondary mt-1">Delta变化率</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-text-secondary mb-1">Theta (Θ)</p>
                <p className="text-lg font-semibold text-text-primary">
                  {strategy.greeks.theta.toFixed(2)}
                </p>
                <p className="text-xs text-text-secondary mt-1">时间衰减</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-text-secondary mb-1">Vega (ν)</p>
                <p className="text-lg font-semibold text-text-primary">
                  {strategy.greeks.vega.toFixed(2)}
                </p>
                <p className="text-xs text-text-secondary mt-1">波动率敏感度</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-text-secondary mb-1">Rho (ρ)</p>
                <p className="text-lg font-semibold text-text-primary">
                  {strategy.greeks.rho.toFixed(2)}
                </p>
                <p className="text-xs text-text-secondary mt-1">利率敏感度</p>
              </div>
            </div>
          </div>
        )}

        {/* 策略腿详情 */}
        {strategy.legs && strategy.legs.length > 0 && (
          <div className="bg-bg-secondary rounded-lg p-4">
            <h3 className="text-lg font-semibold text-text-primary mb-4">策略腿</h3>
            <div className="space-y-3">
              {strategy.legs.map((leg, index) => (
                <div 
                  key={index}
                  className="bg-bg-primary rounded-lg p-3 border border-text-disabled"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-text-primary">
                      腿 {index + 1}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      leg.action === 'buy' 
                        ? 'bg-green-500 bg-opacity-20 text-green-500' 
                        : 'bg-red-500 bg-opacity-20 text-red-500'
                    }`}>
                      {leg.action === 'buy' ? '买入' : '卖出'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-text-secondary">合约: </span>
                      <span className="text-text-primary font-mono">
                        {leg.option_contract.instrument_name}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-secondary">类型: </span>
                      <span className="text-text-primary">
                        {leg.option_contract.option_type === 'call' ? '看涨' : '看跌'}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-secondary">执行价: </span>
                      <span className="text-text-primary font-medium">
                        ${leg.option_contract.strike_price.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-secondary">数量: </span>
                      <span className="text-text-primary font-medium">
                        {leg.quantity}
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-text-secondary">到期日: </span>
                      <span className="text-text-primary">
                        {new Date(leg.option_contract.expiration_date).toLocaleDateString('zh-CN')}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-text-disabled">
          {onCopy && (
            <button
              onClick={handleCopy}
              className="px-4 py-2 bg-bg-secondary text-text-primary rounded-lg hover:bg-opacity-80 transition-colors"
            >
              复制策略
            </button>
          )}
          {onEdit && (
            <button
              onClick={handleEdit}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              编辑策略
            </button>
          )}
          {onDelete && (
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              删除策略
            </button>
          )}
        </div>
      </div>
    </Modal>
  )
}

export default StrategyDetailModal
