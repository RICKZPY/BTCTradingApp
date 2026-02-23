import apiClient from './client'

export interface HistoricalDataRecord {
  timestamp: string
  instrument_name: string
  underlying_symbol: string
  strike_price: number
  expiry_date: string
  option_type: string
  open_price: number
  high_price: number
  low_price: number
  close_price: number
  volume: number
  open_interest: number
  implied_volatility: number
}

export interface CoverageStats {
  start_date: string
  end_date: string
  total_days: number
  days_with_data: number
  coverage_percentage: number
  missing_dates_count: number
  strikes_covered: number[]
  expiries_covered: string[]
}

export interface QualityReport {
  total_records: number
  missing_records: number
  anomaly_records: number
  coverage_percentage: number
  quality_score: number
  time_range_start: string
  time_range_end: string
  issues_count: number
}

export interface ManagerStats {
  download_dir: string
  csv_files: number
  database_records: number
  memory_cache_entries: number
  memory_cache_size_mb: number
}

export const historicalApi = {
  // 获取可用的期权合约列表
  getAvailableInstruments: async (underlyingSymbol?: string): Promise<string[]> => {
    const params = underlyingSymbol ? { underlying_symbol: underlyingSymbol } : {}
    const response = await apiClient.get('/api/historical/contracts', { params })
    return response.data
  },

  // 获取合约详情
  getContractDetails: async (instrumentName: string): Promise<any> => {
    const response = await apiClient.get(`/api/historical/contract/${instrumentName}`)
    return response.data
  },

  // 获取可用的日期列表
  getAvailableDates: async (instrumentName?: string): Promise<string[]> => {
    // 暂时返回空数组，因为简化API不支持此功能
    return []
  },

  // 获取覆盖率统计
  getCoverageStats: async (startDate: string, endDate: string): Promise<CoverageStats> => {
    // 返回模拟数据
    return {
      start_date: startDate,
      end_date: endDate,
      total_days: 30,
      days_with_data: 25,
      coverage_percentage: 0.83,
      missing_dates_count: 5,
      strikes_covered: [50000, 55000, 60000],
      expiries_covered: ['2026-02-20', '2026-03-13']
    }
  },

  // 获取质量报告
  getQualityReport: async (startDate?: string, endDate?: string): Promise<QualityReport> => {
    // 返回模拟数据
    return {
      total_records: 922,
      missing_records: 0,
      anomaly_records: 0,
      coverage_percentage: 1.0,
      quality_score: 0.95,
      time_range_start: '2026-02-20T01:43:31',
      time_range_end: '2026-02-20T01:47:30',
      issues_count: 0
    }
  },

  // 获取管理器统计
  getStats: async (): Promise<ManagerStats> => {
    const response = await apiClient.get('/api/historical/overview')
    return {
      download_dir: 'data/downloads',
      csv_files: response.data.csv_files,
      database_records: response.data.database_records,
      memory_cache_entries: response.data.unique_instruments,
      memory_cache_size_mb: response.data.memory_cache_size_mb
    }
  },

  // 健康检查
  healthCheck: async (): Promise<{ status: string; message: string }> => {
    return { status: 'ok', message: 'Simple API is running' }
  },
}
