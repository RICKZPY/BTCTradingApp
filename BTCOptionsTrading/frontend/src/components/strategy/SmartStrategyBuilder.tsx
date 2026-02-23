import { useState, useEffect } from 'react'
import { smartStrategyApi } from '../../api/smartStrategy'
import LoadingSpinner from '../LoadingSpinner'

interface SmartLeg {
  option_type: 'call' | 'put'
  action: 'buy' | 'sell'
  quantity: number
  relative_expiry: string
  relative_strike: string
}

interface SmartStrategyBuilderProps {
  onStrategyBuilt: (strategy: any) => void
  onCancel: () => void
}

const SmartStrategyBuilder = ({ onStrategyBuilt, onCancel }: SmartStrategyBuilderProps) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [strategyType, setStrategyType] = useState('single_leg')
  const [legs, setLegs] = useState<SmartLeg[]>([{
    option_type: 'call',
    action: 'buy',
    quantity: 1,
    relative_expiry: 'T+7',
    relative_strike: 'ATM'
  }])
  
  const [expiries, setExpiries] = useState<any[]>([])
  const [strikes, setStrikes] = useState<any[]>([])
  const [templates, setTemplates] = useState<any[]>([])
  const [preview, setPreview] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isBuilding, setIsBuilding] = useState(false)

  useEffect(() => {
    loadOptions()
    loadTemplates()
  }, [])

  const loadOptions = async () => {
    try {
      const [expiriesData, strikesData] = await Promise.all([
        smartStrategyApi.getRelativeExpiries(),
        smartStrategyApi.getRelativeStrikes()
      ])
      setExpiries(expiriesData.expiries)
      setStrikes(strikesData.strikes)
    } catch (error) {
      console.error('加载选项失败:', error)
    }
  }

  const loadTemplates = async () => {
    try {
      const data = await smartStrategyApi.getTemplates()
      setTemplates(data.templates)
    } catch (error) {
      console.error('加载模板失败:', error)
    }
  }

  const loadPreview = async (legIndex: number) => {
    const leg = legs[legIndex]
    try {
      setIsLoading(true)
      const data = await smartStrategyApi.preview(
        leg.option_type,
        leg.relative_expiry,
        leg.relative_strike
      )
      setPreview(data)
    } catch (error) {
      console.error('预览失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const addLeg = () => {
    setLegs([...legs, {
      option_type: 'call',
      action: 'buy',
      quantity: 1,
      relative_expiry: 'T+7',
      relative_strike: 'ATM'
    }])
  }

  const removeLeg = (index: number) => {
    setLegs(legs.filter((_, i) => i !== index))
  }

  const updateLeg = (index: number, field: keyof SmartLeg, value: any) => {
    const newLegs = [...legs]
    newLegs[index] = { ...newLegs[index], [field]: value }
    setLegs(newLegs)
    
    // 自动预览第一个腿
    if (index === 0) {
      loadPreview(0)
    }
  }

  const loadTemplate = async (templateId: string) => {
    try {
      setIsBuilding(true)
      const strategy = await smartStrategyApi.buildFromTemplate(templateId)
      onStrategyBuilt(strategy)
    } catch (error) {
      console.error('从模板构建失败:', error)
      alert('构建失败: ' + (error as Error).message)
    } finally {
      setIsBuilding(false)
    }
  }

  const buildStrategy = async () => {
    if (!name.trim()) {
      alert('请输入策略名称')
      return
    }

    try {
      setIsBuilding(true)
      const strategy = await smartStrategyApi.build({
        name,
        description,
        strategy_type: strategyType,
        legs,
        underlying: 'BTC'
      })
      onStrategyBuilt(strategy)
    } catch (error) {
      console.error('构建策略失败:', error)
      alert('构建失败: ' + (error as Error).message)
    } finally {
      setIsBuilding(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 预定义模板 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3">快速开始 - 使用模板</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {templates.map((template) => (
            <button
              key={template.id}
              onClick={() => loadTemplate(template.id)}
              disabled={isBuilding}
              className="bg-gray-700 hover:bg-gray-600 p-3 rounded text-left transition-colors disabled:opacity-50"
            >
              <div className="font-medium">{template.name}</div>
              <div className="text-sm text-gray-400 mt-1">{template.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 自定义策略 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">自定义策略</h3>
        
        {/* 基本信息 */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium mb-2">策略名称</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              placeholder="例如：周度看涨策略"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">描述</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              rows={2}
              placeholder="策略说明..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">策略类型</label>
            <select
              value={strategyType}
              onChange={(e) => setStrategyType(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
            >
              <option value="single_leg">单腿</option>
              <option value="straddle">跨式</option>
              <option value="strangle">宽跨式</option>
              <option value="custom">自定义</option>
            </select>
          </div>
        </div>

        {/* 策略腿 */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="font-medium">策略腿配置</h4>
            <button
              onClick={addLeg}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
            >
              + 添加腿
            </button>
          </div>

          {legs.map((leg, index) => (
            <div key={index} className="bg-gray-700 rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">腿 #{index + 1}</span>
                {legs.length > 1 && (
                  <button
                    onClick={() => removeLeg(index)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    删除
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div>
                  <label className="block text-xs mb-1">期权类型</label>
                  <select
                    value={leg.option_type}
                    onChange={(e) => updateLeg(index, 'option_type', e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-sm"
                  >
                    <option value="call">看涨</option>
                    <option value="put">看跌</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs mb-1">操作</label>
                  <select
                    value={leg.action}
                    onChange={(e) => updateLeg(index, 'action', e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-sm"
                  >
                    <option value="buy">买入</option>
                    <option value="sell">卖出</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs mb-1">数量</label>
                  <input
                    type="number"
                    value={leg.quantity}
                    onChange={(e) => updateLeg(index, 'quantity', parseInt(e.target.value))}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-sm"
                    min="1"
                  />
                </div>

                <div>
                  <label className="block text-xs mb-1">到期日</label>
                  <select
                    value={leg.relative_expiry}
                    onChange={(e) => updateLeg(index, 'relative_expiry', e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-sm"
                  >
                    {expiries.map((exp) => (
                      <option key={exp.value} value={exp.value}>
                        {exp.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs mb-1">行权价</label>
                  <select
                    value={leg.relative_strike}
                    onChange={(e) => updateLeg(index, 'relative_strike', e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-sm"
                  >
                    {strikes.map((strike) => (
                      <option key={strike.value} value={strike.value}>
                        {strike.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* 预览 */}
              {index === 0 && preview && (
                <div className="mt-3 p-3 bg-gray-600 rounded text-sm">
                  <div className="font-medium mb-2">实时预览:</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>合约: {preview.instrument_name}</div>
                    <div>行权价: ${preview.strike_price?.toLocaleString()}</div>
                    <div>当前价: {preview.current_price?.toFixed(4)} BTC</div>
                    <div>Delta: {preview.delta?.toFixed(3)}</div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={buildStrategy}
            disabled={isBuilding || !name.trim()}
            className="flex-1 bg-green-600 hover:bg-green-700 px-4 py-2 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isBuilding ? <LoadingSpinner size="sm" /> : '构建策略'}
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  )
}

export default SmartStrategyBuilder
