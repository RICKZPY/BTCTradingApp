import type { StrategyTemplate } from '../../api/types'
import PayoffDiagram from './PayoffDiagram'

interface Step1Props {
  templates: StrategyTemplate[]
  selectedTemplate: string
  onSelect: (templateType: string) => void
}

const Step1_TemplateSelection = ({ 
  templates, 
  selectedTemplate, 
  onSelect 
}: Step1Props) => {
  return (
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
            onClick={() => onSelect(template.type)}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all group relative overflow-hidden ${
              selectedTemplate === template.type
                ? 'border-accent-blue bg-accent-blue bg-opacity-10'
                : 'border-text-disabled hover:border-accent-blue hover:border-opacity-50'
            }`}
          >
            {/* 基本信息 */}
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-lg font-semibold text-text-primary flex-1">
                  {template.name}
                </h4>
                <div className="flex items-center gap-2">
                  {/* 收益曲线图示 */}
                  <div className="ml-2">
                    <PayoffDiagram strategyType={template.type} width={60} height={30} />
                  </div>
                  {selectedTemplate === template.type && (
                    <svg className="w-6 h-6 text-accent-blue" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </div>
              
              <p className="text-text-secondary text-sm mb-3">
                {template.description}
              </p>
              
              {/* 市场条件标签 */}
              {template.market_condition && (
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs px-2 py-1 bg-accent-blue bg-opacity-20 text-accent-blue rounded">
                    {template.market_condition}
                  </span>
                </div>
              )}
              
              {/* 关键特点 */}
              {template.key_features && template.key_features.length > 0 && (
                <div className="mt-3">
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
                      title="查看详细说明"
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
          </div>
        ))}
      </div>
    </div>
  )
}

export default Step1_TemplateSelection
