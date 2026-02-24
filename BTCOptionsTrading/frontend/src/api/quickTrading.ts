import apiClient from './client'

export interface QuickTradeRequest {
  strategy_id: string
  test_mode: boolean
  api_key: string
  api_secret: string
}

export interface QuickTradeResponse {
  success: boolean
  message: string
  orders: Array<{
    instrument_name: string
    side: string
    amount: number
    price: number
    order_id?: string
  }>
  total_cost: number
  execution_time: string
}

export const quickTradingApi = {
  // 执行快速交易
  execute: async (data: QuickTradeRequest): Promise<QuickTradeResponse> => {
    const response = await apiClient.post('/api/quick-trading/execute', data)
    return response.data
  },

  // 测试API连接
  testConnection: async (
    apiKey: string,
    apiSecret: string,
    testMode: boolean = true
  ): Promise<{ success: boolean; message: string; test_mode: boolean }> => {
    const response = await apiClient.get('/api/quick-trading/test-connection', {
      params: {
        api_key: apiKey,
        api_secret: apiSecret,
        test_mode: testMode
      }
    })
    return response.data
  }
}
