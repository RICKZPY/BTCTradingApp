import apiClient from './client'
import type { GreeksRequest, GreeksResponse } from './types'

export const dataApi = {
  // 计算希腊字母
  calculateGreeks: async (data: GreeksRequest): Promise<GreeksResponse> => {
    const response = await apiClient.post('/api/data/calculate-greeks', data)
    return response.data
  },

  // 获取标的资产价格
  getUnderlyingPrice: async (symbol = 'BTC'): Promise<{ symbol: string; price: number; timestamp: string }> => {
    const response = await apiClient.get(`/api/data/underlying-price/${symbol}`)
    return response.data
  },

  // 获取期权链
  getOptionsChain: async (currency = 'BTC', kind = 'option'): Promise<any[]> => {
    const response = await apiClient.get('/api/data/options-chain', {
      params: { currency, kind },
    })
    return response.data
  },

  // 获取波动率曲面
  getVolatilitySurface: async (currency = 'BTC'): Promise<any> => {
    const response = await apiClient.get(`/api/data/volatility-surface/${currency}`)
    return response.data
  },
}
