import { useState, useEffect } from 'react'
import { scheduledTradingApi } from '../../api/scheduledTrading'
import LoadingSpinner from '../LoadingSpinner'
import Modal from '../Modal'

interface ScheduledStrategy {
  strategy_id: string
  strategy_name: string
  enabled: boolean
  schedule_time: string
  timezone: string
  use_market_order: boolean
  auto_close: boolean
  close_time: string | null
}

interface ScheduledTradingManagerProps {
  strategies: any[]
  onClose: () => void
}

const ScheduledTradingManager = ({ strategies, onClose }: ScheduledTradingManagerProps) => {
  const [isInitialized, setIsInitialized] = useState(false)
  const [scheduledStrategies, setScheduledStrategies] = useState<ScheduledStrategy[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showCredentialsModal, setShowCredentialsModal] = useState(false)
  
  // 添加策略表单
  const [selectedStrategyId, setSelectedStrategyId] = useState('')
  const [scheduleTime, setScheduleTime] = useState('05:00')
  const [timezone, setTimezone] = useState('Asia/Shanghai')
  const [useMarketOrder, setUseMarketOrder] = useState(false)
  const [autoClose, setAutoClose] = useState(false)
  const [closeTime, setCloseTime] = useState('16:00')
  
  // API凭证
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [testnet, setTestnet] = useState(true)
  
  // 账户信息
  const [accountSummary, setAccountSummary] = useState<any>(null)
  const [positions, setPositions] = useState<any[]>([])
  const [executionLog, setExecutionLog] = useState<any[]>([])

  useEffect(() => {
    checkInitialization()
  }, [])

  const checkInitialization = async () => {
    try {
      const strategies = await scheduledTradingApi.getScheduledStrategies()
      setScheduledStrategies(strategies)
      setIsInitialized(true)
      loadAccountInfo()
    } catch (error) {
      setIsInitialized(false)
    }
  }

  const initializeManager = async () => {
    if (!apiKey || !apiSecret) {
      alert('请输入API密钥')
      return
    }

    try {
      setIsLoading(true)
      await scheduledTradingApi.initialize({
        api_key: apiKey,
        api_secret: apiSecret,
        testnet
      })
      setIsInitialized(true)
      setShowCredentialsModal(false)
      alert('初始化成功！')
      checkInitialization()
    } catch (error) {
      alert('初始化失败: ' + (error as Error).message)
    } finally {
      setIsLoading(false)
    }
  }

  const loadAccountInfo = async () => {
    try {
      const [summary, positionsData, log] = await Promise.all([
        scheduledTradingApi.getAccountSummary(),
        scheduledTradingApi.getPositions(),
        scheduledTradingApi.getExecutionLog()
      ])
      setAccountSummary(summary)
      setPositions(positionsData.positions || [])
      setExecutionLog(log.log || [])
    } catch (error) {
      console.error('加载账户信息失败:', error)
    }
  }

  const addScheduledStrategy = async () => {
    if (!selectedStrategyId) {
      alert('请选择策略')
      return
    }

    try {
      setIsLoading(true)
      await scheduledTradingApi.addStrategy({
        strategy_id: selectedStrategyId,
        schedule_time: scheduleTime,
        timezone,
        use_market_order: useMarketOrder,
        auto_close: autoClose,
        close_time: autoClose ? closeTime : null
      })
      setShowAddModal(false)
      alert('添加成功！')
      checkInitialization()
    } catch (error) {
      alert('添加失败: ' + (error as Error).message)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleStrategy = async (strategyId: string, enabled: boolean) => {
    try {
      if (enabled) {
        await scheduledTradingApi.enableStrategy(strategyId)
      } else {
        await scheduledTradingApi.disableStrategy(strategyId)
      }
      checkInitialization()
    } catch (error) {
      alert('操作失败: ' + (error as Error).message)
    }
  }

  const removeStrategy = async (strategyId: string) => {
    if (!confirm('确定要移除这个定时策略吗？')) return

    try {
      await scheduledTradingApi.removeStrategy(strategyId)
      checkInitialization()
    } catch (error) {
      alert('移除失败: ' + (error as Error).message)
    }
  }

  if (!isInitialized) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">定时交易管理</h2>
        <div className="bg-yellow-900/30 border border-yellow-600 rounded p-4 mb-4">
          <p className="text-yellow-200">
            ⚠️ 定时交易管理器未初始化。请先配置Deribit API凭证。
          </p>
        </div>
        <button
          onClick={() => setShowCredentialsModal(true)}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
        >
          配置API凭证
        </button>

        {/* API凭证配置模态框 */}
        <Modal
          isOpen={showCredentialsModal}
          onClose={() => setShowCredentialsModal(false)}
          title="配置Deribit API"
        >
          <div className="space-y-4">
            <div className="bg-blue-900/30 border border-blue-600 rounded p-3 text-sm">
              <p className="mb-2">请访问 <a href="https://test.deribit.com/" target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">Deribit测试网</a> 获取API密钥</p>
              <p className="text-gray-400">测试网可以安全地测试交易功能，不会使用真实资金</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Key</label>
              <input
                type="text"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="输入API Key"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Secret</label>
              <input
                type="password"
                value={apiSecret}
                onChange={(e) => setApiSecret(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="输入API Secret"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="testnet"
                checked={testnet}
                onChange={(e) => setTestnet(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="testnet" className="text-sm">
                使用测试网络（推荐）
              </label>
            </div>

            <div className="flex gap-3">
              <button
                onClick={initializeManager}
                disabled={isLoading}
                className="flex-1 bg-green-600 hover:bg-green-700 px-4 py-2 rounded disabled:opacity-50"
              >
                {isLoading ? <LoadingSpinner size="sm" /> : '初始化'}
              </button>
              <button
                onClick={() => setShowCredentialsModal(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded"
              >
                取消
              </button>
            </div>
          </div>
        </Modal>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 账户信息 */}
      {accountSummary && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3">账户信息</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-400">余额</div>
              <div className="text-xl font-bold">{accountSummary.balance?.toFixed(4)} BTC</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">可用资金</div>
              <div className="text-xl font-bold">{accountSummary.available_funds?.toFixed(4)} BTC</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">持仓数量</div>
              <div className="text-xl font-bold">{positions.length}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">网络</div>
              <div className="text-xl font-bold">{testnet ? '测试网' : '生产环境'}</div>
            </div>
          </div>
        </div>
      )}

      {/* 定时策略列表 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">定时策略</h3>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
          >
            + 添加定时策略
          </button>
        </div>

        {scheduledStrategies.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            暂无定时策略，点击上方按钮添加
          </div>
        ) : (
          <div className="space-y-3">
            {scheduledStrategies.map((strategy) => (
              <div key={strategy.strategy_id} className="bg-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-medium">{strategy.strategy_name}</h4>
                      <span className={`px-2 py-1 rounded text-xs ${
                        strategy.enabled ? 'bg-green-600' : 'bg-gray-600'
                      }`}>
                        {strategy.enabled ? '已启用' : '已禁用'}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-300">
                      <div>执行时间: {strategy.schedule_time}</div>
                      <div>时区: {strategy.timezone}</div>
                      <div>订单类型: {strategy.use_market_order ? '市价单' : '限价单'}</div>
                      {strategy.auto_close && (
                        <div>平仓时间: {strategy.close_time}</div>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggleStrategy(strategy.strategy_id, !strategy.enabled)}
                      className={`px-3 py-1 rounded text-sm ${
                        strategy.enabled
                          ? 'bg-yellow-600 hover:bg-yellow-700'
                          : 'bg-green-600 hover:bg-green-700'
                      }`}
                    >
                      {strategy.enabled ? '禁用' : '启用'}
                    </button>
                    <button
                      onClick={() => removeStrategy(strategy.strategy_id)}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 执行日志 */}
      {executionLog.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3">执行日志</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {executionLog.map((log, index) => (
              <div key={index} className="bg-gray-700 rounded p-3 text-sm">
                <div className="flex justify-between items-start mb-1">
                  <span className="font-medium">{log.strategy_name}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    log.success ? 'bg-green-600' : 'bg-red-600'
                  }`}>
                    {log.success ? '成功' : '失败'}
                  </span>
                </div>
                <div className="text-gray-400 text-xs">{log.execution_time}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 添加策略模态框 */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="添加定时策略"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">选择策略</label>
            <select
              value={selectedStrategyId}
              onChange={(e) => setSelectedStrategyId(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
            >
              <option value="">请选择...</option>
              {strategies.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">执行时间</label>
              <input
                type="time"
                value={scheduleTime}
                onChange={(e) => setScheduleTime(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">时区</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              >
                <option value="Asia/Shanghai">北京时间</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">纽约时间</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="useMarketOrder"
              checked={useMarketOrder}
              onChange={(e) => setUseMarketOrder(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="useMarketOrder" className="text-sm">
              使用市价单（否则使用限价单）
            </label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="autoClose"
              checked={autoClose}
              onChange={(e) => setAutoClose(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="autoClose" className="text-sm">
              启用自动平仓
            </label>
          </div>

          {autoClose && (
            <div>
              <label className="block text-sm font-medium mb-2">平仓时间</label>
              <input
                type="time"
                value={closeTime}
                onChange={(e) => setCloseTime(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              />
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={addScheduledStrategy}
              disabled={isLoading}
              className="flex-1 bg-green-600 hover:bg-green-700 px-4 py-2 rounded disabled:opacity-50"
            >
              {isLoading ? <LoadingSpinner size="sm" /> : '添加'}
            </button>
            <button
              onClick={() => setShowAddModal(false)}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded"
            >
              取消
            </button>
          </div>
        </div>
      </Modal>

      <button
        onClick={onClose}
        className="w-full bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded"
      >
        关闭
      </button>
    </div>
  )
}

export default ScheduledTradingManager
