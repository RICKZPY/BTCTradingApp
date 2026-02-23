import { useState, useEffect } from 'react'
import { historicalApi, type ManagerStats, type CoverageStats, type QualityReport } from '../../api/historical'
import { csvApi, type ContractInfo, type ContractPriceData } from '../../api/csv'
import LoadingSpinner from '../LoadingSpinner'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'

const HistoricalDataTab = () => {
  const [stats, setStats] = useState<ManagerStats | null>(null)
  const [instruments, setInstruments] = useState<string[]>([])
  const [selectedInstrument, setSelectedInstrument] = useState<string>('')
  const [contractDetails, setContractDetails] = useState<any>(null)
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [coverageStats, setCoverageStats] = useState<CoverageStats | null>(null)
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'overview' | 'instruments' | 'quality' | 'csv'>('overview')
  
  // CSV数据相关状态
  const [csvContracts, setCSVContracts] = useState<ContractInfo[]>([])
  const [selectedCSVContract, setSelectedCSVContract] = useState<string>('')
  const [csvContractData, setCSVContractData] = useState<ContractPriceData | null>(null)
  const [isLoadingCSV, setIsLoadingCSV] = useState(false)
  const [csvError, setCSVError] = useState<string | null>(null)

  // 加载CSV合约列表
  const loadCSVContracts = async () => {
    try {
      setIsLoadingCSV(true)
      setCSVError(null)
      const contracts = await csvApi.getContracts('BTC')
      setCSVContracts(contracts)
      if (contracts.length > 0 && !selectedCSVContract) {
        setSelectedCSVContract(contracts[0].instrument_name)
      }
    } catch (err) {
      setCSVError(err instanceof Error ? err.message : '加载CSV合约列表失败')
      console.error('加载CSV合约列表失败:', err)
    } finally {
      setIsLoadingCSV(false)
    }
  }

  // 加载CSV合约数据
  const loadCSVContractData = async (instrumentName: string) => {
    if (!instrumentName) return
    
    try {
      setIsLoadingCSV(true)
      setCSVError(null)
      const data = await csvApi.getContractData(instrumentName)
      setCSVContractData(data)
    } catch (err) {
      setCSVError(err instanceof Error ? err.message : '加载CSV合约数据失败')
      console.error('加载CSV合约数据失败:', err)
    } finally {
      setIsLoadingCSV(false)
    }
  }

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
      console.log('开始加载合约列表...')
      
      // 首先尝试从数据库获取
      let instrumentList: string[] = []
      try {
        const data = await historicalApi.getAvailableInstruments('BTC')
        instrumentList = Array.isArray(data) ? (data as string[]) : []
        console.log(`从数据库获取了 ${instrumentList.length} 个合约`)
      } catch (dbErr) {
        console.warn('从数据库获取合约失败:', dbErr)
      }
      
      // 如果数据库中没有数据，尝试从 CSV API 获取
      if (instrumentList.length === 0) {
        console.info('数据库中没有合约，尝试从 CSV 数据获取...')
        try {
          console.log('正在调用 csvApi.getContracts("BTC")...')
          const csvContracts = await csvApi.getContracts('BTC')
          console.log(`从 CSV 获取了 ${csvContracts.length} 个合约`)
          console.log('CSV合约示例:', csvContracts.slice(0, 3))
          const csvInstrumentList = csvContracts.map(c => c.instrument_name)
          console.log(`转换后的合约列表长度: ${csvInstrumentList.length}`)
          setInstruments(csvInstrumentList)
          if (csvInstrumentList.length > 0 && !selectedInstrument) {
            setSelectedInstrument(csvInstrumentList[0])
          }
          console.log('✓ 成功从 CSV 加载合约')
          return
        } catch (csvErr) {
          console.error('从 CSV 获取合约失败:', csvErr)
          console.error('错误详情:', csvErr instanceof Error ? csvErr.message : String(csvErr))
          setError('无法加载合约数据')
          return
        }
      }
      
      setInstruments(instrumentList)
      if (instrumentList.length > 0 && !selectedInstrument) {
        setSelectedInstrument(instrumentList[0])
      }
    } catch (err) {
      console.error('加载合约列表失败:', err)
      setInstruments([]) // 出错时设置为空数组
      setError(err instanceof Error ? err.message : '加载合约列表失败')
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
      setIsLoading(true)
      setError(null)
      console.log(`开始加载合约详情: ${instrumentName}`)
      
      // 首先尝试从数据库获取
      let details: any = null
      try {
        details = await historicalApi.getContractDetails(instrumentName)
        console.log(`从数据库获取了合约详情`)
      } catch (dbErr) {
        console.warn('从数据库获取合约详情失败:', dbErr)
      }
      
      // 如果数据库中没有数据，尝试从 CSV 获取
      if (!details) {
        console.info('数据库中没有合约详情，尝试从 CSV 获取...')
        try {
          const csvData = await csvApi.getContractData(instrumentName)
          console.log(`从 CSV 获取了合约详情`)
          
          // 转换 CSV 数据格式以匹配数据库格式
          details = {
            instrument_name: csvData.instrument_name,
            underlying: csvData.underlying,
            strike_price: csvData.strike_price,
            option_type: csvData.option_type,
            expiry_date: csvData.expiry_date,
            data_points: csvData.data_points,
            avg_price: csvData.avg_price,
            price_history: csvData.price_history,
            total_volume: csvData.price_history.reduce((sum: number, p: any) => sum + (p.volume || 0), 0)
          }
        } catch (csvErr) {
          console.error('从 CSV 获取合约详情失败:', csvErr)
          setError('无法加载合约详情')
          setIsLoading(false)
          return
        }
      }
      
      if (!details) {
        setError('无法加载合约详情')
        setIsLoading(false)
        return
      }
      
      setContractDetails(details)
      
      // 从价格历史中提取日期
      if (details.price_history && details.price_history.length > 0) {
        const dates = details.price_history.map((item: any) => item.timestamp.split('T')[0])
        const uniqueDates = Array.from(new Set(dates)).sort() as string[]
        setAvailableDates(uniqueDates)
        
        // 设置覆盖率统计
        if (uniqueDates.length >= 1) {
          const startDate = uniqueDates[0]
          const endDate = uniqueDates[uniqueDates.length - 1]
          setCoverageStats({
            start_date: startDate,
            end_date: endDate,
            total_days: uniqueDates.length,
            days_with_data: uniqueDates.length,
            coverage_percentage: 1.0,
            missing_dates_count: 0,
            strikes_covered: [details.strike_price],
            expiries_covered: [details.expiry_date]
          })
        }
      }
      console.log('✓ 成功加载合约详情')
    } catch (err) {
      console.error('加载合约详情失败:', err)
      setError(err instanceof Error ? err.message : '加载合约详情失败')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadStats()
    loadInstruments()
    loadQualityReport()
    loadCSVContracts()
  }, [])

  useEffect(() => {
    if (selectedInstrument) {
      loadDatesForInstrument(selectedInstrument)
    }
  }, [selectedInstrument])

  useEffect(() => {
    if (selectedCSVContract) {
      loadCSVContractData(selectedCSVContract)
    }
  }, [selectedCSVContract])

  // 格式化数字
  const formatNumber = (num: number | undefined) => {
    if (num === undefined || num === null) return '0'
    return num.toLocaleString('en-US')
  }

  // 格式化百分比
  const formatPercent = (value: number | undefined) => {
    if (value === undefined || value === null) return '0.0%'
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
          onClick={() => setActiveView('csv')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeView === 'csv'
              ? 'text-accent-blue border-b-2 border-accent-blue'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          CSV数据分析
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
                    {(stats.memory_cache_size_mb || 0).toFixed(1)} MB
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
                    {((qualityReport?.quality_score || 0) * 100).toFixed(0)}分
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
              {Array.isArray(instruments) && instruments.map((instrument) => (
                <option key={instrument} value={instrument}>
                  {instrument}
                </option>
              ))}
            </select>
            <p className="text-sm text-text-secondary mt-2">
              共有 {instruments.length} 个可用合约
            </p>
          </div>

          {/* 合约基本信息 */}
          {selectedInstrument && contractDetails && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 text-text-primary">合约信息</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-text-secondary text-sm">合约名称</p>
                  <p className="text-text-primary font-medium mt-1">{contractDetails.instrument_name}</p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">标的资产</p>
                  <p className="text-text-primary font-medium mt-1">{contractDetails.underlying}</p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">执行价</p>
                  <p className="text-text-primary font-medium mt-1">${contractDetails.strike_price.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">期权类型</p>
                  <p className="text-text-primary font-medium mt-1">
                    {contractDetails.option_type === 'call' ? '看涨 (Call)' : '看跌 (Put)'}
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">到期日</p>
                  <p className="text-text-primary font-medium mt-1">
                    {new Date(contractDetails.expiry_date).toLocaleDateString('zh-CN')}
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">数据点数</p>
                  <p className="text-accent-blue font-bold text-xl mt-1">{contractDetails.data_points}</p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">平均价格</p>
                  <p className="text-accent-green font-bold text-xl mt-1">
                    {contractDetails.avg_price.toFixed(4)} BTC
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary text-sm">总成交量</p>
                  <p className="text-text-primary font-bold text-xl mt-1">
                    {contractDetails.total_volume.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 价格历史图表 */}
          {selectedInstrument && contractDetails && contractDetails.price_history && contractDetails.price_history.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 text-text-primary">价格历史</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={contractDetails.price_history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#848E9C"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                  />
                  <YAxis stroke="#848E9C" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1E2329',
                      border: '1px solid #474D57',
                      borderRadius: '8px'
                    }}
                    labelFormatter={(value) => new Date(value).toLocaleString('zh-CN')}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="mark_price" stroke="#F0B90B" name="标记价格" />
                  <Line type="monotone" dataKey="bid_price" stroke="#0ECB81" name="买价" />
                  <Line type="monotone" dataKey="ask_price" stroke="#F6465D" name="卖价" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* 希腊值和隐含波动率 */}
          {selectedInstrument && contractDetails && contractDetails.price_history && contractDetails.price_history.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 text-text-primary">隐含波动率</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={contractDetails.price_history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#848E9C"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                  />
                  <YAxis stroke="#848E9C" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1E2329',
                      border: '1px solid #474D57',
                      borderRadius: '8px'
                    }}
                    labelFormatter={(value) => new Date(value).toLocaleString('zh-CN')}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="implied_volatility" stroke="#B7BDC6" name="隐含波动率 (%)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

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

      {/* CSV数据分析视图 */}
      {activeView === 'csv' && (
        <div className="space-y-6">
          {csvError && (
            <div className="p-4 bg-accent-red bg-opacity-10 border border-accent-red rounded-lg">
              <p className="text-accent-red">{csvError}</p>
            </div>
          )}

          {/* CSV合约选择器 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-text-primary">选择CSV合约</h3>
            {isLoadingCSV && csvContracts.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : (
              <>
                <select
                  value={selectedCSVContract}
                  onChange={(e) => setSelectedCSVContract(e.target.value)}
                  className="select w-full max-w-md"
                >
                  <option value="">选择合约...</option>
                  {csvContracts.map((contract) => (
                    <option key={contract.instrument_name} value={contract.instrument_name}>
                      {contract.instrument_name} (执行价: ${contract.strike_price.toLocaleString()})
                    </option>
                  ))}
                </select>
                <p className="text-sm text-text-secondary mt-2">
                  共有 {csvContracts.length} 个可用合约
                </p>
              </>
            )}
          </div>

          {/* CSV合约信息 */}
          {selectedCSVContract && csvContractData && (
            <>
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 text-text-primary">合约信息</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-text-secondary text-sm">合约名称</p>
                    <p className="text-text-primary font-medium mt-1">{csvContractData.instrument_name}</p>
                  </div>
                  <div>
                    <p className="text-text-secondary text-sm">标的资产</p>
                    <p className="text-text-primary font-medium mt-1">{csvContractData.underlying}</p>
                  </div>
                  <div>
                    <p className="text-text-secondary text-sm">执行价</p>
                    <p className="text-text-primary font-medium mt-1">${csvContractData.strike_price.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-text-secondary text-sm">期权类型</p>
                    <p className="text-text-primary font-medium mt-1">
                      {csvContractData.option_type === 'call' ? '看涨 (Call)' : '看跌 (Put)'}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-secondary text-sm">到期日</p>
                    <p className="text-text-primary font-medium mt-1">
                      {new Date(csvContractData.expiry_date).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-secondary text-sm">数据点数</p>
                    <p className="text-accent-blue font-bold text-xl mt-1">{csvContractData.data_points}</p>
                  </div>
                  <div>
                    <p className="text-text-secondary text-sm">平均价格</p>
                    <p className="text-accent-green font-bold text-xl mt-1">
                      {csvContractData.avg_price.toFixed(4)} BTC
                    </p>
                  </div>
                  <div>
                    <p className="text-text-secondary text-sm">数据时间范围</p>
                    <p className="text-text-primary font-medium text-sm mt-1">
                      {formatDate(csvContractData.date_range.start)} ~ {formatDate(csvContractData.date_range.end)}
                    </p>
                  </div>
                </div>
              </div>

              {/* 价格曲线图 */}
              {csvContractData.price_history && csvContractData.price_history.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 text-text-primary">价格曲线</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={csvContractData.price_history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                      <XAxis 
                        dataKey="timestamp" 
                        stroke="#848E9C"
                        tickFormatter={(value) => {
                          try {
                            return new Date(value).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                          } catch {
                            return value
                          }
                        }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis stroke="#848E9C" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1E2329',
                          border: '1px solid #474D57',
                          borderRadius: '8px'
                        }}
                        labelFormatter={(value) => {
                          try {
                            return new Date(value).toLocaleString('zh-CN')
                          } catch {
                            return value
                          }
                        }}
                        formatter={(value: any) => value ? value.toFixed(4) : 'N/A'}
                      />
                      <Legend />
                      {csvContractData.price_history.some(p => p.mark_price) && (
                        <Line type="monotone" dataKey="mark_price" stroke="#F0B90B" name="标记价格" dot={false} />
                      )}
                      {csvContractData.price_history.some(p => p.bid_price) && (
                        <Line type="monotone" dataKey="bid_price" stroke="#0ECB81" name="买价" dot={false} />
                      )}
                      {csvContractData.price_history.some(p => p.ask_price) && (
                        <Line type="monotone" dataKey="ask_price" stroke="#F6465D" name="卖价" dot={false} />
                      )}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* 隐含波动率曲线 */}
              {csvContractData.price_history && csvContractData.price_history.some(p => p.implied_volatility) && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 text-text-primary">隐含波动率</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={csvContractData.price_history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                      <XAxis 
                        dataKey="timestamp" 
                        stroke="#848E9C"
                        tickFormatter={(value) => {
                          try {
                            return new Date(value).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                          } catch {
                            return value
                          }
                        }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis stroke="#848E9C" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1E2329',
                          border: '1px solid #474D57',
                          borderRadius: '8px'
                        }}
                        labelFormatter={(value) => {
                          try {
                            return new Date(value).toLocaleString('zh-CN')
                          } catch {
                            return value
                          }
                        }}
                        formatter={(value: any) => value ? `${(value * 100).toFixed(2)}%` : 'N/A'}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="implied_volatility" stroke="#B7BDC6" name="隐含波动率" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* 成交量曲线 */}
              {csvContractData.price_history && csvContractData.price_history.some(p => p.volume) && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 text-text-primary">成交量</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={csvContractData.price_history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
                      <XAxis 
                        dataKey="timestamp" 
                        stroke="#848E9C"
                        tickFormatter={(value) => {
                          try {
                            return new Date(value).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                          } catch {
                            return value
                          }
                        }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis stroke="#848E9C" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1E2329',
                          border: '1px solid #474D57',
                          borderRadius: '8px'
                        }}
                        labelFormatter={(value) => {
                          try {
                            return new Date(value).toLocaleString('zh-CN')
                          } catch {
                            return value
                          }
                        }}
                      />
                      <Bar dataKey="volume" fill="#3861FB" name="成交量" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
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
                  {((qualityReport?.quality_score || 0) * 100).toFixed(0)}
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
                  {((qualityReport?.coverage_percentage || 0) * 100).toFixed(1)}
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
