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
}
