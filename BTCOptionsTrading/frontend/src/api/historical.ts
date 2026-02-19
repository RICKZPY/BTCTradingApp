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
    const response = await apiClient.get('/api/historical-data/available/instruments', {
      params: { underlying_symbol: underlyingSymbol },
    })
    return response.data
  },

  // 获取可用的日期列表
  getAvailableDates: async (instrumentName?: string): Promise<string[]> => {
    const response = await apiClient.get('/api/historical-data/available/dates', {
      params: { instrument_name: instrumentName },
    })
    return response.data
  },

  // 获取覆盖率统计
  getCoverageStats: async (startDate: string, endDate: string): Promise<CoverageStats> => {
    const response = await apiClient.get('/api/historical-data/coverage', {
      params: { start_date: startDate, end_date: endDate },
    })
    return response.data
  },

  // 获取质量报告
  getQualityReport: async (startDate?: string, endDate?: string): Promise<QualityReport> => {
    const response = await apiClient.get('/api/historical-data/quality', {
      params: { start_date: startDate, end_date: endDate },
    })
    return response.data
  },

  // 获取管理器统计
  getStats: async (): Promise<ManagerStats> => {
    const response = await apiClient.get('/api/historical-data/stats')
    return response.data
  },

  // 健康检查
  healthCheck: async (): Promise<{ status: string; message: string }> => {
    const response = await apiClient.get('/api/historical-data/health')
    return response.data
  },
}
