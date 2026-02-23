import { apiClient } from './client'

export const scheduledTradingApi = {
  // 初始化管理器
  initialize: async (credentials: {
    api_key: string
    api_secret: string
    testnet: boolean
  }) => {
    const response = await apiClient.post('/scheduled-trading/initialize', credentials)
    return response.data
  },

  // 添加定时策略
  addStrategy: async (data: {
    strategy_id: string
    schedule_time: string
    timezone: string
    use_market_order: boolean
    auto_close: boolean
    close_time: string | null
  }) => {
    const response = await apiClient.post('/scheduled-trading/add-strategy', data)
    return response.data
  },

  // 获取所有定时策略
  getScheduledStrategies: async () => {
    const response = await apiClient.get('/scheduled-trading/strategies')
    return response.data
  },

  // 启用策略
  enableStrategy: async (strategyId: string) => {
    const response = await apiClient.post(`/scheduled-trading/enable/${strategyId}`)
    return response.data
  },

  // 禁用策略
  disableStrategy: async (strategyId: string) => {
    const response = await apiClient.post(`/scheduled-trading/disable/${strategyId}`)
    return response.data
  },

  // 移除策略
  removeStrategy: async (strategyId: string) => {
    const response = await apiClient.delete(`/scheduled-trading/${strategyId}`)
    return response.data
  },

  // 获取执行日志
  getExecutionLog: async () => {
    const response = await apiClient.get('/scheduled-trading/execution-log')
    return response.data
  },

  // 获取账户摘要
  getAccountSummary: async () => {
    const response = await apiClient.get('/scheduled-trading/account-summary')
    return response.data
  },

  // 获取持仓
  getPositions: async () => {
    const response = await apiClient.get('/scheduled-trading/positions')
    return response.data
  }
}
