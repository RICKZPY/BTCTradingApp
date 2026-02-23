/**
 * CSV数据API客户端
 * 用于获取从daily_snapshots下载的历史数据
 */

import apiClient from './client'

export interface ContractDataPoint {
  timestamp: string
  mark_price?: number
  bid_price?: number
  ask_price?: number
  volume?: number
  open_interest?: number
  implied_volatility?: number
}

export interface ContractPriceData {
  instrument_name: string
  underlying: string
  strike_price: number
  option_type: string
  expiry_date: string
  data_points: number
  avg_price: number
  price_history: ContractDataPoint[]
  date_range: {
    start: string
    end: string
  }
}

export interface CSVDataSummary {
  total_files: number
  total_records: number
  total_contracts: number
  contracts: Record<string, any>
  last_updated: string
}

export interface ContractInfo {
  instrument_name: string
  record_count: number
  strike_price: number
  option_type: string
  expiry_date: string
  date_range: {
    start: string
    end: string
  }
}

export const csvApi = {
  /**
   * 获取CSV数据摘要
   */
  getSummary: async (): Promise<CSVDataSummary> => {
    const response = await apiClient.get('/api/csv/summary')
    return response.data
  },

  /**
   * 获取CSV中的合约列表
   */
  getContracts: async (underlying: string = 'BTC'): Promise<ContractInfo[]> => {
    const response = await apiClient.get('/api/csv/contracts', {
      params: { underlying }
    })
    return response.data.contracts
  },

  /**
   * 获取特定合约的CSV数据
   */
  getContractData: async (instrumentName: string): Promise<ContractPriceData> => {
    const response = await apiClient.get(`/api/csv/contract/${instrumentName}`)
    return response.data
  },

  /**
   * 同步CSV数据到缓存
   */
  syncData: async () => {
    const response = await apiClient.post('/api/csv/sync')
    return response.data
  }
}
