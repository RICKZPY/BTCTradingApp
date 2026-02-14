import { useState } from 'react'
import type { StrategyTemplate } from '../../api/types'
import Step1_TemplateSelection from './Step1_TemplateSelection'
import Step2_ParameterConfig from './Step2_ParameterConfig'
import Step3_Confirmation from './Step3_Confirmation'

interface StrategyWizardProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (strategyData: any) => void
  templates: StrategyTemplate[]
  underlyingPrice: number
}

type WizardStep = 1 | 2 | 3

const StrategyWizard = ({ 
  isOpen, 
  onClose, 
  onComplete, 
  templates,
  underlyingPrice 
}: StrategyWizardProps) => {
  const [currentStep, setCurrentStep] = useState<WizardStep>(1)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<any>({
    name: '',
    description: '',
    expiry_date: '',
    quantity: '1',
    strike: '',
    call_strike: '',
    put_strike: '',
    strikes: ['', '', '', ''],
    wing_width: ''
  })

  if (!isOpen) return null

  const handleNext = () => {
    if (currentStep < 3 && canProceed()) {
      setCurrentStep((currentStep + 1) as WizardStep)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((currentStep - 1) as WizardStep)
    }
  }

  const handleComplete = async () => {
    setIsSubmitting(true)
    try {
      await onComplete({
        ...formData,
        strategy_type: selectedTemplate
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  // 验证步骤
  const validateStep = (step: WizardStep): { isValid: boolean; errors: string[] } => {
    const errors: string[] = []
    
    switch (step) {
      case 1:
        if (!selectedTemplate) {
          errors.push('请选择一个策略模板')
        }
        break
      
      case 2:
        // 基本字段验证
        if (!formData.expiry_date) {
          errors.push('请选择到期日')
        } else {
          // 验证到期日不能是过去的日期
          const expiryDate = new Date(formData.expiry_date)
          const today = new Date()
          today.setHours(0, 0, 0, 0)
          if (expiryDate < today) {
            errors.push('到期日不能是过去的日期')
          }
        }
        
        if (!formData.quantity || parseInt(formData.quantity) < 1) {
          errors.push('数量必须至少为1')
        }
        
        // 根据策略类型验证执行价
        switch (selectedTemplate) {
          case 'single_leg':
          case 'straddle':
            if (!formData.strike) {
              errors.push('请选择执行价')
            } else if (parseFloat(formData.strike) <= 0) {
              errors.push('执行价必须大于0')
            }
            break
          
          case 'strangle':
            if (!formData.call_strike) {
              errors.push('请选择看涨期权执行价')
            } else if (parseFloat(formData.call_strike) <= 0) {
              errors.push('看涨期权执行价必须大于0')
            }
            
            if (!formData.put_strike) {
              errors.push('请选择看跌期权执行价')
            } else if (parseFloat(formData.put_strike) <= 0) {
              errors.push('看跌期权执行价必须大于0')
            }
            
            // 验证宽跨式执行价顺序：看跌执行价应该低于看涨执行价
            if (formData.call_strike && formData.put_strike) {
              const callStrike = parseFloat(formData.call_strike)
              const putStrike = parseFloat(formData.put_strike)
              if (putStrike >= callStrike) {
                errors.push('宽跨式策略中，看跌期权执行价应低于看涨期权执行价')
              }
            }
            break
          
          case 'iron_condor':
            if (!formData.strikes.every((s: string) => s !== '')) {
              errors.push('请选择所有4个执行价')
            } else {
              // 验证铁鹰执行价顺序：必须从低到高
              const strikes = formData.strikes.map((s: string) => parseFloat(s))
              if (strikes.some((s: number) => s <= 0)) {
                errors.push('所有执行价必须大于0')
              } else {
                for (let i = 0; i < strikes.length - 1; i++) {
                  if (strikes[i] >= strikes[i + 1]) {
                    errors.push('铁鹰策略的执行价必须按从低到高的顺序排列')
                    break
                  }
                }
              }
            }
            break
          
          case 'butterfly':
            if (!formData.strike) {
              errors.push('请选择中心执行价')
            } else if (parseFloat(formData.strike) <= 0) {
              errors.push('中心执行价必须大于0')
            }
            
            if (!formData.wing_width) {
              errors.push('请输入翼宽')
            } else if (parseFloat(formData.wing_width) <= 0) {
              errors.push('翼宽必须大于0')
            }
            break
          
          default:
            errors.push('未知的策略类型')
        }
        break
      
      case 3:
        // 步骤3没有额外验证，只是确认
        break
      
      default:
        errors.push('无效的步骤')
    }
    
    return {
      isValid: errors.length === 0,
      errors
    }
  }

  const canProceed = () => {
    return validateStep(currentStep).isValid
  }

  // 获取当前步骤的验证错误
  const getValidationErrors = () => {
    return validateStep(currentStep).errors
  }

  const getSelectedTemplateName = () => {
    const template = templates.find(t => t.type === selectedTemplate)
    return template?.name || ''
  }

  // 获取帮助提示
  const getStepHelp = () => {
    switch (currentStep) {
      case 1:
        return {
          title: '选择策略模板',
          text: '根据您的市场预期选择合适的期权策略。每个策略都有不同的风险收益特征，适用于不同的市场环境。',
          tips: [
            '看涨市场：考虑单腿看涨期权',
            '高波动预期：考虑跨式或宽跨式策略',
            '低波动预期：考虑铁鹰或蝶式策略'
          ]
        }
      case 2:
        return {
          title: '配置参数',
          text: '设置策略的具体参数。系统会自动加载实时市场数据帮助您做出决策。',
          tips: [
            '到期日：选择符合您交易周期的到期日',
            '执行价：使用智能选择器查看实时价格和隐含波动率',
            '数量：根据您的风险承受能力设置合约数量'
          ]
        }
      case 3:
        return {
          title: '确认创建',
          text: '仔细检查所有参数，确保策略配置符合您的预期。创建后可以随时编辑或删除。',
          tips: [
            '检查所有执行价是否正确',
            '确认到期日和数量',
            '理解策略的风险特征'
          ]
        }
      default:
        return {
          title: '',
          text: '',
          tips: []
        }
    }
  }

  const stepHelp = getStepHelp()

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-bg-primary rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* 头部 */}
        <div className="px-6 py-4 border-b border-text-disabled">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-text-primary">创建策略向导</h2>
            <button
              onClick={onClose}
              className="text-text-secondary hover:text-text-primary transition-colors"
              title="关闭向导"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* 步骤指示器 */}
          <div className="mt-6 flex items-center justify-between">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center flex-1">
                <div className="flex items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                      currentStep >= step
                        ? 'bg-accent-blue text-white'
                        : 'bg-bg-secondary text-text-secondary'
                    }`}
                  >
                    {step}
                  </div>
                  <div className="ml-3">
                    <div className={`text-sm font-medium ${
                      currentStep >= step ? 'text-text-primary' : 'text-text-secondary'
                    }`}>
                      {step === 1 && '选择模板'}
                      {step === 2 && '配置参数'}
                      {step === 3 && '确认创建'}
                    </div>
                  </div>
                </div>
                {step < 3 && (
                  <div className={`flex-1 h-0.5 mx-4 ${
                    currentStep > step ? 'bg-accent-blue' : 'bg-text-disabled'
                  }`} />
                )}
              </div>
            ))}
          </div>

          {/* 帮助提示 */}
          <div className="mt-4 p-4 bg-accent-blue bg-opacity-10 rounded-lg border border-accent-blue border-opacity-30">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-accent-blue flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-accent-blue mb-1">{stepHelp.title}</h4>
                <p className="text-sm text-accent-blue-light mb-2">{stepHelp.text}</p>
                {stepHelp.tips.length > 0 && (
                  <ul className="space-y-1 mt-2">
                    {stepHelp.tips.map((tip, index) => (
                      <li key={index} className="text-xs text-accent-blue-light flex items-start gap-2">
                        <svg className="w-3 h-3 text-accent-blue mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                        </svg>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {currentStep === 1 && (
            <Step1_TemplateSelection
              templates={templates}
              selectedTemplate={selectedTemplate}
              onSelect={setSelectedTemplate}
            />
          )}

          {currentStep === 2 && (
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                配置策略参数
              </h3>
              <p className="text-text-secondary text-sm mb-6">
                为您的 {getSelectedTemplateName()} 策略设置具体参数
              </p>
              <Step2_ParameterConfig
                selectedTemplate={selectedTemplate}
                formData={formData}
                setFormData={setFormData}
                underlyingPrice={underlyingPrice}
              />
            </div>
          )}

          {currentStep === 3 && (
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                确认并创建
              </h3>
              <p className="text-text-secondary text-sm mb-6">
                请仔细检查您的策略配置
              </p>
              <Step3_Confirmation
                selectedTemplate={selectedTemplate}
                formData={formData}
                templateName={getSelectedTemplateName()}
                onSubmit={handleComplete}
                isSubmitting={isSubmitting}
              />
            </div>
          )}
          
          {/* 验证错误显示 */}
          {!canProceed() && currentStep !== 3 && (
            <div className="mt-6 p-4 bg-accent-red bg-opacity-10 border border-accent-red border-opacity-30 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-accent-red mb-2">请完成以下项目：</h4>
                  <ul className="space-y-1">
                    {getValidationErrors().map((error, index) => (
                      <li key={index} className="text-sm text-accent-red-light">
                        • {error}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        {currentStep !== 3 && (
          <div className="px-6 py-4 border-t border-text-disabled flex justify-between">
            <button
              onClick={currentStep === 1 ? onClose : handleBack}
              className="btn btn-secondary"
              disabled={isSubmitting}
            >
              {currentStep === 1 ? '取消' : '上一步'}
            </button>
            <button
              onClick={handleNext}
              className="btn btn-primary"
              disabled={!canProceed() || isSubmitting}
            >
              下一步
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default StrategyWizard
