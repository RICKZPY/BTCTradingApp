import { useState } from 'react'
import type { StrategyTemplate } from '../../api/types'
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
  const validateStep = (step: WizardStep): boolean => {
    switch (step) {
      case 1:
        return selectedTemplate !== ''
      
      case 2:
        // 基本字段验证
        if (!formData.expiry_date || !formData.quantity) {
          return false
        }
        
        // 根据策略类型验证执行价
        switch (selectedTemplate) {
          case 'single_leg':
          case 'straddle':
            return formData.strike !== ''
          
          case 'strangle':
            return formData.call_strike !== '' && formData.put_strike !== ''
          
          case 'iron_condor':
            return formData.strikes.every((s: string) => s !== '')
          
          case 'butterfly':
            return formData.strike !== '' && formData.wing_width !== ''
          
          default:
            return false
        }
      
      case 3:
        return true
      
      default:
        return false
    }
  }

  const canProceed = () => {
    return validateStep(currentStep)
  }

  const getSelectedTemplateName = () => {
    const template = templates.find(t => t.type === selectedTemplate)
    return template?.name || ''
  }

  // 获取帮助提示
  const getStepHelp = () => {
    switch (currentStep) {
      case 1:
        return '选择最适合您交易目标和市场预期的策略类型'
      case 2:
        return '设置策略的具体参数，包括到期日、执行价和数量'
      case 3:
        return '仔细检查策略配置，确认无误后创建'
      default:
        return ''
    }
  }

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
          <div className="mt-4 flex items-start gap-2 p-3 bg-accent-blue bg-opacity-10 rounded-lg border border-accent-blue border-opacity-30">
            <svg className="w-5 h-5 text-accent-blue flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-accent-blue-light">{getStepHelp()}</p>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {currentStep === 1 && (
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                选择策略模板
              </h3>
              <p className="text-text-secondary text-sm mb-6">
                选择一个适合您交易目标的期权策略模板
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map((template) => (
                  <div
                    key={template.type}
                    onClick={() => setSelectedTemplate(template.type)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedTemplate === template.type
                        ? 'border-accent-blue bg-accent-blue bg-opacity-10'
                        : 'border-text-disabled hover:border-accent-blue hover:border-opacity-50'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-lg font-semibold text-text-primary">
                        {template.name}
                      </h4>
                      {selectedTemplate === template.type && (
                        <svg className="w-6 h-6 text-accent-blue" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                    <p className="text-text-secondary text-sm">
                      {template.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
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
