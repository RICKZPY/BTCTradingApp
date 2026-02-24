import { useState } from 'react'
import { quickTradingApi } from '../../api/quickTrading'
import type { Strategy } from '../../api/types'
import LoadingSpinner from '../LoadingSpinner'

interface QuickTradingModalProps {
  strategy: Strategy
  onClose: () => void
  onSuccess: () => void
}

const QuickTradingModal = ({ strategy, onClose, onSuccess }: QuickTradingModalProps) => {
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [testMode, setTestMode] = useState(true)
  const [isExecuting, setIsExecuting] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<{
    tested: boolean
    success: boolean
    message: string
  } | null>(null)
  const [executionResult, setExecutionResult] = useState<any>(null)

  const handleTestConnection = async () => {
    if (!apiKey || !apiSecret) {
      alert('请输入API密钥和密钥')
      return
    }

    try {
      setIsTesting(true)
      setConnectionStatus(null)
      
      const result = await quickTradingApi.testConnection(apiKey, apiSecret, testMode)
      
      setConnectionStatus({
        tested: true,
        success: result.success,
        message: result.message
      })
    } catch (error) {
      setConnectionStatus({
        tested: true,
        success: false,
        message: error instanceof Error ? error.message : '连接测试失败'
      })
    } finally {
      setIsTesting(false)
    }
  }

  const handleExecute = async () => {
    if (!apiKey || !apiSecret) {
      alert('请输入API密钥和密钥')
      return
    }

    if (!connectionStatus?.success) {
      alert('请先测试API连接')
      return
    }

    if (!confirm(`确定要立即执行策略 "${strategy.name}" 吗？\n\n${testMode ? '⚠️ 当前使用测试网' : '⚠️⚠️⚠️ 当前使用真实资金！'}`)) {
      return
    }

    try {
      setIsExecuting(true)
      setExecutionResult(null)
      
      const result = await quickTradingApi.execute({
        strategy_id: strategy.id,
        test_mode: testMode,
        api_key: apiKey,
        api_secret: apiSecret
      })
      
      setExecutionResult(result)
      
      if (result.success) {
        alert('交易执行成功！')
        onSuccess()
      }
    } catch (error) {
      alert('执行失败: ' + (error instanceof Error ? error.message : '未知错误'))
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 策略信息 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3">策略信息</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">策略名称:</span>
            <span className="font-medium">{strategy.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">策略类型:</span>
            <span>{strategy.strategy_type}</span>
          </div>
          {strategy.legs && (
            <div className="flex justify-between">
              <span className="text-gray-400">策略腿数:</span>
              <span>{strategy.legs.length}</span>
            </div>
          )}
        </div>
      </div>

      {/* API配置 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3">API配置</h3>
        
        <div className="space-y-4">
          {/* 测试模式切换 */}
          <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
            <div>
              <div className="font-medium">
                {testMode ? '🧪 测试网模式' : '💰 真实交易模式'}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {testMode ? '使用测试网，不会使用真实资金' : '⚠️ 使用真实资金交易！'}
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={testMode}
                onChange={(e) => {
                  setTestMode(e.target.checked)
                  setConnectionStatus(null)
                }}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* API密钥 */}
          <div>
            <label className="block text-sm font-medium mb-2">
              API Key *
            </label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value)
                setConnectionStatus(null)
              }}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              placeholder="输入Deribit API Key"
            />
          </div>

          {/* API密钥 */}
          <div>
            <label className="block text-sm font-medium mb-2">
              API Secret *
            </label>
            <input
              type="password"
              value={apiSecret}
              onChange={(e) => {
                setApiSecret(e.target.value)
                setConnectionStatus(null)
              }}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              placeholder="输入Deribit API Secret"
            />
          </div>

          {/* 测试连接按钮 */}
          <button
            onClick={handleTestConnection}
            disabled={isTesting || !apiKey || !apiSecret}
            className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isTesting ? <LoadingSpinner size="sm" /> : '测试连接'}
          </button>

          {/* 连接状态 */}
          {connectionStatus && (
            <div className={`p-3 rounded ${
              connectionStatus.success 
                ? 'bg-green-900 bg-opacity-20 border border-green-600 border-opacity-30' 
                : 'bg-red-900 bg-opacity-20 border border-red-600 border-opacity-30'
            }`}>
              <div className="flex items-center gap-2">
                {connectionStatus.success ? (
                  <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                <span className={connectionStatus.success ? 'text-green-200' : 'text-red-200'}>
                  {connectionStatus.message}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 执行结果 */}
      {executionResult && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3">执行结果</h3>
          
          <div className={`p-3 rounded mb-3 ${
            executionResult.success 
              ? 'bg-green-900 bg-opacity-20 border border-green-600 border-opacity-30' 
              : 'bg-red-900 bg-opacity-20 border border-red-600 border-opacity-30'
          }`}>
            <div className="font-medium mb-1">
              {executionResult.success ? '✓ 执行成功' : '✗ 执行失败'}
            </div>
            <div className="text-sm text-gray-300">{executionResult.message}</div>
          </div>

          {executionResult.orders && executionResult.orders.length > 0 && (
            <div className="space-y-2">
              <div className="text-sm font-medium">订单详情:</div>
              {executionResult.orders.map((order: any, index: number) => (
                <div key={index} className="bg-gray-700 rounded p-3 text-sm">
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">合约:</span>
                    <span className="font-mono">{order.instrument_name}</span>
                  </div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">方向:</span>
                    <span className={order.side === 'buy' ? 'text-green-400' : 'text-red-400'}>
                      {order.side === 'buy' ? '买入' : '卖出'}
                    </span>
                  </div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">数量:</span>
                    <span>{order.amount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">价格:</span>
                    <span className="font-mono">{order.price} BTC</span>
                  </div>
                  {order.order_id && (
                    <div className="flex justify-between mt-1 pt-1 border-t border-gray-600">
                      <span className="text-gray-400">订单ID:</span>
                      <span className="font-mono text-xs">{order.order_id}</span>
                    </div>
                  )}
                </div>
              ))}
              
              <div className="bg-gray-700 rounded p-3 text-sm font-medium">
                <div className="flex justify-between">
                  <span>总成本:</span>
                  <span className="text-lg">{executionResult.total_cost.toFixed(4)} BTC</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex gap-3">
        <button
          onClick={handleExecute}
          disabled={isExecuting || !connectionStatus?.success}
          className="flex-1 bg-green-600 hover:bg-green-700 px-4 py-3 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExecuting ? <LoadingSpinner size="sm" /> : '⚡ 立即执行'}
        </button>
        <button
          onClick={onClose}
          className="px-4 py-3 bg-gray-600 hover:bg-gray-500 rounded"
        >
          {executionResult ? '关闭' : '取消'}
        </button>
      </div>

      {/* 风险提示 */}
      <div className="bg-yellow-900 bg-opacity-20 border border-yellow-600 border-opacity-30 rounded p-3">
        <div className="flex items-start gap-2">
          <svg className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="text-sm text-yellow-200">
            <div className="font-medium mb-1">风险提示</div>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>快速交易将立即执行，无法撤销</li>
              <li>请确保在测试网充分测试后再使用真实资金</li>
              <li>市场价格波动可能导致实际成交价格与预期不同</li>
              <li>请确保账户有足够的余额</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default QuickTradingModal
