interface Step3Props {
  selectedTemplate: string
  formData: any
  templateName: string
  onSubmit: () => void
  isSubmitting: boolean
}

const Step3_Confirmation = ({ 
  selectedTemplate, 
  formData, 
  templateName,
  onSubmit,
  isSubmitting 
}: Step3Props) => {
  
  // 格式化执行价显示
  const formatStrike = (strike: string | number) => {
    if (!strike) return '-'
    return `$${parseFloat(strike.toString()).toLocaleString()}`
  }

  // 获取策略腿的摘要
  const getStrategyLegs = () => {
    const quantity = parseInt(formData.quantity) || 1
    
    switch (selectedTemplate) {
      case 'single_leg':
        return [
          { type: '看涨期权', action: '买入', strike: formData.strike, quantity }
        ]
      
      case 'straddle':
        return [
          { type: '看涨期权', action: '买入', strike: formData.strike, quantity },
          { type: '看跌期权', action: '买入', strike: formData.strike, quantity }
        ]
      
      case 'strangle':
        return [
          { type: '看涨期权', action: '买入', strike: formData.call_strike, quantity },
          { type: '看跌期权', action: '买入', strike: formData.put_strike, quantity }
        ]
      
      case 'iron_condor':
        return [
          { type: '看跌期权', action: '买入', strike: formData.strikes[0], quantity },
          { type: '看跌期权', action: '卖出', strike: formData.strikes[1], quantity },
          { type: '看涨期权', action: '卖出', strike: formData.strikes[2], quantity },
          { type: '看涨期权', action: '买入', strike: formData.strikes[3], quantity }
        ]
      
      case 'butterfly':
        const centerStrike = parseFloat(formData.strike)
        const wingWidth = parseFloat(formData.wing_width)
        return [
          { type: '看涨期权', action: '买入', strike: (centerStrike - wingWidth).toString(), quantity },
          { type: '看涨期权', action: '卖出', strike: formData.strike, quantity: quantity * 2 },
          { type: '看涨期权', action: '买入', strike: (centerStrike + wingWidth).toString(), quantity }
        ]
      
      default:
        return []
    }
  }

  const legs = getStrategyLegs()

  return (
    <div className="space-y-6">
      {/* 策略摘要 */}
      <div className="bg-bg-secondary rounded-lg p-4 border border-text-disabled">
        <h4 className="text-lg font-semibold text-text-primary mb-4">策略摘要</h4>
        
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-text-secondary">策略类型:</span>
            <span className="text-text-primary font-medium">{templateName}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-text-secondary">策略名称:</span>
            <span className="text-text-primary font-medium">
              {formData.name || `${templateName} 策略`}
            </span>
          </div>
          
          {formData.description && (
            <div className="flex justify-between">
              <span className="text-text-secondary">描述:</span>
              <span className="text-text-primary">{formData.description}</span>
            </div>
          )}
          
          <div className="flex justify-between">
            <span className="text-text-secondary">到期日:</span>
            <span className="text-text-primary font-medium">
              {new Date(formData.expiry_date).toLocaleDateString('zh-CN')}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-text-secondary">数量:</span>
            <span className="text-text-primary font-medium">{formData.quantity}</span>
          </div>
        </div>
      </div>

      {/* 策略腿详情 */}
      <div className="bg-bg-secondary rounded-lg p-4 border border-text-disabled">
        <h4 className="text-lg font-semibold text-text-primary mb-4">策略腿配置</h4>
        
        <div className="space-y-2">
          {legs.map((leg, index) => (
            <div 
              key={index}
              className="flex items-center justify-between p-3 bg-bg-primary rounded border border-text-disabled"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-text-secondary">
                  腿 {index + 1}
                </span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  leg.action === '买入' 
                    ? 'bg-accent-green bg-opacity-20 text-accent-green' 
                    : 'bg-accent-red bg-opacity-20 text-accent-red'
                }`}>
                  {leg.action}
                </span>
                <span className="text-sm text-text-primary">
                  {leg.type}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-text-secondary">
                  执行价: <span className="text-text-primary font-mono">{formatStrike(leg.strike)}</span>
                </span>
                <span className="text-sm text-text-secondary">
                  数量: <span className="text-text-primary">{leg.quantity}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 风险提示 */}
      <div className="bg-yellow-900 bg-opacity-20 border border-yellow-600 border-opacity-30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <h5 className="text-sm font-semibold text-yellow-200 mb-2">风险提示</h5>
            <p className="text-sm text-yellow-100">
              期权交易具有高风险，可能导致全部本金损失。请确保您完全理解该策略的风险特征，并在创建前仔细检查所有参数。
            </p>
          </div>
        </div>
      </div>

      {/* 确认按钮 */}
      <div className="flex justify-center pt-4">
        <button
          onClick={onSubmit}
          disabled={isSubmitting}
          className="btn btn-primary px-8"
        >
          {isSubmitting ? '创建中...' : '确认创建策略'}
        </button>
      </div>
    </div>
  )
}

export default Step3_Confirmation
