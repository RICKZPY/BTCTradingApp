import apiClient from './client'
import type { BacktestRequest, BacktestResult, Trade, DailyPnL } from './types'

export const backtestApi = {
  // 运行回测
  run: async (data: BacktestRequest): Promise<BacktestResult> => {
    const response = await apiClient.post('/api/backtest/run', data)
    return response.data
  },

  // 获取回测结果列表
  listResults: async (strategyId?: string, limit = 10): Promise<BacktestResult[]> => {
    const response = await apiClient.get('/api/backtest/results', {
      params: { strategy_id: strategyId, limit },
    })
    return response.data
  },

  // 获取回测结果详情
  getResult: async (id: string): Promise<BacktestResult> => {
    const response = await apiClient.get(`/api/backtest/results/${id}`)
    return response.data
  },

  // 获取交易记录
  getTrades: async (resultId: string): Promise<Trade[]> => {
    const response = await apiClient.get(`/api/backtest/results/${resultId}/trades`)
    return response.data
  },

  // 获取每日盈亏
  getDailyPnL: async (resultId: string): Promise<DailyPnL[]> => {
    const response = await apiClient.get(`/api/backtest/results/${resultId}/daily-pnl`)
    return response.data
  },

  // 删除回测结果
  deleteResult: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/backtest/results/${id}`)
  },
}
