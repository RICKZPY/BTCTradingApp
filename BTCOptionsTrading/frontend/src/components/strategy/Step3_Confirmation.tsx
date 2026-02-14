import { useState } from 'react'
import type { ValidationResult, RiskMetrics } from '../../api/types'

interface Step3Props {
  selectedTemplate: string
  formData: any
  templateName: string
  onSubmit: () => void
  isSubmitting: boolean
  validationResult: ValidationResult | null
  riskMetrics: RiskMetrics | null
  isValidating: boolean
  isCalculatingRisk: boolean
}

const Step3_Confirmation = ({ 
  selectedTemplate, 
  formData, 
  templateName,
  onSubmit,
  isSubmitting,
  validationResult,
  riskMetrics,
  isValidating,
  isCalculatingRisk
}: Step3Props) => {
  const [showHighRiskConfirm, setShowHighRiskConfirm] = useState(false)
  
  // 检查是否有高风险警告
  const hasHighRiskWarnings = () => {
    if (!validationResult || !validationResult.warnings) return false
    
    // 检查是否有高风险相关的警告
    return validationResult.warnings.some(warning => 
      warning.message.includes('高风险') || 
      warning.message.includes('超过') ||
      warning.message.includes('无限损失') ||
      warning.message.includes('风险较大')
    )
  }

  // 处理提交
  const handleSubmit = () => {
    // 如果有高风险警告且未确认，显示确认对话框
    if (hasHighRiskWarnings() && !showHighRiskConfirm) {
      setShowHighRiskConfirm(true)
      return
    }
    
    // 否则直接提交
    onSubmit()
  }

  // 确认高风险并提交
  const confirmHighRiskAndSubmit = () => {
    setShowHighRiskConfirm(false)
    onSubmit()
  }
  
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

      {/* 风险指标预览 */}
      {isCalculatingRisk && (
        <div className="bg-bg-secondary rounded-lg p-4 border border-text-disabled">
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-blue mx-auto mb-3"></div>
              <p className="text-sm text-text-secondary">正在计算风险指标...</p>
            </div>
          </div>
        </div>
      )}

      {!isCalculatingRisk && riskMetrics && (
        <div className="bg-bg-secondary rounded-lg p-4 border border-text-disabled">
          <h4 className="text-lg font-semibold text-text-primary mb-4">风险指标预览</h4>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-3 bg-bg-primary rounded border border-text-disabled">
              <div className="text-xs text-text-secondary mb-1">初始成本</div>
              <div className="text-lg font-semibold text-text-primary">
                ${riskMetrics.initial_cost.toFixed(2)}
              </div>
            </div>
            
            <div className="p-3 bg-bg-primary rounded border border-text-disabled">
              <div className="text-xs text-text-secondary mb-1">风险收益比</div>
              <div className="text-lg font-semibold text-text-primary">
                {riskMetrics.risk_reward_ratio.toFixed(2)}
              </div>
            </div>
            
            <div className="p-3 bg-bg-primary rounded border border-accent-green border-opacity-30">
              <div className="text-xs text-text-secondary mb-1">最大收益</div>
              <div className="text-lg font-semibold text-accent-green">
                ${riskMetrics.max_profit === Infinity ? '无限' : riskMetrics.max_profit.toFixed(2)}
              </div>
            </div>
            
            <div className="p-3 bg-bg-primary rounded border border-accent-red border-opacity-30">
              <div className="text-xs text-text-secondary mb-1">最大损失</div>
              <div className="text-lg font-semibold text-accent-red">
                ${riskMetrics.max_loss === Infinity ? '无限' : Math.abs(riskMetrics.max_loss).toFixed(2)}
              </div>
            </div>
          </div>

          {riskMetrics.breakeven_points && riskMetrics.breakeven_points.length > 0 && (
            <div className="p-3 bg-bg-primary rounded border border-text-disabled mb-4">
              <div className="text-xs text-text-secondary mb-2">盈亏平衡点</div>
              <div className="flex flex-wrap gap-2">
                {riskMetrics.breakeven_points.map((point, index) => (
                  <span key={index} className="px-3 py-1 bg-accent-blue bg-opacity-20 text-accent-blue rounded text-sm font-mono">
                    ${point.toFixed(2)}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="p-3 bg-bg-primary rounded border border-text-disabled">
            <div className="text-xs text-text-secondary mb-3">希腊字母</div>
            <div className="grid grid-cols-5 gap-3">
              <div className="text-center">
                <div className="text-xs text-text-secondary mb-1">Delta</div>
                <div className="text-sm font-mono text-text-primary">{riskMetrics.greeks.delta.toFixed(4)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-text-secondary mb-1">Gamma</div>
                <div className="text-sm font-mono text-text-primary">{riskMetrics.greeks.gamma.toFixed(4)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-text-secondary mb-1">Theta</div>
                <div className="text-sm font-mono text-text-primary">{riskMetrics.greeks.theta.toFixed(4)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-text-secondary mb-1">Vega</div>
                <div className="text-sm font-mono text-text-primary">{riskMetrics.greeks.vega.toFixed(4)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-text-secondary mb-1">Rho</div>
                <div className="text-sm font-mono text-text-primary">{riskMetrics.greeks.rho.toFixed(4)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 验证警告 */}
      {validationResult && validationResult.warnings.length > 0 && (
        <div className="bg-yellow-900 bg-opacity-20 border border-yellow-600 border-opacity-30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <h5 className="text-sm font-semibold text-yellow-200 mb-2">风险警告</h5>
              <ul className="space-y-1">
                {validationResult.warnings.map((warning, index) => (
                  <li key={index} className="text-sm text-yellow-100">
                    • {warning.message}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 验证错误 */}
      {validationResult && validationResult.errors.length > 0 && (
        <div className="bg-accent-red bg-opacity-10 border border-accent-red border-opacity-30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 text-accent-red flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h5 className="text-sm font-semibold text-accent-red mb-2">配置错误</h5>
              <ul className="space-y-1">
                {validationResult.errors.map((error, index) => (
                  <li key={index} className="text-sm text-accent-red-light">
                    • {error.message}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

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
          onClick={handleSubmit}
          disabled={isSubmitting || isValidating || (validationResult !== null && validationResult.errors.length > 0)}
          className="btn btn-primary px-8"
        >
          {isSubmitting ? '创建中...' : '确认创建策略'}
        </button>
      </div>

      {/* 高风险确认对话框 */}
      {showHighRiskConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-bg-primary rounded-lg shadow-xl max-w-md w-full p-6 border-2 border-accent-red">
            <div className="flex items-start gap-4 mb-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-accent-red bg-opacity-20 flex items-center justify-center">
                <svg className="w-6 h-6 text-accent-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-accent-red mb-2">高风险策略警告</h3>
                <p className="text-sm text-text-primary mb-4">
                  您的策略配置包含以下高风险因素：
                </p>
                <ul className="space-y-2 mb-4">
                  {validationResult?.warnings.map((warning, index) => (
                    <li key={index} className="text-sm text-text-secondary flex items-start gap-2">
                      <svg className="w-4 h-4 text-accent-red flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      <span>{warning.message}</span>
                    </li>
                  ))}
                </ul>
                <div className="p-3 bg-accent-red bg-opacity-10 rounded-lg border border-accent-red border-opacity-30 mb-4">
                  <p className="text-xs text-accent-red-light">
                    <strong>重要提示：</strong> 高风险策略可能导致重大损失。请确保您完全理解该策略的风险特征，并且只投入您能够承受损失的资金。
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowHighRiskConfirm(false)}
                className="flex-1 btn btn-secondary"
                disabled={isSubmitting}
              >
                取消
              </button>
              <button
                onClick={confirmHighRiskAndSubmit}
                className="flex-1 btn bg-accent-red hover:bg-accent-red-light text-white"
                disabled={isSubmitting}
              >
                我理解风险，继续创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Step3_Confirmation
