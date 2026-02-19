import { useState, useEffect } from 'react'
import { historicalApi, type ManagerStats, type CoverageStats, type QualityReport } from '../../api/historical'
import LoadingSpinner from '../LoadingSpinner'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'

const HistoricalDataTab = () => {
  const [stats, setStats] = useState<ManagerStats | null>(null)
  const [instruments, setInstruments] = useState<string[]>([])
  const [selectedInstrument, setSelectedInstrument] = useState<string>('')
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [coverageStats, setCoverageStats] = useState<CoverageStats | null>(null)
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'overview' | 'instruments' | 'quality'>('overview')

  // 加载统计数据
  const loadStats = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await historicalApi.getStats()
      setStats(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载统计数据失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 加载可用合约
  const loadInstruments = async () => {
    try {
      const data = await historicalApi.getAvailableInstruments('BTC')
      setInstruments(data)
      if (data.length > 0 && !selectedInstrument) {
        setSelectedInstrument(data[0])
      }
    } catch (err) {
      console.error('加载合约列表失败:', err)
    }
  }

  // 加载质量报告
  const loadQualityReport = async () => {
    try {
      const data = await historicalApi.getQualityReport()
      setQualityReport(data)
    } catch (err) {
      console.error('加载质量报告失败:', err)
    }
  }

  // 加载选中合约的日期
  const loadDatesForInstrument = async (instrumentName: string) => {
    try {
      const dates = await historicalApi.getAvailableDates(instrumentName)
      setAvailableDates(dates)
      
      // 如果有日期数据，加载覆盖率统计
      if (dates.length >= 2) {
        const startDate = dates[0]
        const endDate = dates[dates.length - 1]
        const coverage = await historicalApi.getCoverageStats(startDate, endDate)
        setCoverageStats(coverage)
      }
    } catch (err) {
      console.error('加载日期数据失败:', err)
    }
  }

  useEffect(() => {
    loadStats()
    loadInstruments()
    loadQualityReport()
  }, [])

  useEffect(() => {
    if (selectedInstrument) {
      loadDatesForInstrument(selectedInstrument)
    }
  }, [selectedInstrument])

  // 格式化数字
  const formatNumber = (num: number) => {
    return num.toLocaleString('en-US')
  }

  // 格式化百分比
  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  // 格式化日期
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  }

  // 准备覆盖率图表数据
  const prepareCoverageChartData = () => {
    if (!coverageStats) return []
    
    return [
      {
        name: '数据覆盖',
        有数据: coverageStats.days_with_data,
        缺失: coverageStats.total_days - coverageStats.days_with_data
      }
    ]
  }

  // 准备质量分数图表数据
  const prepareQualityChartData = () => {
    if (!qualityReport) return []
    
    return [
      { name: '正常记录', value: qualityReport.total_records - qualityReport.missing_records - qualityReport.anomaly_records },
      { name: '缺失记录', value: qualityReport.missing_records },
      { name: '异常记录', value: qualityReport.anomaly_records }
    ]
  }

  if (isLoading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">历史数据分析</h2>
        <button
          onClick={loadStats}
          className="btn btn-secondary"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新数据
        </button>
      </div>

      {error && (
        <div className="p-4 bg-accent-red bg-opacity-10 border border-accent-red rounded-lg">
          <p className="text-accent-red">{error}</p>
        </div>
      )}

      {/* 视图切换 */}
      <div className="flex gap-2 border-b border-text-disabled">
        <button
          onClick={() => setActiveView('overview')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeView === 'overview'
              ? 'text-accent-blue border-b-2 border-accent-blue'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          数据概览
        </button>
        <button
          onClick={() => setActiveView('instruments')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeView === 'instruments'
              ? 'text-accent-blue border-b-2 border-accent-blue'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          合约分析
        </button>
        <button
          onClick={() => setActiveView('quality')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeView === 'quality'
              ? 'text-accent-blue border-b-2 border-accent-blue'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          数据质量
        </button>
      </div>

      {/* 数据概览视图 */}
      {activeView === 'overview' && stats && (
        <div className="space-y-6">
          {/* 统计卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">CSV文件数</p>
                  <p className="text-3xl font-bold text-text-primary mt-2">
                    {formatNumber(stats.csv_files)}
                  </p>
                </div>
                <div className="w-12 h-12 bg-accent-blue bg-opacity-20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-accent-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">数据库记录</p>
                  <p className="text-3xl font-bold text-text-primary mt-2">
                    {formatNumber(stats.database_records)}
                  </p>
                </div>
                <div className="w-12 h-12 bg-accent-green bg-opacity-20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-accent-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">缓存条目</p>
                  <p className="text-3xl font-bold text-text-primary mt-2">
                    {formatNumber(stats.memory_cache_entries)}
                  </p>
                </div>
                <div className="w-12 h-12 bg-accent-yellow bg-opacity-20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-accent-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">缓存大小</p>
                  <p className="text-3xl font-bold text-text-primary mt-2">
                    {stats.memory_cache_size_mb.toFixed(1)} MB
                  </p>
                </div>
                <div className="w-12 h-12 bg-accent-purple bg-opacity-20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-accent-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* 数据目录信息 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-text-primary">存储位置</h3>
            <div className="bg-bg-secondary p-4 rounded-lg font-mono text-sm text-text-primary">
              {stats.download_dir}
            </div>
          </div>

          {/* 质量概览 */}
          {qualityReport && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 text-text-primary">数据质量概览</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-text-secondary text-sm">质量分数</p>
                  <p className={`text-2xl font-bold mt-1 ${
                    qualityReport.quality_score >= 0.9 ? 'text-accent-green' :
                    qualityReport.quality_score >= 0.7 ? 'text-accent-yellow' :
                    'text-accent-red'
                  }`}>
                    {(qualityReport.quality_score * 100).toFixed(0)}分
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">覆盖率</p>
                  <p className="text-2xl font-bold text-text-primary mt-1">
                    {formatPercent(qualityReport.coverage_percentage)}
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">总记录数</p>
                  <p className="text-2xl font-bold text-text-primary mt-1">
                    {formatNumber(qualityReport.total_records)}
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">问题数量</p>
                  <p className="text-2xl font-bold text-accent-red mt-1">
                    {formatNumber(qualityReport.issues_count)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 合约分析视图 */}
      {activeView === 'instruments' && (
        <div className="space-y-6">
          {/* 合约选择器 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-text-primary">选择期权合约</h3>
            <select
              value={selectedInstrument}
              onChange={(e) => setSelectedInstrument(e.target.value)}
              className="select w-full max-w-md"
            >
              <option value="">选择合约...</option>
              {instruments.map((instrument) => (
                <option key={instrument} value={instrument}>
                  {instrument}
                </option>
              ))}
            </select>
            <p className="text-sm text-text-secondary mt-2">
              共有 {instruments.length} 个可用合约
            </p>
          </div>

          {/* 合约数据统计 */}
          {selectedInstrument && coverageStats && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 覆盖率统计 */}
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 text-text-primary">数据覆盖率</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">时间范围:</span>
                    <span className="text-text-primary font-medium">
                      {formatDate(coverageStats.start_date)} - {formatDate(coverageStats.end_date)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">总天数:</span>
                    <span className="text-text-primary font-medium">{coverageStats.total_days} 天</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">有数据天数:</span>
                    <span className="text-accent-green font-medium">{coverageStats.days_with_data} 天</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">缺失天数:</span>
                    <span className="text-accent-red font-medium">{coverageStats.missing_dates_count} 天</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">覆盖率:</span>
                    <span className="text-accent-blue font-bold text-xl">
                      {formatPercent(coverageStats.coverage_percentage)}
                    </span>
                  </div>
                </div>
              </div>

              {/* 覆盖率图表 */}
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 text-text-primary">数据完整性</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={prepareCoverageChartData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                    <XAxis dataKey="name" stroke="#848E9C" />
                    <YAxis stroke="#848E9C" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1E2329',
                        border: '1px solid #474D57',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="有数据" fill="#0ECB81" />
                    <Bar dataKey="缺失" fill="#F6465D" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* 可用日期列表 */}
          {selectedInstrument && availableDates.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 text-text-primary">
                可用数据日期 ({availableDates.length} 天)
              </h3>
              <div className="max-h-64 overflow-y-auto">
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                  {availableDates.slice(0, 50).map((date) => (
                    <div
                      key={date}
                      className="px-3 py-2 bg-bg-secondary rounded text-sm text-text-primary text-center"
                    >
                      {formatDate(date)}
                    </div>
                  ))}
                </div>
                {availableDates.length > 50 && (
                  <p className="text-sm text-text-secondary mt-4 text-center">
                    还有 {availableDates.length - 50} 个日期未显示...
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 数据质量视图 */}
      {activeView === 'quality' && qualityReport && (
        <div className="space-y-6">
          {/* 质量指标 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <h4 className="text-sm text-text-secondary mb-2">质量分数</h4>
              <div className="flex items-end gap-2">
                <p className={`text-4xl font-bold ${
                  qualityReport.quality_score >= 0.9 ? 'text-accent-green' :
                  qualityReport.quality_score >= 0.7 ? 'text-accent-yellow' :
                  'text-accent-red'
                }`}>
                  {(qualityReport.quality_score * 100).toFixed(0)}
                </p>
                <p className="text-text-secondary mb-1">/ 100</p>
              </div>
              <div className="mt-2 w-full bg-bg-secondary rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    qualityReport.quality_score >= 0.9 ? 'bg-accent-green' :
                    qualityReport.quality_score >= 0.7 ? 'bg-accent-yellow' :
                    'bg-accent-red'
                  }`}
                  style={{ width: `${qualityReport.quality_score * 100}%` }}
                />
              </div>
            </div>

            <div className="card">
              <h4 className="text-sm text-text-secondary mb-2">数据覆盖率</h4>
              <div className="flex items-end gap-2">
                <p className="text-4xl font-bold text-accent-blue">
                  {(qualityReport.coverage_percentage * 100).toFixed(1)}
                </p>
                <p className="text-text-secondary mb-1">%</p>
              </div>
              <div className="mt-2 w-full bg-bg-secondary rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-accent-blue"
                  style={{ width: `${qualityReport.coverage_percentage * 100}%` }}
                />
              </div>
            </div>

            <div className="card">
              <h4 className="text-sm text-text-secondary mb-2">问题总数</h4>
              <div className="flex items-end gap-2">
                <p className="text-4xl font-bold text-accent-red">
                  {formatNumber(qualityReport.issues_count)}
                </p>
              </div>
              <p className="text-xs text-text-secondary mt-2">
                缺失: {qualityReport.missing_records} | 异常: {qualityReport.anomaly_records}
              </p>
            </div>
          </div>

          {/* 数据分布 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-text-primary">数据记录分布</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={prepareQualityChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                <XAxis dataKey="name" stroke="#848E9C" />
                <YAxis stroke="#848E9C" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E2329',
                    border: '1px solid #474D57',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="value" fill="#3861FB" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 时间范围 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-text-primary">数据时间范围</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-text-secondary text-sm mb-1">开始时间</p>
                <p className="text-text-primary font-medium">
                  {formatDate(qualityReport.time_range_start)}
                </p>
              </div>
              <div>
                <p className="text-text-secondary text-sm mb-1">结束时间</p>
                <p className="text-text-primary font-medium">
                  {formatDate(qualityReport.time_range_end)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default HistoricalDataTab
