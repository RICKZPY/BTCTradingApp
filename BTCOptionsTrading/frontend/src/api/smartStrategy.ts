import { apiClient } from './client'

export const smartStrategyApi = {
  // 获取相对到期日选项
  getRelativeExpiries: async () => {
    const response = await apiClient.get('/smart-strategy/relative-expiries')
    return response.data
  },

  // 获取相对行权价选项
  getRelativeStrikes: async () => {
    const response = await apiClient.get('/smart-strategy/relative-strikes')
    return response.data
  },

  // 获取预定义模板
  getTemplates: async () => {
    const response = await apiClient.get('/smart-strategy/templates')
    return response.data
  },

  // 构建智能策略
  build: async (data: {
    name: string
    description: string
    strategy_type: string
    legs: Array<{
      option_type: string
      action: string
      quantity: number
      relative_expiry: string
      relative_strike: string
    }>
    underlying?: string
  }) => {
    const response = await apiClient.post('/smart-strategy/build', data)
    return response.data
  },

  // 从模板构建
  buildFromTemplate: async (templateId: string, underlying: string = 'BTC') => {
    const response = await apiClient.post(
      `/smart-strategy/build-from-template/${templateId}`,
      null,
      { params: { underlying } }
    )
    return response.data
  },

  // 预览合约
  preview: async (
    optionType: string,
    relativeExpiry: string,
    relativeStrike: string,
    underlying: string = 'BTC'
  ) => {
    const response = await apiClient.get('/smart-strategy/preview', {
      params: {
        option_type: optionType,
        relative_expiry: relativeExpiry,
        relative_strike: relativeStrike,
        underlying
      }
    })
    return response.data
  }
}
