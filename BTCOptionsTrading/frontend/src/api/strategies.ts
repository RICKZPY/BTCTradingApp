import apiClient from './client'
import type { Strategy, CreateStrategyRequest, StrategyTemplate } from './types'

export const strategiesApi = {
  // 获取策略列表
  list: async (skip = 0, limit = 100): Promise<Strategy[]> => {
    const response = await apiClient.get('/api/strategies/', {
      params: { skip, limit },
    })
    return response.data
  },

  // 获取策略详情
  get: async (id: string): Promise<Strategy> => {
    const response = await apiClient.get(`/api/strategies/${id}`)
    return response.data
  },

  // 创建策略
  create: async (data: CreateStrategyRequest): Promise<Strategy> => {
    const response = await apiClient.post('/api/strategies/', data)
    return response.data
  },

  // 更新策略
  update: async (id: string, data: Partial<CreateStrategyRequest>): Promise<Strategy> => {
    const response = await apiClient.put(`/api/strategies/${id}`, data)
    return response.data
  },

  // 删除策略
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/strategies/${id}`)
  },

  // 获取策略模板
  getTemplates: async (): Promise<{ templates: StrategyTemplate[] }> => {
    const response = await apiClient.get('/api/strategies/templates/list')
    return response.data
  },

  // 验证策略配置
  validate: async (data: {
    name?: string
    strategy_type: string
    legs: any[]
    initial_capital?: number
  }): Promise<{
    is_valid: boolean
    errors: Array<{ field: string; message: string }>
    warnings: Array<{ field: string; message: string }>
  }> => {
    const response = await apiClient.post('/api/strategies/validate', data)
    return response.data
  },

  // 计算策略风险
  calculateRisk: async (data: {
    legs: any[]
    spot_price: number
    risk_free_rate?: number
    volatility?: number
  }): Promise<{
    greeks: {
      delta: number
      gamma: number
      theta: number
      vega: number
      rho: number
    }
    initial_cost: number
    max_profit: number
    max_loss: number
    breakeven_points: number[]
    risk_reward_ratio: number
    probability_of_profit?: number
  }> => {
    const response = await apiClient.post('/api/strategies/calculate-risk', data)
    return response.data
  },
}
